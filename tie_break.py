from functools import cmp_to_key

VALID_PENALTIES = {"DSQ", "DNF"}

def _numeric_value(result, race_results, dns):
    """Translate any race result into a numeric score."""
    if isinstance(result, int):
        return result                       # normal place
    if isinstance(result, str) and result in VALID_PENALTIES:
        dsq = len([v for v in race_results.values() if isinstance(v, int)]) + 1
        return dsq                          # DSQ / DNF
    return dns                              # DNS (not in race dict)

def _compare_A8(p1, p2, all_races, dns):
    """
    Implements World-Sailing rule A8 for two already-tied boats.
    Returns ‑1 if p1 beats p2, +1 if p2 beats p1, 0 if still tied.
    """
    # ---- A8.1  best-to-worst comparison (exclude nothing in our model) ----
    scores1 = []
    scores2 = []
    for race in all_races.values():
        scores1.append(_numeric_value(race.get(p1), race, dns))
        scores2.append(_numeric_value(race.get(p2), race, dns))

    for s1, s2 in zip(sorted(scores1), sorted(scores2)):   # best → worst
        if s1 != s2:
            return -1 if s1 < s2 else 1

    # ---- A8.2  last-race, next-to-last … ----
    for race_no in sorted(all_races.keys(), reverse=True): # last → first
        race = all_races[race_no]
        s1 = _numeric_value(race.get(p1), race, dns)
        s2 = _numeric_value(race.get(p2), race, dns)
        if s1 != s2:
            return -1 if s1 < s2 else 1
    return 0

def _cmp(p1, p2, all_races, totals):
    """Full ordering: total score first, then A8."""
    if totals[p1] != totals[p2]:
        return totals[p1] - totals[p2]
    participants = set().union(*(r.keys() for r in all_races.values()))
    dns = len(participants) + 1
    return _compare_A8(p1, p2, all_races, dns)

def sort_participants(participants, all_races, totals):
    """Return `participants` sorted by total then A8 rules."""
    return sorted(
        participants,
        key=cmp_to_key(lambda a, b: _cmp(a, b, all_races, totals))
    )
