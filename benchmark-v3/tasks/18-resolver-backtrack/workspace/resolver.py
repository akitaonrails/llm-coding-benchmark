"""resolver.py — resolve a compatible set of package versions.

Implement `resolve(registry, root)`:
  * registry: {name: {version: [[dep_name, spec], ...]}}  — every package version and
    the dependencies it introduces.
  * root: [[name, spec], ...]  — the top-level requirements.
Return a dict {name: version} that satisfies EVERY (transitive) constraint, or None if
no such assignment exists.

`spec` grammar: "*" (any), ">=x.y.z", "^x.y.z" (compatible: caret), or "x.y.z" (exact).

The starter below works on simple inputs but is INCOMPLETE — it greedily takes the
newest satisfying version and never reconsiders.
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
        return v[0] == lo[0] and v >= lo
    return v == _parse(spec)


def resolve(registry, root):
    assign = {}
    queue = [list(r) for r in root]
    while queue:
        name, spec = queue.pop(0)
        if name in assign:
            continue
        options = [v for v in registry.get(name, {}) if _satisfies(v, spec)]
        if not options:
            return None
        v = sorted(options, key=_parse)[-1]  # newest satisfying — greedy, no backtracking
        assign[name] = v
        for dep in registry[name][v]:
            queue.append(list(dep))
    return assign
