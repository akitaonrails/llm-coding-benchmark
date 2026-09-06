"""Reference: correct semver range satisfaction (npm-style subset)."""
import re

_CORE = r"(\d+|x|X|\*)(?:\.(\d+|x|X|\*))?(?:\.(\d+|x|X|\*))?"
_PRE = r"(?:-([0-9A-Za-z.-]+))?"
_VER_RE = re.compile(r"^\s*[v=]?\s*" + _CORE + _PRE + r"(?:\+[0-9A-Za-z.-]+)?\s*$")


def _parse_version(v):
    m = _VER_RE.match(v)
    if not m:
        raise ValueError(f"bad version {v!r}")
    maj, mn, pa, pre = m.group(1), m.group(2), m.group(3), m.group(4)
    return (int(maj), int(mn or 0), int(pa or 0), _split_pre(pre))


def _split_pre(pre):
    if not pre:
        return None
    return tuple(int(x) if x.isdigit() else x for x in pre.split("."))


def _cmp_pre(a, b):
    # a, b are prerelease tuples or None. None (release) > any prerelease.
    if a is None and b is None:
        return 0
    if a is None:
        return 1
    if b is None:
        return -1
    for x, y in zip(a, b):
        xn, yn = isinstance(x, int), isinstance(y, int)
        if xn and yn:
            if x != y:
                return -1 if x < y else 1
        elif xn != yn:
            return -1 if xn else 1  # numeric identifiers < alphanumeric
        else:
            if x != y:
                return -1 if x < y else 1
    if len(a) != len(b):
        return -1 if len(a) < len(b) else 1
    return 0


def _cmp(a, b):
    for i in range(3):
        if a[i] != b[i]:
            return -1 if a[i] < b[i] else 1
    return _cmp_pre(a[3], b[3])


class _Comp:
    __slots__ = ("op", "ver")

    def __init__(self, op, ver):
        self.op = op
        self.ver = ver  # parsed tuple

    def has_pre(self):
        return self.ver[3] is not None

    def test(self, v):
        c = _cmp(v, self.ver)
        return {"<": c < 0, "<=": c <= 0, ">": c > 0, ">=": c >= 0, "=": c == 0}[self.op]


def _xr(part):
    return part in (None, "", "x", "X", "*")


def _expand(token):
    """Expand one range token into a list of _Comp (ANDed)."""
    token = token.strip()
    if token == "" or token == "*":
        return [_Comp(">=", (0, 0, 0, None))]

    # hyphen range: "a - b"
    # (handled by caller splitting on ' - '); here token is a single comparator/range.
    m = re.match(r"^(\^|~|>=|<=|>|<|=)?\s*(.+)$", token)
    if not m:
        raise ValueError(f"bad range token {token!r}")
    op, rest = m.group(1), m.group(2).strip()
    cm = re.match(r"^[v=]?\s*" + _CORE + _PRE + r"(?:\+[0-9A-Za-z.-]+)?$", rest)
    if not cm:
        raise ValueError(f"bad range token {token!r}")
    maj, mn, pa, pre = cm.group(1), cm.group(2), cm.group(3), cm.group(4)
    pre_t = _split_pre(pre)

    def num(x):
        return int(x)

    # x-ranges (only meaningful without an explicit comparator, or with =)
    if op in (None, "="):
        if _xr(maj):
            return [_Comp(">=", (0, 0, 0, None))]
        if _xr(mn):
            lo = (num(maj), 0, 0, None)
            hi = (num(maj) + 1, 0, 0, None)
            return [_Comp(">=", lo), _Comp("<", hi)]
        if _xr(pa):
            lo = (num(maj), num(mn), 0, None)
            hi = (num(maj), num(mn) + 1, 0, None)
            return [_Comp(">=", lo), _Comp("<", hi)]
        return [_Comp("=", (num(maj), num(mn), num(pa), pre_t))]

    ver = (num(maj), num(mn or 0), num(pa or 0), pre_t)
    if op in (">", ">=", "<", "<="):
        return [_Comp(op, ver)]

    if op == "~":  # ~1.2.3 -> >=1.2.3 <1.3.0 ; ~1.2 -> >=1.2.0 <1.3.0 ; ~1 -> >=1.0.0 <2.0.0
        lo = ver
        if not _xr(mn):
            hi = (num(maj), num(mn) + 1, 0, None)
        else:
            hi = (num(maj) + 1, 0, 0, None)
        return [_Comp(">=", lo), _Comp("<", hi)]

    if op == "^":  # allow changes that don't modify the left-most non-zero element
        lo = ver
        M, m2, p = num(maj), num(mn or 0), num(pa or 0)
        if M > 0 or _xr(mn):
            hi = (M + 1, 0, 0, None)
        elif m2 > 0 or _xr(pa):
            hi = (0, m2 + 1, 0, None)
        else:
            hi = (0, 0, p + 1, None)
        return [_Comp(">=", lo), _Comp("<", hi)]

    raise ValueError(f"unhandled op {op!r}")


def _parse_group(group):
    """One AND-group -> list of _Comp. Handles hyphen ranges."""
    group = group.strip()
    hy = re.match(r"^(.+?)\s+-\s+(.+)$", group)
    if hy:
        left = _parse_version(hy.group(1).strip() + ("" if "-" in hy.group(1) else ""))
        # lower bound is >= left (as given)
        comps = [_Comp(">=", _parse_version(hy.group(1).strip()))]
        # upper bound: partial right side becomes an upper wildcard
        rm = re.match(r"^[v=]?\s*" + _CORE + _PRE + r"$", hy.group(2).strip())
        if not rm:
            raise ValueError(f"bad hyphen range {group!r}")
        rmaj, rmn, rpa = rm.group(1), rm.group(2), rm.group(3)
        if _xr(rmn):
            comps.append(_Comp("<", (int(rmaj) + 1, 0, 0, None)))
        elif _xr(rpa):
            comps.append(_Comp("<", (int(rmaj), int(rmn) + 1, 0, None)))
        else:
            comps.append(_Comp("<=", _parse_version(hy.group(2).strip())))
        _ = left
        return comps
    comps = []
    for tok in group.split():
        comps.extend(_expand(tok))
    return comps


def satisfies(version, range_spec):
    """Return True iff `version` satisfies `range_spec` (npm-style)."""
    v = _parse_version(version)
    for group in range_spec.split("||"):
        comps = _parse_group(group)
        if not comps:
            continue
        if not all(c.test(v) for c in comps):
            continue
        # prerelease-match rule: a prerelease version only satisfies the group if some
        # comparator in it names the same [maj,minor,patch] AND has a prerelease.
        if v[3] is not None:
            if not any(c.has_pre() and c.ver[:3] == v[:3] for c in comps):
                continue
        return True
    return False
