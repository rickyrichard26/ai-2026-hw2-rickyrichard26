from jsonschema import validate
from sublab_hard.cv_extract_and_rank import CV_SCHEMA


valid_record = {
    "candidate_id": "C-TEST",
    "full_name": "Test Candidate",
    "degree": "Computer Science",
    "graduation_year": 2026,
    "gpa_4_scale": 3.8,
    "gpa_original": 3.8,
    "gpa_scale": 4.0,
    "languages": ["English"],
    "published_peer_reviewed_outputs": 2,
    "non_published_outputs": [],
    "total_countable_relevant_experience_months": 24,
    "uncounted_experience": [],
    "evidence_quotes": {
        "full_name": "My name is Test Candidate.",
        "gpa_4_scale": "My GPA is 3.8/4.0."
    },
    "ambiguities": []
}


validate(instance=valid_record, schema=CV_SCHEMA)

print("Valid CV schema test: PASS")