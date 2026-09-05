"""Reference: all five boundaries hardened."""
import ast
import os
import re
import sqlite3
from decimal import Decimal, InvalidOperation


def find_user(conn: sqlite3.Connection, username: str):
    cur = conn.execute("SELECT id, username, role FROM users WHERE username = ?", (username,))
    return cur.fetchall()


def safe_path(base_dir: str, filename: str) -> str:
    base = os.path.realpath(base_dir)
    full = os.path.realpath(os.path.join(base, filename))
    if full != base and not full.startswith(base + os.sep):
        raise ValueError("path escapes base_dir")
    return full


def build_backup_command(filename: str) -> list[str]:
    # argv list, no shell: filename is a single opaque argument.
    return ["gzip", "-k", "--", filename]


def load_config_value(s: str):
    try:
        val = ast.literal_eval(s)  # never executes code
    except (ValueError, SyntaxError, MemoryError, RecursionError) as e:
        raise ValueError(f"invalid config value: {e}") from e
    if not _is_allowed(val):
        raise ValueError("disallowed value type")
    return val


def _is_allowed(v) -> bool:
    if isinstance(v, (int, float, bool, str)) or v is None:
        return True
    if isinstance(v, (list, tuple)):
        return all(_is_allowed(x) for x in v)
    if isinstance(v, dict):
        return all(_is_allowed(k) and _is_allowed(x) for k, x in v.items())
    return False


_MONEY = re.compile(r"^-?\d{1,15}(\.\d{1,2})?$")
_MAX_CENTS = 10 ** 15


def parse_cents(s: str) -> int:
    s = s.strip()
    if not _MONEY.match(s):
        raise ValueError(f"malformed money: {s!r}")
    try:
        cents = int((Decimal(s) * 100).to_integral_value())
    except (InvalidOperation, ValueError) as e:
        raise ValueError(str(e)) from e
    if abs(cents) > _MAX_CENTS:
        raise ValueError("amount out of range")
    return cents
