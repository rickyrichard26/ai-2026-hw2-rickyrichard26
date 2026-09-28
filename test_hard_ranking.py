from sublab_hard.cv_extract_and_rank import rank_candidates

data = [
    {
        "candidate_id": "C-01",
        "full_name": "Candidate 1",
        "scores": {
            "academic": 4,
            "research": 3,
            "experience": 2
        },
        "weighted_total": 3.3
    },
    {
        "candidate_id": "C-02",
        "full_name": "Candidate 2",
        "scores": {
            "academic": 5,
            "research": 5,
            "experience": 5
        },
        "weighted_total": 5.0
    },
    {
        "candidate_id": "C-03",
        "full_name": "Candidate 3",
        "scores": {
            "academic": 3,
            "research": 2,
            "experience": 4
        },
        "weighted_total": 2.9
    }
]

ranked = rank_candidates(data)

print("Ranking test:")
for position, candidate in enumerate(ranked, start=1):
    print(
        f"{position}. "
        f"{candidate['candidate_id']} = "
        f"{candidate['weighted_total']}"
    )

assert ranked[0]["candidate_id"] == "C-02"
assert ranked[1]["candidate_id"] == "C-01"
assert ranked[2]["candidate_id"] == "C-03"

print("Ranking test: PASS")