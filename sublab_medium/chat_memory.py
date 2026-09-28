import argparse
import json
from pathlib import Path

import tiktoken
from dotenv import load_dotenv
from jsonschema import validate, ValidationError
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

MODEL = "gpt-5.6-luna"

load_dotenv(ROOT / ".env")
client = OpenAI()


def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def count_tokens(messages):
    """
    Count tokens approximately as tokens sent to the model.
    We count the serialized message content using the model tokenizer.
    """
    encoding = tiktoken.get_encoding("o200k_base")

    text = ""
    for message in messages:
        text += f"{message['role']}: {message['content']}\n"

    return len(encoding.encode(text))


def call_model(messages):
    response = client.responses.create(
        model=MODEL,
        input=messages,
    )

    return response.output_text.strip()


def parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def validate_state(state, schema):
    if state is None:
        return False

    try:
        validate(instance=state, schema=schema)
        return True
    except ValidationError:
        return False


def build_system_prompt():
    return """
You are a grant-office assistant.

Answer the applicant using only information available in the conversation
or the structured compressed state provided to you.

Do not invent facts.

The grant policy is:
- GPA must be at least 2.67.
- Income band must be 1 or 2.
- Required documents are transcript and id_card.
- Band 1 amount is 250000 KZT.
- Band 2 amount is 150000 KZT.
- The official applicant record is the source of truth for eligibility.

When answering questions about what the applicant said, distinguish:
- facts the applicant stated,
- decisions already discussed,
- constraints the applicant stated,
- unanswered questions.

Give a direct and concise answer.
"""


def build_compression_prompt(messages):
    conversation_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in messages
    )

    return f"""
Compress the conversation into exactly one JSON object.

You MUST use this structure:

{{
  "applicant_id": string or null,
  "topic": string,
  "facts": [],
  "decisions": [],
  "constraints": [],
  "open_questions": [],
  "language": string
}}

Rules:

- applicant_id is null if the applicant never established it.
- facts are things the APPLICANT explicitly stated.
- decisions are decisions or conclusions already discussed.
- constraints are conditions on how or when something can happen,
  including days, deadlines, or requirements stated by the applicant.
- open_questions are questions the applicant asked that have not been answered.
- language describes the language used by the applicant.
- Do not invent anything.
- Do not infer unstated facts.
- Keep important information even if it is not directly about eligibility.
- Return JSON only.

Conversation:

{conversation_text}
"""


def answer_from_state(state, question):
    state_text = json.dumps(state, ensure_ascii=False, indent=2)

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(),
        },
        {
            "role": "user",
            "content": (
                "Here is the compressed conversation state:\n\n"
                f"{state_text}\n\n"
                f"Applicant question: {question}"
            ),
        },
    ]

    return call_model(messages), count_tokens(messages)


def run_script(compress_enabled):
    data = load_json("chat_script.json")
    schema = load_json("memory_state.schema.json")

    conversation = data["conversation"]

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(),
        }
    ]

    state = None
    token_log = []

    print()
    print("=" * 70)
    print("SUBLAB MEDIUM")
    print("Compression:", "ENABLED" if compress_enabled else "DISABLED")
    print("=" * 70)

    for index, turn in enumerate(conversation, start=1):

        # <compress> is a command, not an applicant message.
        if turn == "<compress>":

            if not compress_enabled:
                print(f"\nTurn {index}: <compress> skipped")
                continue

            print(f"\nTurn {index}: <compress>")

            compression_messages = [
                {
                    "role": "system",
                    "content": (
                        "You compress an applicant conversation into "
                        "the required structured state."
                    ),
                },
                {
                    "role": "user",
                    "content": build_compression_prompt(messages),
                },
            ]

            compressed_text = call_model(compression_messages)
            state_candidate = parse_json(compressed_text)

            if validate_state(state_candidate, schema):
                state = state_candidate

                print("Compression successful.")
                print(json.dumps(state, ensure_ascii=False, indent=2))

                # Throw away old turns.
                messages = [
                    {
                        "role": "system",
                        "content": build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Current compressed conversation state:\n"
                            + json.dumps(
                                state,
                                ensure_ascii=False,
                                indent=2,
                            )
                        ),
                    },
                ]
            else:
                print("Compression FAILED validation.")
                print("Keeping the original conversation history.")

            continue

        # Applicant turn
        messages.append(
            {
                "role": "user",
                "content": turn,
            }
        )

        reply = call_model(messages)

        messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        tokens = count_tokens(messages)
        token_log.append(
            {
                "turn": index,
                "tokens": tokens,
            }
        )

        print(f"\nTurn {index}")
        print("Applicant:", turn)
        print("Assistant:", reply)
        print("Tokens sent:", tokens)

    print("\n" + "=" * 70)
    print("PROBES")
    print("=" * 70)

    probe_results = []

    for probe in data["probes"]:

        if compress_enabled and state is not None:
            reply, tokens = answer_from_state(
                state,
                probe["question"],
            )
        else:
            probe_messages = messages + [
                {
                    "role": "user",
                    "content": probe["question"],
                }
            ]

            reply = call_model(probe_messages)
            tokens = count_tokens(probe_messages)

        lower_reply = reply.lower()

        retrieved = any(
            expected.lower() in lower_reply
            for expected in probe["expect_contains"]
        )

        result = {
            "id": probe["id"],
            "question": probe["question"],
            "retrieved": retrieved,
            "reply": reply,
            "tokens": tokens,
        }

        probe_results.append(result)

        print(f"\n{probe['id']}: {probe['question']}")
        print("Retrieved:", retrieved)
        print("Reply:", reply)
        print("Tokens:", tokens)

    print("\n" + "=" * 70)
    print("TOKEN LOG")
    print("=" * 70)

    for item in token_log:
        print(
            f"Turn {item['turn']}: "
            f"{item['tokens']} tokens"
        )

    if state is not None:
        print("\n" + "=" * 70)
        print("FINAL COMPRESSED STATE")
        print("=" * 70)
        print(json.dumps(state, ensure_ascii=False, indent=2))

    return {
        "compression_enabled": compress_enabled,
        "token_log": token_log,
        "probe_results": probe_results,
        "state": state,
    }


def interactive():
    print("=" * 70)
    print("INTERACTIVE MODE")
    print("Type 'compress' to compress the conversation.")
    print("Type 'tokens' to see the last token count.")
    print("Type 'quit' to exit.")
    print("=" * 70)

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(),
        }
    ]

    schema = load_json("memory_state.schema.json")
    state = None
    last_tokens = 0

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "quit":
            break

        if user_input.lower() == "tokens":
            print("Last token count:", last_tokens)
            continue

        if user_input.lower() == "compress":

            compression_messages = [
                {
                    "role": "system",
                    "content": (
                        "You compress an applicant conversation into "
                        "the required structured state."
                    ),
                },
                {
                    "role": "user",
                    "content": build_compression_prompt(messages),
                },
            ]

            compressed_text = call_model(compression_messages)
            candidate = parse_json(compressed_text)

            if validate_state(candidate, schema):
                state = candidate

                print("\nCompression successful.")
                print(
                    json.dumps(
                        state,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

                messages = [
                    {
                        "role": "system",
                        "content": build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Current compressed conversation state:\n"
                            + json.dumps(
                                state,
                                ensure_ascii=False,
                                indent=2,
                            )
                        ),
                    },
                ]
            else:
                print(
                    "\nCompression failed validation. "
                    "Conversation history preserved."
                )

            last_tokens = count_tokens(messages)
            print("Tokens:", last_tokens)
            continue

        if state is not None:
            reply, last_tokens = answer_from_state(
                state,
                user_input,
            )

            print("\nAssistant:", reply)
        else:
            messages.append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )

            reply = call_model(messages)

            messages.append(
                {
                    "role": "assistant",
                    "content": reply,
                }
            )

            last_tokens = count_tokens(messages)

            print("\nAssistant:", reply)

        print("Tokens:", last_tokens)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Run the scripted conversation without compression.",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive mode.",
    )

    args = parser.parse_args()

    if args.interactive:
        interactive()
        return

    run_script(compress_enabled=not args.no_compress)


if __name__ == "__main__":
    main()