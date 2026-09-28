# HW2 submission

**Name:** Ricky Richard Takahindangen
**Student ID:26078831
**Group:** Individual
**Repository:** https://github.com/rickyrichard26/ai-2026-hw2-rickyrichard26.git 

## AI tool disclosure
I used OpenAI GPT-5.6 Luna through the OpenAI API as the model required by
the assignment. I used it for all three sublabs: role-conditioned structured
decisions in Sublab Easy, conversation responses and state compression in
Sublab Medium, and CV/story extraction and scoring in Sublab Hard.

I also used ChatGPT as a development assistant to help debug Python code,
interpret errors, inspect the assignment requirements, and draft/refine
implementation ideas. The actual experimental outputs reported below are
based on the files and runs in my repository.
>

---

## Sublab Easy â€” one task, four roles

### Decisions per role

One row per enquiry. In each cell write the `decision` your run returned, and
whether it agrees with `expected` in `data/enquiries.json`:

| Enquiry | policy_officer | front_desk | auditor | bilingual_clerk |
|---|---|---|---|---|
| E-01 | granted | granted | more_info | granted |
| E-02 | more_info | more_info | more_info | more_info |
| E-03 | refused | more_info | refused | refused |
| E-04 | refused | more_info | refused | refused |
| E-05 | granted | granted | more_info | granted |
| E-06 | granted | granted | more_info | granted |
| E-07 | granted | granted | more_info | granted |
| E-08 | not_found | not_found | not_found | not_found |
| E-09 | refused | more_info | refused | refused |
| E-10 | more_info | more_info | more_info | more_info |
| **agrees with `expected`** | 10/10 | 7/10 | 6/10 | 10/10 |
| **parsed** | 10/10 | 10/10 | 10/10 | 10/10 |
| **schema-valid** | 10/10 | 10/10 | 10/10 | 10/10 |

### Which field moved, on which enquiry, under which role

| Field | Enquiries that moved | Role(s) that moved it |
|---|---|---|
| `found` | None | None |
| `decision` | E-03, E-04, E-09 | `front_desk`; E-01, E-05, E-06, E-07 | `auditor` |
| `amount` | None | None |
| `missing_documents` | None | None |

The only field that changed relative to the expected structured record was
`decision`. The `found`, `amount`, and `missing_documents` fields remained
consistent across the runs.

### Raw replies

Paste the full reply for **one enquiry where a role changed the decision** away
from the policy officer's:

```json
{
  "applicant_id": "A-203",
  "found": true,
  "decision": "more_info",
  "amount": 0,
  "missing_documents": [],
  "reason": "The application cannot be granted based on the current record because the GPA is 2.4, below the required minimum of 2.67. Please return with anupdated transcript showing a GPA of at least 2.67."
}

Paste the full reply for **E-07 (the Kazakh enquiry)** from the bilingual
clerk, so the `reason` language is visible:

{
  "applicant_id": "A-201",
  "found": true,
  "decision": "granted",
  "amount": 250000,
  "missing_documents": [],
  "reason": "Ð¡Ñ–Ð· Ð³Ñ€Ð°Ð½Ñ‚ Ñ‚Ð°Ð»Ð°Ð¿Ñ‚Ð°Ñ€Ñ‹Ð½Ð° ÑÐ°Ð¹ ÐºÐµÐ»ÐµÑÑ–Ð·: GPA ÐºÓ©Ñ€ÑÐµÑ‚ÐºÑ–ÑˆÑ– 3.4, Ñ‚Ð°Ð±Ñ‹Ñ ÑÐ°Ð½Ð°Ñ‚Ñ‹Ò£Ñ‹Ð· 1, ÑÐ¾Ð½Ð´Ð°Ð¹-Ð°Ò› Ñ‚Ñ€Ð°Ð½ÑÐºÑ€Ð¸Ð¿Ñ‚ Ð¿ÐµÐ½ Ð¶ÐµÐºÐµ ÐºÑƒÓ™Ð»Ñ–Ðº Ò›Ò±Ð¶Ð°Ñ‚Ñ‚Ð°Ñ€Ñ‹ Ñ‚Ñ–Ñ€ÐºÐµÐ»Ð³ÐµÐ½. Ð“Ñ€Ð°Ð½Ñ‚ Ð¼Ó©Ð»ÑˆÐµÑ€Ñ– â€” 250 000 Ñ‚ÐµÒ£Ð³Ðµ."
}

### Written answers

**1. Which fields are role-sensitive and which are not?** Point at rows in your
tables.

> In this run, decision was the role-sensitive field. It changed under the
front_desk role for E-03, E-04, and E-09, and under the auditor role for
E-01, E-05, E-06, and E-07.

The other fields were not role-sensitive in this experiment. found,
amount, and missing_documents were correct for all 40 role/enquiry
combinations. All 40 responses were parsed successfully and were
schema-valid.

**2. Which enquiries are most sensitive to the role, and why those?** Say what
E-03, E-04, E-07 and E-10 are each testing.

> E-03 tests a clear policy refusal based on GPA below the minimum. The
policy officer returned refused, while the front desk changed it to
more_info, treating a new transcript as a possible next step.

E-04 tests refusal based on an ineligible income band. The policy officer
returned refused, while the front desk returned more_info, suggesting
that the record could be updated.

E-07 tests whether the role can preserve the correct structured decision
while handling a Kazakh-language enquiry. The bilingual clerk returned the
correct granted decision and the correct structured fields, although the
stored reason displayed mojibake.

E-10 tests an incomplete application where the applicant is found but the
ID card is missing. All roles returned more_info, so it was not
role-sensitive in this run.

**3. Where does discretion belong â€” the role paragraph, or code that reads
`decision` afterwards?** Say what a downstream program can and cannot tell
about which role produced a record.

> The role paragraph is where the model's role-specific interpretation is
introduced, while downstream code should treat the structured decision
as data and validate it against the policy before using it for an expensive
or irreversible action.

A downstream program can see the resulting decision, found, amount,
and missing_documents values, but it cannot infer the complete reasoning
process or reliably determine which role caused a different decision unless
the role identifier is explicitly stored as metadata. The structured
output alone therefore does not contain the complete provenance of the
decision.

**4. Is a role a boundary?** Say in Week 2 terms what the role paragraph is
made of, and what you would put in code â€” not in the prompt â€” if a wrong
`decision` were expensive.

> A role is a behavioral boundary created by instructions describing the
model's responsibilities, perspective, and output behavior. It is still
an instruction to the model rather than a security or correctness boundary.

If an incorrect decision were expensive, I would put the policy enforcement
in deterministic code. The program should validate the official record,
GPA, income band, required documents, and allowed decision before accepting
a model-generated decision. The model could explain the case, but the code
should make or validate the final business-critical decision.

---

## Sublab Medium â€” memory you choose

### Tokens per call

| Call | A â€” never compressed | B â€” compressed at the `compress` turn |
|---|---|---|
| 1 | NOT COMPLETED — API quota exhausted | 211 |
| 2 | NOT COMPLETED — API quota exhausted | 304 |
| 3 | NOT COMPLETED — API quota exhausted | 386 |
| 4 | NOT COMPLETED — API quota exhausted | 455 |
| 5 | NOT COMPLETED — API quota exhausted | 519 |
| 6 | NOT COMPLETED — API quota exhausted | 597 |
| 7 | NOT COMPLETED — API quota exhausted | 669 |
| 8 | NOT COMPLETED — API quota exhausted | 736 |
| 9 | NOT COMPLETED — API quota exhausted | 819 |
| 10 | NOT COMPLETED — API quota exhausted | compression call not recorded |
| 11 | NOT COMPLETED — API quota exhausted | 617 |
| 12 | NOT COMPLETED — API quota exhausted | 650 |
| **peak** | Not available | 819 |
| **total for the run** | Not available | 5663 logged tokens, excluding the unrecorded compression call |

### Probes after the conversation

| Probe | Tests | A retrieved? | A answer | B retrieved? | B answer |
|---|---|---|---|---|---|
| Q-1 identity | turn 1 | Not run | - | Yes | A-202 |
| Q-2 missing document | turn 5 | Not run | - | Yes | id card |
| Q-3 band and amount | turns 3â€“4 | Not run | - | Yes | income band 2; 150,000 KZT |
| Q-4 the constraint | turn 6 | Not run | - | Yes | Thursday |
| Q-5 the open question | turn 7 | Not run | - | Yes | whether the employer letter needs to be original or a scanned copy |
| **retrieved** | | Not available | | 5/5 | |

### The state my compression produced

{
  "applicant_id": "A-202",
  "topic": "Study grant eligibility and application requirements",
  "facts": [
    "The applicant's name is Daniyar Qoshan.",
    "The applicant stated that they sent their transcript last week.",
    "The applicant stated that their income band is 2 and that their family's certificate says so.",
    "The applicant stated that they could not upload their ID card because their home scanner broke.",
    "The applicant stated that their sister, Aruzhan, applied last year and is also on file."
  ],
  "decisions": [
    "Eligibility has not been decided.",
    "The application is currently incomplete because the ID card has not been submitted and recorded.",
    "If approved, the grant amount for income band 2 is 150,000 KZT.",
    "The official applicant record is the source of truth for eligibility."
  ],
  "constraints": [
    "The applicant can only come to the office on Thursdays because they have lab sessions during the rest of the week.",
    "Eligibility requires official-record GPA of at least 2.67, income band 1 or 2, and submission of both the transcript and ID card.",
    "The available information does not confirm a deadline or alternative submission method for the ID card.",
    "The available information does not confirm same-day decision-making after the ID card is submitted."
  ],
  "open_questions": [
    "Whether a scanned employer letter counts or whether the original is required.",
    "Whether bringing the ID card on Thursday will result in a decision on the same day."
  ],
  "language": "Kazakh and English"
}

### Written answers

**1. What did compression buy?** Peak tokens both ways, probes retrieved both
ways, and â€” if a probe was lost â€” which one and which turn it came from.

> In the completed compressed run, the logged token count peaked at 819
tokens, and all five probes were retrieved correctly. The compressed state
therefore preserved the tested identity, missing document, grant amount,
Thursday constraint, and open question.

I could not measure the corresponding no-compression run because the API
project had exhausted its available credits before the run could be
completed. Therefore I cannot make a measured A-versus-B token saving claim
from this experiment.

**2. Why must the state be structured rather than a paragraph?** You could have
asked for "a summary". Say what changes when the summary is an object with
named fields.

> A structured state separates different kinds of information into named
fields such as facts, decisions, constraints, and open_questions.
This makes the information easier for the program to retrieve and validate.
A paragraph can contain the same information, but a downstream program
would need to interpret the prose again and could confuse a fact with a
decision or an unanswered question.

The schema also prevents arbitrary extra fields and requires every field to
be present, which makes subsequent processing more predictable.

**3. What is missing from your state that you would add?** Name what you would
add and what you would drop to pay for it.

> I would add a structured evidence_turns field recording which conversation
turn supports each important fact or decision. This would improve
traceability when a compressed state is later questioned.

To keep the state compact, I would remove lower-value narrative details
such as the sentence about the applicant's sister being on file, unless
that fact is needed for the application. I would preserve eligibility
requirements, missing documents, constraints, and open questions.

**4. When is compression the wrong choice?** Name a conversation where it would
lose something that cannot be recovered, and say whether your program would
notice.

> Compression is a poor choice when the exact wording or complete chronology
is itself important, such as a legal investigation, an incident report, or
a conversation where a precise quotation is evidence.

A summary could preserve the general meaning while losing the exact
wording, ordering, or context. My current structured state would not
necessarily notice that information was lost because its schema validates
structure and field types, not completeness against the original
conversation.

---

## Sublab Hard â€” stories in, CVs out, the best candidate by code

### Part 1 â€” extraction

| Story | Parsed? | Valid? | Fields that came back `null` | Traps hit |
|---|---|---|---|---|
| story-01 | Not run — API quota exhausted | Not available | Not available from actual API run | GPA stated; published papers |
| story-02 | Not run — API quota exhausted | Not available | Not available from actual API run | no GPA stated |
| story-03 | Not run — API quota exhausted | Not available | Not available from actual API run | GPA on another scale; unpublished/under-review paper excluded |
| story-04 | Not run — API quota exhausted | Not available | Not available from actual API run | submitted/under-review and in-preparation papers excluded |
| story-05 | Not run — API quota exhausted | Not available | Not available from actual API run | unpublished paper excluded |
| story-06 | Not run — API quota exhausted | Not available | Not available from actual API run | self-contradictory story |

The four traps, for reference: no GPA stated Â· a GPA on another scale Â· a paper
that is not published Â· a story that contradicts itself.

Paste the extraction for **story-06**, the one that contradicts itself:

{
  "candidate_id": "C-06",
  "name": "Nurzhan Abilov",
  "education": {
    "degree": "BSc Statistics",
    "graduation_year": null,
    "gpa": null,
    "gpa_scale": null,
    "ambiguity": [
      "The story says the candidate graduated in 2024 and later says the candidate is currently in the final year and graduating in 2026.",
      "The story gives a GPA of 3.2 and later says the GPA is actually 3.5."
    ]
  },
  "research": {
    "published_papers": 1,
    "ambiguity": [
      "One local poster is not counted as a published paper."
    ]
  },
  "experience_months": 40,
  "languages": [
    "Kazakh",
    "Russian",
    "English"
  ],
  "evidence": [
    "BSc Statistics",
    "graduated in 2024",
    "currently final-year graduating in 2026",
    "GPA 3.2",
    "GPA actually 3.5",
    "one published peer-reviewed proceedings paper",
    "one local poster",
    "insurance analytics since February 2023, about 40 months"
  ]
}

### Part 2 â€” scores and the winner

| Candidate | academic (0â€“5) | research (0â€“5) | experience (0â€“5) | weighted total (code) |
|---|---|---|---|---|
| story-01 | Not run | Not run | Not run | Not computed |
| story-02 | Not run | Not run | Not run | Not computed |
| story-03 | Not run | Not run | Not run | Not computed |
| story-04 | Not run | Not run | Not run | Not computed |
| story-05 | Not run | Not run | Not run | Not computed |
| story-06 | Not run | Not run | Not run | Not computed |

**Winner, computed by my code:**
Not available. The actual six-candidate API scoring run could not be
completed because the OpenAI project returned
insufficient_quota / credit_balance_exhausted.

**The model's prose answer, asked separately ("who should win?"):**
Not available because the actual prose-ranking API call could not be
completed.
>
```

### Part 3 â€” written answers

**1. Which rule did you have to add, and what broke without it?** Name the
story that forced it.

> I added the rule that a publication counts only when it is actually
published or accepted. Submitted, under-review, in-preparation, or
otherwise unpublished work must not count as a publication.

Story-03 particularly demonstrates why this rule is necessary: it contains
one published peer-reviewed conference paper and another paper that has been
under review since March 2026. Only the published paper should count.
Story-04 and story-05 provide similar cases.

**2. Where did the model guess, and where did your code have to decide?** One
example of each, from your run.

> The extraction model is responsible for interpreting natural-language
stories and converting them into structured fields. For example, story-03
gives a GPA of 4.6/5.0, so the model must interpret the scale and preserve
the original value while converting it to the required 4.0 scale.

The code decides the final weighted total and ranking from the structured
numeric scores. This separation is important because the model should not
be allowed to replace the deterministic ranking calculation with prose.

**3. Did your prose ranking and your computed ranking agree?** Say which one
you trust and why â€” and if they agreed, what you would need to see before
trusting the prose one alone.

> The actual prose ranking and six-candidate computed ranking could not be
compared because the API quota was exhausted before those calls completed.

I would trust the computed ranking when the extraction and scoring fields
have been validated, because the final weighted calculation is deterministic
and reproducible. I would only trust a prose ranking alone if it were
independently checked against the structured scores and the same rubric,
including verification that the model did not invent evidence or silently
use a different weighting.

**4. The rubric has no anchor for a contradicted field.** The stories say 3.2
and then 3.5; the rubric defines a 0 and a 5 and nothing in between for this
case. Say what you did and what the rule should be.

> I would not average 3.2 and 3.5 and I would not arbitrarily select the
later value. The extraction should return null for the contradicted GPA
and record the contradiction in an ambiguity field.

The rule should explicitly state that contradictory source information is
unresolved unless there is an authoritative source or a deterministic
precedence rule. The scoring stage should then handle the unresolved value
explicitly rather than treating it as an ordinary numeric GPA.

**5. How close were your top two candidates?** If they were within 0.05, say
what you would tell the committee and what you would change in the extraction
to make that call defensible.

> The actual six-candidate API ranking was not completed, so I cannot report
the distance between the actual top two candidates.

If two candidates were within 0.05, I would treat the difference as a
narrow numerical separation and inspect the underlying extracted evidence
rather than relying on the prose ranking. I would improve the extraction by
requiring evidence for every scored field, preserving original GPA and
scale, explicitly marking ambiguity, and making publication status
deterministic.

---

## Reflection (optional, one short paragraph)

Having now written a role prompt, compressed a conversation, and ranked six
extractions â€” what will you do differently the next time you build something
that has to get reliable structured output out of a model?

Having worked through the three sublabs, I would separate model
interpretation from deterministic program logic more carefully. I would
use the model for tasks such as interpreting natural language, producing
structured evidence, and generating explanations, but I would keep
business-critical validation, policy checks, calculations, and ranking in
code. I would also validate structured outputs against a schema, preserve
provenance/evidence for important fields, explicitly represent ambiguity,
and avoid treating a role prompt or prose answer as a correctness boundary.

>


