#!/usr/bin/env python3
"""compute_contacts.py — compute epitope contact residues for an
antibody-antigen complex instance from its PDB coordinates.

    python3 compute_contacts.py PDB --h H --l L --antigen A[,B] \
        [--cutoff 4.5] [--cache-dir PATH]

Downloads the mmCIF from RCSB (https://files.rcsb.org/download/<PDB>.cif) into
a local cache (default: .sabdab-cif-cache/ under cwd — gitignore it; RCSB is
the immutable archive, the cache is disposable), then finds every antigen
residue with any atom within CUTOFF A (all-atom) of the antibody heavy or
light chain. Waters, ions, glycans and other heterogens are excluded — only
standard polymer ATOM records on the named chains are considered.

Output: JSON {pdb, cutoff, h_chain, l_chain, antigen_chains, h_contacts,
l_contacts, n_atoms} — contacts as "RESNAME###" strings keyed by the chain's
own residue numbering (author seq id), sorted by residue number.
"""
import argparse
import json
import os
import sys
import urllib.request

CIF_URL = "https://files.rcsb.org/download/{pdb}.cif"


def fetch_cif(pdb: str, cache_dir: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{pdb.lower()}.cif")
    if not os.path.exists(path):
        url = CIF_URL.format(pdb=pdb.upper())
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()
        if not data.startswith(b"data_"):
            raise RuntimeError(f"unexpected CIF payload for {pdb} ({len(data)} bytes)")
        with open(path, "wb") as f:
            f.write(data)
    return path


def residue_key(res) -> str:
    seq = res.get_id()[1]
    ins = res.get_id()[2].strip()
    return f"{res.get_resname()}{seq}{ins}"


def compute(path: str, h_chain: str, l_chain: str, antigen_chains: list, cutoff: float):
    from Bio.PDB import MMCIFParser, NeighborSearch
    structure = MMCIFParser(QUIET=True).get_structure("x", path)
    model = structure[0]

    def polymer_atoms(chain_id):
        if chain_id not in model:
            return []
        return [a for r in model[chain_id] if r.get_id()[0] == " " for a in r]

    ab = {c: polymer_atoms(c) for c in [h_chain, l_chain] if c}
    ag_res = {c: [r for r in model[c] if r.get_id()[0] == " "]
              for c in antigen_chains if c in model}
    missing = ([c for c in [h_chain, l_chain] if c and not ab[c]]
               + [c for c in antigen_chains if c not in model])
    out = {}
    for label, chain_id in [("h_contacts", h_chain), ("l_contacts", l_chain)]:
        if not chain_id or not ab[chain_id]:
            out[label] = []
            continue
        ns = NeighborSearch(ab[chain_id])
        contacts = set()
        for c, residues in ag_res.items():
            for r in residues:
                for a in r:
                    if ns.search(a.get_vector().get_array(), cutoff, level="A"):
                        contacts.add(f"{c}:{residue_key(r)}")
                        break
        out[label] = sorted(contacts, key=lambda s: (s.split(":")[0],
                            int("".join(ch for ch in s.split(":")[1] if ch.isdigit()) or 0)))
    out["_missing_chains"] = missing
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdb")
    ap.add_argument("--h", dest="h_chain", default=None)
    ap.add_argument("--l", dest="l_chain", default=None)
    ap.add_argument("--antigen", required=True, help="comma-separated antigen chain ids")
    ap.add_argument("--cutoff", type=float, default=4.5)
    ap.add_argument("--cache-dir", default=".sabdab-cif-cache")
    a = ap.parse_args()
    try:
        path = fetch_cif(a.pdb, a.cache_dir)
    except Exception as e:
        print(json.dumps({"error": f"fetch failed for {a.pdb}: {e}"}))
        sys.exit(2)
    antigen = [c.strip() for c in a.antigen.split(",") if c.strip()]
    res = compute(path, a.h_chain, a.l_chain, antigen, a.cutoff)
    res.update({"pdb": a.pdb.lower(), "cutoff": a.cutoff,
                "h_chain": a.h_chain, "l_chain": a.l_chain,
                "antigen_chains": antigen,
                "note": "computed from coordinates; not a database annotation"})
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
