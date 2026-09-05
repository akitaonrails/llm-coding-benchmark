"""Deduplicate a list of contact emails, keeping one entry per unique person.

NAIVE STARTER — exact string dedup. It does not account for the normalization
rules implied by the examples in TASK.md (case, and Gmail's dot/plus handling).
"""


def dedupe(emails):
    return list(dict.fromkeys(emails))
