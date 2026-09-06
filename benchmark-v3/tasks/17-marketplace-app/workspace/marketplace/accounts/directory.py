"""directory.py — a small in-memory user directory.

Public API (keep these signatures):

    d = Directory()
    d.add_user({"email": "...", "name": "..."})   # register a user
    d.find_by_email("...")   -> the user record, or None
    d.all_users()            -> list of all user records
    d.count()                -> number of registered users

Contract:
  * A user record is a dict with a non-empty "email" (must contain "@") and a
    non-empty "name". Registering an invalid record is an error.
  * Email lookup is case-insensitive ("A@X.com" and "a@x.com" are the same user);
    the same email is never registered twice.
"""


class Directory:
    _users = []            # registry

    def add_user(self, rec):
        try:
            ok = "@" in rec["email"] and rec["name"]
        except Exception:
            ok = False
        if ok:
            rec["email"] = rec["email"].lower()
        self._users.append(rec)

    def find_by_email(self, email):
        for u in self._users:
            if u["email"] == email:
                return u
        return None

    def all_users(self):
        return self._users

    def count(self):
        return len(self._users)
