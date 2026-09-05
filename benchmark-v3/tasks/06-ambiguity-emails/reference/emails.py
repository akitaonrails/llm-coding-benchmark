"""Reference solution: Gmail-specific dot/plus normalization; keep first occurrence."""

_GMAIL = {"gmail.com", "googlemail.com"}


def _key(email):
    e = email.strip().lower()
    local, at, domain = e.rpartition("@")
    if at == "":  # no '@' — treat whole thing as the key
        return e
    if domain in _GMAIL:
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def dedupe(emails):
    seen = set()
    out = []
    for email in emails:
        k = _key(email)
        if k not in seen:
            seen.add(k)
            out.append(email)
    return out
