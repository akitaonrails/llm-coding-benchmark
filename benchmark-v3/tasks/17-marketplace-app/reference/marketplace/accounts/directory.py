"""Reference: correct contract AND production-grade practices — per-instance state,
input validation, no caller-argument mutation, and no leaking of internal state.
"""


class Directory:
    def __init__(self):
        self._users = []
        self._by_email = {}

    def add_user(self, rec):
        email = (rec or {}).get("email")
        name = (rec or {}).get("name")
        if not email or "@" not in email or not name:
            raise ValueError("invalid user record")
        key = email.lower()
        if key in self._by_email:
            raise ValueError("duplicate email")
        stored = {**rec, "email": key}      # copy; never mutate the caller's dict
        self._by_email[key] = stored
        self._users.append(stored)

    def find_by_email(self, email):
        u = self._by_email.get((email or "").lower())
        return dict(u) if u is not None else None      # copy; no internal leak

    def all_users(self):
        return [dict(u) for u in self._users]          # copies; no internal leak

    def count(self):
        return len(self._users)
