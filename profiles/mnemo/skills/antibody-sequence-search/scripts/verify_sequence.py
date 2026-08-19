#!/usr/bin/env python3
"""verify_sequence.py — independently confirm a VH/VL against PDB-deposited
chain sequences (RCSB data API). This is the cross-deposition-class check:
patent-derived curations (Thera-SAbDab, PLAbDab) share underlying sources,
but a chain sequence deposited with a structure is an independent vote that
the sequence exists as a physical protein.

    python3 verify_sequence.py --vh SEQ [--vl SEQ] \
        --structures "1n8z:BA/4hkz:BA/6cr1:HL" [--max-pdbs 3]
    python3 verify_sequence.py --vh SEQ --pdb 1n8z

--structures takes the Thera-SAbDab `100% SI Structure` column verbatim
('/'-separated pdb:chains groups). Each PDB's polymer entity sequences are
fetched via the RCSB data API (no mmCIF download). Confirmation requires an
EXACT match of VH (and VL when given) to some entity in the same PDB —
near-matches are reported, never counted.

Output: JSON {verdict, confirmed_by, checks: [{pdb, vh_exact, vl_exact,
best_vh_identity, matched_entity, description}], note}
verdict: "structure-confirmed" | "unconfirmed" | "no-structures" | "conflict"
(conflict = a 100%-SI structure's deposited sequence DISAGREES with the
query — that is a provenance alarm, not a soft miss.)
"""
import json
import sys
import urllib.request

API = "https://data.rcsb.org/rest/v1/core"


def http_json(path, timeout=60):
    with urllib.request.urlopen(API + path, timeout=timeout) as r:
        return json.loads(r.read())


def entity_ids(pdb):
    d = http_json(f"/entry/{pdb.lower()}")
    return d.get("rcsb_entry_container_identifiers", {}).get("polymer_entity_ids", [])


def entity_seq(pdb, eid):
    d = http_json(f"/polymer_entity/{pdb.lower()}/{eid}")
    seq = d.get("entity_poly", {}).get("pdbx_seq_one_letter_code_can", "") or ""
    seq = seq.replace("\n", "").replace(" ", "")
    desc = d.get("rcsb_polymer_entity", {}).get("pdbx_description", "")
    return seq, desc


def identity(a, b):
    """Query coverage: longest common substring of (query a, deposited b) as a
    fraction of the query length. A VH that is a prefix of a deposited Fab
    chain scores 1.0 — full-length constant regions must not count against
    the match. Uses difflib's longest match (ungapped; adequate for
    exact/near-exact verification)."""
    import difflib
    if not a or not b:
        return 0.0
    if a in b:
        return 1.0
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(
        0, len(a), 0, len(b))
    return m.size / len(a)


def check_pdb(pdb, vh, vl):
    ids = entity_ids(pdb)
    best = {"vh_exact": False, "vl_exact": None if vl is None else False,
            "best_vh_identity": 0.0, "matched_entity": None, "description": None}
    for eid in ids:
        seq, desc = entity_seq(pdb, eid)
        if vh:
            # exact = query contained in the deposited chain (VH may be a
            # prefix of a full Fab/IgG chain)
            if vh in seq or seq == vh:
                best["vh_exact"] = True
                best["matched_entity"] = eid
                best["description"] = desc
            best["best_vh_identity"] = max(best["best_vh_identity"], identity(vh, seq))
        if vl and (vl in seq or seq == vl):
            best["vl_exact"] = True
            if best["matched_entity"] is None:
                best["matched_entity"] = eid
                best["description"] = desc
    return best


def main():
    args = sys.argv[1:]
    vh = vl = pdb = structures = None
    max_pdbs = 3
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--vh":
            vh = args[i + 1]; i += 2
        elif a == "--vl":
            vl = args[i + 1]; i += 2
        elif a == "--pdb":
            pdb = args[i + 1]; i += 2
        elif a == "--structures":
            structures = args[i + 1]; i += 2
        elif a == "--max-pdbs":
            max_pdbs = int(args[i + 1]); i += 2
        else:
            print(__doc__); sys.exit(1)
    if not vh:
        print(json.dumps({"error": "--vh is required"}))
        sys.exit(1)

    pdbs = [pdb] if pdb else []
    if structures:
        for grp in structures.split("/"):
            for p in grp.split(";"):  # bispecific rows use ';' between arms
                p = p.split(":")[0].strip().lower()
                if p and p != "none" and p not in pdbs:
                    pdbs.append(p)
    if not pdbs:
        print(json.dumps({"verdict": "no-structures",
                          "note": "no 100%-SI structures supplied; independent "
                                  "confirmation unavailable"}))
        return
    pdbs = pdbs[:max_pdbs]

    checks, confirmed_by, conflict = [], None, False
    for p in pdbs:
        try:
            c = check_pdb(p, vh, vl)
        except Exception as e:
            checks.append({"pdb": p, "error": str(e)[:200]})
            continue
        c["pdb"] = p
        checks.append(c)
        vh_ok = c.get("vh_exact")
        vl_ok = c.get("vl_exact") in (True, None)
        if vh_ok and vl_ok:
            confirmed_by = p
            break
        # conflict alarm: a supposed 100%-SI structure whose best chain is
        # clearly NOT the query (identity < 0.9) suggests a data error
        if c.get("best_vh_identity", 0) and c["best_vh_identity"] < 0.9 and not vh_ok:
            conflict = True

    if confirmed_by:
        verdict = "structure-confirmed"
    elif conflict:
        verdict = "conflict"
    else:
        verdict = "unconfirmed"
    print(json.dumps({
        "verdict": verdict,
        "confirmed_by": confirmed_by,
        "checks": checks,
        "note": "exact-match only; near-matches reported but never counted"
    }, indent=2))


if __name__ == "__main__":
    main()
