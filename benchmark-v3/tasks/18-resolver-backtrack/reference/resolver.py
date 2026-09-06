"""Reference: a correct backtracking dependency resolver.

Greedy "always pick the newest satisfying version" is WRONG: the newest version of one
package can force an unsatisfiable constraint elsewhere that an older version would have
avoided. A correct resolver must backtrack.
"""


def _parse(v):
    return tuple(int(x) for x in v.split("."))


def _satisfies(version, spec):
    spec = spec.strip()
    if spec in ("*", ""):
        return True
    v = _parse(version)
    if spec.startswith(">="):
        return v >= _parse(spec[2:].strip())
    if spec.startswith("^"):
        lo = _parse(spec[1:].strip())
        if v < lo:
            return False
        if lo[0] > 0:
            return v[0] == lo[0]
        if lo[1] > 0:
            return v[0] == 0 and v[1] == lo[1]
        return v[0] == 0 and v[1] == 0 and v[2] == lo[2]
    return v == _parse(spec)  # exact


def resolve(registry, root):
    """registry: {name: {version: [[dep_name, spec], ...]}}. root: [[name, spec], ...].
    Return {name: version} satisfying every (transitive) constraint, or None if no such
    assignment exists. When multiple solutions exist, prefer newer versions."""
    def candidates(name, spec):
        vs = [v for v in registry.get(name, {}) if _satisfies(v, spec)]
        return sorted(vs, key=_parse, reverse=True)  # newest first

    # constraints accumulate as {name: [specs]}; assignment maps name->version.
    def backtrack(assign, pending):
        if not pending:
            return dict(assign)
        name, spec = pending[0]
        rest = pending[1:]
        if name in assign:
            return backtrack(assign, rest) if _satisfies(assign[name], spec) else None
        for v in candidates(name, spec):
            # v must also satisfy every other pending spec for the same name
            if not all(_satisfies(v, s2) for (n2, s2) in rest if n2 == name):
                continue
            assign[name] = v
            new_pending = [p for p in rest] + [[d, s] for d, s in registry[name][v]]
            got = backtrack(assign, new_pending)
            if got is not None:
                return got
            del assign[name]
        return None

    return backtrack({}, [list(r) for r in root])
