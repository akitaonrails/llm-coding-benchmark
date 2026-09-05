"""safebox: five small operations that each sit on a security boundary.

Implement all five SECURELY (see TASK.md). The starter implementations below are
the naive, VULNERABLE versions — they work for legit input but are exploitable.
You are scored by how many real exploits your version blocks (while still handling
legitimate input correctly). Standard library only.
"""
import sqlite3


def find_user(conn: sqlite3.Connection, username: str):
    """Return rows [(id, username, role), ...] for the given username."""
    # VULNERABLE: string-interpolated SQL (SQL injection).
    cur = conn.execute(f"SELECT id, username, role FROM users WHERE username = '{username}'")
    return cur.fetchall()


def safe_path(base_dir: str, filename: str) -> str:
    """Return the absolute path of `filename` inside base_dir; raise ValueError if it
    would escape base_dir."""
    # VULNERABLE: no traversal check.
    import os
    return os.path.join(base_dir, filename)


def build_backup_command(filename: str) -> list[str]:
    """Return an argv list to back up `filename` (e.g. gzip it). Must be safe to run
    without a shell interpreting metacharacters in `filename`."""
    # VULNERABLE: returns a shell string; a caller running it with a shell is injectable.
    return ["sh", "-c", f"gzip -c {filename} > {filename}.gz"]


def load_config_value(s: str):
    """Parse a single config scalar: int, float, bool, None, str, or a list/dict of
    those. Reject anything else."""
    # VULNERABLE: eval() -> arbitrary code execution.
    return eval(s)  # noqa: S307


def parse_cents(s: str) -> int:
    """Parse a money string like '12.34' into integer cents (1234). Reject inf/nan,
    overflow, scientific-notation abuse, and malformed input with ValueError."""
    # VULNERABLE: float() accepts 'inf'/'nan'/'1e400'; float math loses precision.
    return int(float(s) * 100)
