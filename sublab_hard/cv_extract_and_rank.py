from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from jsonschema import validate
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_DIR = ROOT / "data" / "candidates"
RUBRIC_PATH = ROOT / "data" / "candidate_rubric.json"

MODEL = "gpt-5.6-luna"

load_dotenv(ROOT / ".env", override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")

client = OpenAI(api_key=api_key)


# ---------------------------------------------------------------------
# JSON schema for the structured CV extracted from each story
# ---------------------------------------------------------------------

CV_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_id": {
            "type": "string"
        },
        "full_name": {
            "type": ["string", "null"]
        },
        "degree": {
            "type": ["string", "null"]
        },
        "graduation_year": {
            "type": ["integer", "null"]
        },
        "gpa_4_scale": {
            "type": ["number", "null"]
        },
        "gpa_original": {
            "type": ["number", "null"]
        },
        "gpa_scale": {
            "type": ["number", "null"]
        },
        "languages": {
            "type": "array",
            "items": {"type": "string"}
        },
        "published_peer_reviewed_outputs": {
            "type": "integer",
            "minimum": 0
        },
        "non_published_outputs": {
            "type": "array",
            "items": {"type": "string"}
        },
        "total_countable_relevant_experience_months": {
            "type": "integer",
            "minimum": 0
        },
        "uncounted_experience": {
            "type": "array",
            "items": {"type": "string"}
        },
        "evidence_quotes": {
            "type": "object",
            "additionalProperties": {
                "type": "string"
            }
        },
        "ambiguities": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "candidate_id",
        "full_name",
        "degree",
        "graduation_year",
        "gpa_4_scale",
        "gpa_original",
        "gpa_scale",
        "languages",
        "published_peer_reviewed_outputs",
        "non_published_outputs",
        "total_countable_relevant_experience_months",
        "uncounted_experience",
        "evidence_quotes",
        "ambiguities"
    ],
    "additionalProperties": False
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def parse_json(text: str) -> dict[str, Any]:
    """
    Parse JSON even if the model accidentally wraps it in
    ```json ... ```
    """
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}") from exc

    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")

    return value


def call_model(system_prompt: str, user_prompt: str) -> str:
    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response.output_text


def load_rubric() -> dict[str, Any]:
    with RUBRIC_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------
# Part 1: CV extraction
# ---------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """
You are extracting structured scholarship-CV information from one
unstructured written application.

Return ONLY one JSON object matching the schema provided by the caller.

Rules:

1. Never invent facts.
   If the story does not state a fact, use null.

2. GPA:
   - If GPA is already on a 4.0 scale, record it directly.
   - If GPA is on another numeric scale, convert it to a 4.0 scale
     using proportional conversion:
         converted = original / original_scale * 4.0
   - Always preserve the original GPA and original scale.
   - Never estimate a missing GPA.

3. Publications:
   Count a publication only when the story explicitly says it was
   published or accepted.
   Do NOT count:
   - submitted
   - under review
   - in preparation
   - planned
   - in press

   Record those separately in non_published_outputs.

4. Contradictions:
   If the story gives contradictory values for a field:
   - set that field to null
   - describe the contradiction in ambiguities
   - do not average the values
   - do not choose one value

5. Experience:
   Count months, not jobs.
   Only count periods where the duration or dates are actually stated.
   Do not invent missing dates.
   Overlapping periods must only be counted once.

6. Relevant experience:
   Count work or internships that are directly relevant to the
   candidate's academic/research/technical application.

7. Evidence:
   Every populated factual field should have an evidence quote.
   Quotes must come directly from the story.

8. Candidate ID:
   The caller supplies the candidate ID. Do not invent another ID.

Return JSON only.
"""


def extract_candidate(candidate_id: str, story: str) -> dict[str, Any]:
    user_prompt = f"""
Candidate ID: {candidate_id}

Return a JSON object matching this schema:

{json.dumps(CV_SCHEMA, indent=2)}

Application story:

--- BEGIN STORY ---
{story}
--- END STORY ---
"""

    raw = call_model(EXTRACTION_SYSTEM_PROMPT, user_prompt)
    record = parse_json(raw)

    # The program owns the candidate ID.
    record["candidate_id"] = candidate_id

    validate(instance=record, schema=CV_SCHEMA)

    return record


# ---------------------------------------------------------------------
# Part 2: model scoring
# ---------------------------------------------------------------------

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "academic": {
            "type": "number",
            "minimum": 0,
            "maximum": 5
        },
        "research": {
            "type": "number",
            "minimum": 0,
            "maximum": 5
        },
        "experience": {
            "type": "number",
            "minimum": 0,
            "maximum": 5
        }
    },
    "required": [
        "academic",
        "research",
        "experience"
    ],
    "additionalProperties": False
}


SCORING_SYSTEM_PROMPT = """
You are scoring scholarship candidates against a fixed rubric.

Return ONLY JSON with exactly these three numeric fields:

{
  "academic": 0-5,
  "research": 0-5,
  "experience": 0-5
}

Do not calculate a weighted total.
Do not choose a winner.
Do not add explanations.
Do not add any other fields.

Use only the candidate record and the supplied rubric.
"""


def score_candidate(
    candidate_id: str,
    record: dict[str, Any],
    rubric: dict[str, Any]
) -> dict[str, Any]:

    user_prompt = f"""
Candidate: {candidate_id}

Candidate structured record:
{json.dumps(record, ensure_ascii=False, indent=2)}

Rubric:
{json.dumps(rubric, ensure_ascii=False, indent=2)}

Return only:

{json.dumps(SCORE_SCHEMA, indent=2)}
"""

    raw = call_model(SCORING_SYSTEM_PROMPT, user_prompt)
    scores = parse_json(raw)

    validate(instance=scores, schema=SCORE_SCHEMA)

    return scores


# ---------------------------------------------------------------------
# Part 2b: independent prose ranking
# ---------------------------------------------------------------------

PROSE_SYSTEM_PROMPT = """
You are reviewing scholarship candidates.

Based on the supplied candidate records and rubric, write a short prose
answer identifying which candidate you think should receive the funded
scholarship and why.

This is intentionally separate from the programmatic ranking.

Do not output JSON.
"""


def prose_ranking(
    records: list[dict[str, Any]],
    rubric: dict[str, Any]
) -> str:

    user_prompt = f"""
Rubric:
{json.dumps(rubric, ensure_ascii=False, indent=2)}

Candidate records:

{json.dumps(records, ensure_ascii=False, indent=2)}

Which candidate should receive the funded scholarship?
Give a concise prose explanation.
"""

    return call_model(PROSE_SYSTEM_PROMPT, user_prompt)


# ---------------------------------------------------------------------
# Programmatic ranking
# ---------------------------------------------------------------------

def compute_weighted_total(
    scores: dict[str, Any],
    rubric: dict[str, Any]
) -> float:

    weights = {
        criterion["id"]: criterion["weight"]
        for criterion in rubric["criteria"]
    }

    total = (
        scores["academic"] * weights["academic"]
        + scores["research"] * weights["research"]
        + scores["experience"] * weights["experience"]
    )

    return round(total, 2)


def rank_candidates(
    scored_candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    return sorted(
        scored_candidates,
        key=lambda item: item["weighted_total"],
        reverse=True
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    rubric = load_rubric()

    story_files = sorted(CANDIDATES_DIR.glob("story-*.md"))

    if len(story_files) != 6:
        raise RuntimeError(
            f"Expected 6 candidate stories, found {len(story_files)}"
        )

    records = []

    print("=" * 80)
    print("SUBLAB HARD — PART 1: CV EXTRACTION")
    print("=" * 80)

    for story_file in story_files:
        candidate_id = story_file.stem.replace("story-", "C-")

        story = story_file.read_text(encoding="utf-8")

        print(f"\nExtracting {candidate_id} from {story_file.name}...")

        record = extract_candidate(candidate_id, story)
        records.append(record)

        print("  parse: YES")
        print("  schema: VALID")
        print(f"  name: {record['full_name']}")
        print(f"  GPA 4.0: {record['gpa_4_scale']}")
        print(
            "  published peer-reviewed outputs: "
            f"{record['published_peer_reviewed_outputs']}"
        )
        print(
            "  countable relevant experience: "
            f"{record['total_countable_relevant_experience_months']} months"
        )

        if record["gpa_4_scale"] is None:
            print("  null field: gpa_4_scale")

        if record["graduation_year"] is None:
            print("  null field: graduation_year")

        if record["ambiguities"]:
            print("  ambiguities:")
            for item in record["ambiguities"]:
                print(f"    - {item}")

    print("\n")
    print("=" * 80)
    print("SUBLAB HARD — PART 2: MODEL SCORES")
    print("=" * 80)

    scored_candidates = []

    for record in records:
        candidate_id = record["candidate_id"]

        print(f"\nScoring {candidate_id}...")

        scores = score_candidate(
            candidate_id,
            record,
            rubric
        )

        weighted_total = compute_weighted_total(
            scores,
            rubric
        )

        result = {
            "candidate_id": candidate_id,
            "full_name": record["full_name"],
            "scores": scores,
            "weighted_total": weighted_total
        }

        scored_candidates.append(result)

        print(
            f"  academic={scores['academic']}, "
            f"research={scores['research']}, "
            f"experience={scores['experience']}"
        )

        print(f"  weighted total={weighted_total:.2f}")

    ranked = rank_candidates(scored_candidates)

    print("\n")
    print("=" * 80)
    print("COMPUTED RANKING")
    print("=" * 80)

    for position, candidate in enumerate(ranked, start=1):
        scores = candidate["scores"]

        print(
            f"{position}. "
            f"{candidate['candidate_id']} — "
            f"{candidate['full_name']} — "
            f"academic={scores['academic']}, "
            f"research={scores['research']}, "
            f"experience={scores['experience']}, "
            f"total={candidate['weighted_total']:.2f}"
        )

    winner = ranked[0]

    print("\nCOMPUTED WINNER:")
    print(
        f"{winner['candidate_id']} — "
        f"{winner['full_name']} "
        f"({winner['weighted_total']:.2f})"
    )

    print("\n")
    print("=" * 80)
    print("PART 2b — INDEPENDENT PROSE RANKING")
    print("=" * 80)

    prose = prose_ranking(records, rubric)

    print(prose)

    save_results(
    records,
    scored_candidates,
    ranked,
    prose
)

    print("\n")
    print("=" * 80)
    print("FULL EXTRACTION RECORDS")
    print("=" * 80)

    print(
        json.dumps(
            records,
            ensure_ascii=False,
            indent=2
        )
    )

def save_results(
    records: list[dict[str, Any]],
    scored_candidates: list[dict[str, Any]],
    ranked: list[dict[str, Any]],
    prose: str
) -> None:

    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)

    result = {
        "model": MODEL,
        "extractions": records,
        "scores": scored_candidates,
        "computed_ranking": ranked,
        "computed_winner": ranked[0] if ranked else None,
        "prose_ranking": prose
    }

    output_path = output_dir / "hard_results.json"

    output_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()