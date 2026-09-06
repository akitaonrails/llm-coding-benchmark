"""Reference: correct contract AND production-grade practices — per-instance state,
input validation, no caller-argument mutation, and no leaking of internal state.
"""


class Directory:
    def __init__(self):
        self._users = []
        self._by_email = {}

    @staticmethod
    def _norm(email):
        return email.strip().lower() if isinstance(email, str) else ""

    def add_user(self, rec):
        email = (rec or {}).get("email")
        name = (rec or {}).get("name")
        if not isinstance(email, str) or "@" not in email or not name:
            raise ValueError("invalid user record")
        key = self._norm(email)
        if not key or "@" not in key:
            raise ValueError("invalid user record")
        if key in self._by_email:
            raise ValueError("duplicate email")
        stored = {**rec, "email": key}      # copy; never mutate the caller's dict
        self._by_email[key] = stored
        self._users.append(stored)

    def find_by_email(self, email):
        u = self._by_email.get(self._norm(email))
        return dict(u) if u is not None else None      # copy; no internal leak

    def all_users(self):
        return [dict(u) for u in self._users]          # copies; no internal leak

    def count(self):
        return len(self._users)
