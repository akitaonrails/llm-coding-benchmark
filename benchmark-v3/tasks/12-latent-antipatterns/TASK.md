# Task 12 — Make the user directory production-ready

**Category:** quality · **Language:** Python · **Scoring:** continuous (0–100)

`directory.py` is a small in-memory user directory that a teammate left behind. The
existing tests (`test_directory.py`) pass. **Make this module production-ready** while
keeping the public API (`add_user`, `find_by_email`, `all_users`, `count`) and the
contract described in the module docstring:

- A user record needs a non-empty `name` and a non-empty `email` containing `@`;
  registering an invalid record is an error.
- Email lookup is case-insensitive; the same email is never registered twice.

Standard library only. Edit `directory.py` in place (you may also update the tests if
you find that appropriate).

Your work is graded on a spectrum by a hidden suite covering a range of inputs and
usage patterns — make it correct and robust the way production code must be, not just
enough to pass the tests already present.
