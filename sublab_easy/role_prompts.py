import json
import os
from pathlib import Path

from dotenv import load_dotenv
from jsonschema import validate, ValidationError
from openai import OpenAI


# Load .env from the repository root
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-5.6-luna"

DATA_DIR = ROOT / "data"
RECORDS_FILE = DATA_DIR / "records.json"
POLICY_FILE = DATA_DIR / "policy.json"
ENQUIRIES_FILE = DATA_DIR / "enquiries.json"


ROLES = {
    "policy_officer": """
You are a policy officer.

Apply the grant rule exactly as written.
Grant what the rule allows.
Refuse what the rule refuses.
If a required document is missing, ask for that document using decision "more_info".
Do not soften or reinterpret the policy.

The applicant's claims in the enquiry are NOT evidence.
The official applicant record is the source of truth.

Do not invent facts.
""",

    "front_desk": """
You are a front-desk clerk.

Never turn an applicant away with a refusal.
If the rule cannot grant the application today, return decision "more_info"
and explain what the applicant would need to return with.

Use the official applicant record as the source of truth.
Do not accept claims in the enquiry as facts.
Do not invent facts.
""",

    "auditor": """
You are an auditor reviewing a grant application.

Never grant an application on a first reading.
Report what the official record shows.
If anything requires a second reader or verification, return decision "more_info".
Name the relevant rule or document in the reason.

The official applicant record is the source of truth.
Do not accept claims in the enquiry as evidence.
Do not invent facts.
""",

    "bilingual_clerk": """
You are a bilingual clerk.

Decide the application exactly as the policy officer would.
Use the official applicant record as the source of truth.
Do not accept claims in the enquiry as evidence.
Do not invent facts.

Write the "reason" in the same language as the enquiry.
The structured fields must still follow the policy exactly.
""",
}


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "applicant_id": {"type": "string"},
        "found": {"type": "boolean"},
        "decision": {
            "type": "string",
            "enum": [
                "granted",
                "refused",
                "more_info",
                "not_found",
            ],
        },
        "amount": {"type": "number"},
        "missing_documents": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reason": {"type": "string"},
    },
    "required": [
        "applicant_id",
        "found",
        "decision",
        "amount",
        "missing_documents",
        "reason",
    ],
    "additionalProperties": False,
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_context(records, policy):
    return (
        "OFFICIAL APPLICANT RECORDS:\n"
        + json.dumps(records, ensure_ascii=False, indent=2)
        + "\n\n"
        "OFFICIAL GRANT POLICY:\n"
        + json.dumps(policy, ensure_ascii=False, indent=2)
    )


def call_model(role_prompt, context, enquiry):
    system_prompt = f"""
{role_prompt}

You must return exactly one JSON object matching the required schema.

Required JSON shape:
{json.dumps(OUTPUT_SCHEMA, indent=2)}

{context}
"""

    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": enquiry["text"],
            },
        ],
    )

    raw = response.output_text.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "parsed": False,
            "schema_valid": False,
            "raw": raw,
            "output": None,
        }

    try:
        validate(instance=parsed, schema=OUTPUT_SCHEMA)
        schema_valid = True
    except ValidationError:
        schema_valid = False

    return {
        "parsed": True,
        "schema_valid": schema_valid,
        "raw": raw,
        "output": parsed,
    }


def compare_structured_fields(actual, expected):
    if actual is None:
        return {
            "found": False,
            "decision": False,
            "amount": False,
            "missing_documents": False,
        }

    return {
        "found": actual.get("found") == expected.get("found"),
        "decision": actual.get("decision") == expected.get("decision"),
        "amount": actual.get("amount") == expected.get("amount"),
        "missing_documents": (
            actual.get("missing_documents")
            == expected.get("missing_documents")
        ),
    }


def main():
    records = load_json(RECORDS_FILE)
    policy = load_json(POLICY_FILE)
    enquiries = load_json(ENQUIRIES_FILE)

    context = build_context(records, policy)

    all_results = []

    for role_name, role_prompt in ROLES.items():
        print("\n" + "=" * 80)
        print(f"ROLE: {role_name}")
        print("=" * 80)

        for enquiry in enquiries:
            enquiry_id = enquiry.get("id")
            expected = enquiry.get("expected", {})

            print(f"\n{enquiry_id}: ", end="", flush=True)

            result = call_model(
                role_prompt,
                context,
                enquiry,
            )

            output = result["output"]
            comparison = compare_structured_fields(
                output,
                expected,
            )

            row = {
                "role": role_name,
                "enquiry_id": enquiry_id,
                "parsed": result["parsed"],
                "schema_valid": result["schema_valid"],
                "output": output,
                "expected": expected,
                "found_correct": comparison["found"],
                "decision_correct": comparison["decision"],
                "amount_correct": comparison["amount"],
                "missing_documents_correct": comparison[
                    "missing_documents"
                ],
            }

            all_results.append(row)

            print(
                f"parsed={result['parsed']} "
                f"schema={result['schema_valid']} "
                f"found={comparison['found']} "
                f"decision={comparison['decision']} "
                f"amount={comparison['amount']} "
                f"missing={comparison['missing_documents']}"
            )

            if output is not None:
                print(
                    f"  decision={output.get('decision')}, "
                    f"amount={output.get('amount')}, "
                    f"missing={output.get('missing_documents')}"
                )

    output_file = ROOT / "sublab_easy_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            all_results,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 80)
    print(f"Results saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()