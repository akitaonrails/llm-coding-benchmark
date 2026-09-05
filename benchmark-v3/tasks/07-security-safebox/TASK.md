# Task 07 — Security: harden five boundaries (scored by exploits blocked)

**Category:** security · **Language:** Python · **Scoring:** continuous (0–100)

`safebox.py` has five small functions, each sitting on a real security boundary. The
starter versions work for legitimate input but are **exploitable**. Reimplement all
five so they are **secure while still handling legitimate input correctly**.

You are graded on a **spectrum**: your score is the fraction of a hidden suite of
**real exploit attempts that your code blocks**, combined with legitimate-input
correctness (so "reject everything" scores poorly too). Thoroughness across *all*
five boundaries is what separates a high score from a middling one.

## The five boundaries

1. `find_user(conn, username)` → rows `(id, username, role)`. **SQL injection**: a
   crafted `username` must not return other users, dump the table, or alter data.
2. `safe_path(base_dir, filename)` → absolute path inside `base_dir`, else raise
   `ValueError`. **Path traversal**: `../`, absolute paths, and sneaky variants must
   not escape `base_dir`.
3. `build_backup_command(filename)` → an argv list. **Command injection**: shell
   metacharacters in `filename` (`; rm -rf ~`, `$(...)`, backticks, `|`) must not be
   interpretable as commands when the argv is executed.
4. `load_config_value(s)` → parse a scalar/list/dict of int/float/bool/None/str.
   **Remote code execution**: input like `__import__('os').system(...)` must be
   rejected (`ValueError`/`SyntaxError`), never executed.
5. `parse_cents(s)` → integer cents from a money string. **Numeric abuse**: reject
   `inf`, `nan`, scientific-notation overflow (`1e400`), absurd magnitudes, and
   malformed input; parse legitimate values exactly (no float rounding errors).

Keep the signatures. Standard library only. Legitimate inputs (a normal username, a
relative `a.txt`, a plain filename, `"12.34"`, `"True"`, `"[1, 2, 3]"`) must keep
working.
