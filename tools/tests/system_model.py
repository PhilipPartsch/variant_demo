"""System-level checks (plan 7 S§2.3) that the schema cannot express, shared by
L4 (real builds) and L5 (mutated copies). Each returns a list of problems.

ubc exports no backlinks, so `has_part` is computed from `part_of`."""

# Vehicle requirements a subsystem covers although none of its parts satisfies
# them yet (not implemented; plan 7 phase 2, D4). Named, like PH01_EXCLUDED.
NOT_IMPLEMENTED: dict[str, str] = {}


def _ids(value):
    return set(value or [])


def parts(needs: dict, sub_id: str) -> set:
    return {i for i, n in needs.items() if sub_id in _ids(n.get("part_of"))}


def covers_mismatch(needs: dict) -> list:
    """SUB_X.covers == union of satisfies of its parts, apart from NOT_IMPLEMENTED."""
    problems = []
    for sid, sub in needs.items():
        if sub["type"] != "subsystem":
            continue
        covers = _ids(sub.get("covers"))
        satisfied = set().union(*(_ids(needs[p].get("satisfies")) for p in parts(needs, sid)))
        extra = covers - satisfied - set(NOT_IMPLEMENTED)
        missing = satisfied - covers
        if extra:
            problems.append(f"{sid} covers {sorted(extra)}, which none of its parts satisfies")
        if missing:
            problems.append(f"{sid} does not cover {sorted(missing)}, which its parts satisfy")
    return problems


def system_tree(needs: dict) -> list:
    """Exactly one system; every subsystem part_of it."""
    systems = sorted(i for i, n in needs.items() if n["type"] == "system")
    if len(systems) != 1:
        return [f"expected exactly one system, found {systems}"]
    return [f"{i} is not part_of {systems[0]}" for i, n in needs.items()
            if n["type"] == "subsystem" and _ids(n.get("part_of")) != {systems[0]}]
