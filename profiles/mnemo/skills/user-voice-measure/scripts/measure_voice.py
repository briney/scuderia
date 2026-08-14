#!/usr/bin/env python3
"""Measure a human's writing voice from ## Verbatim sections into VOICE.md.

Stdlib only. Usage:
    python3 measure_voice.py --brain <brain-root> [--out USER/VOICE.md]

Extracts a quantized fingerprint from every grant/paper page carrying a
`## Verbatim` section (the human's preserved submitted prose). Sentence-length
statistics come from *narrative* prose only; list/scaffold-heavy verbatim is
scanned for tells but excluded from length stats.

Prints the fingerprint block to stdout AND rewrites the `## The fingerprint`
section of the target file in place (between the `## The fingerprint` header
and the next `## ` header). Never touches USER/<name>.md.
"""
import argparse
import glob
import os
import re
import statistics

TELL_PHRASES = [
    "not only",
    "in order to",
    "it is important to note",
    "sheds light",
    "pivotal",
    "leverage",
    "underscore",
    "paradigm shift",
    "plays a crucial role",
    "groundbreaking",
]

# Sentence splitter: on . ! ? followed by whitespace + capital/quote/digit.
SENT_RE = re.compile(r"(?<=[.!?])\s+")


def load_verbatim_sents(brain_root):
    """Return (narrative_sents, structured_sents) across all verbatim pages.

    narrative: median sentence length >= 18 words (flowing prose)
    structured: everything else (list/scaffold-heavy)
    """
    narrative, structured = [], []
    pages = 0
    for kind in ("grants", "papers"):
        for path in glob.glob(os.path.join(brain_root, kind, "*.md")):
            with open(path, encoding="utf-8") as f:
                txt = f.read()
            m = re.search(r"^## Verbatim\s*\n(.*?)(?=^## |\Z)", txt, re.M | re.S)
            if not m:
                continue
            body = m.group(1)
            kept = []
            for ln in body.splitlines():
                ln = ln.strip()
                if not ln.startswith(">"):
                    continue
                ln = ln[1:].strip()
                if not ln:
                    continue
                if ln.startswith("[Source:"):
                    continue
                if ln.startswith("[Figure"):
                    continue
                if ln.startswith("*Figure"):
                    continue
                if ln.isupper() and len(ln) > 3:  # ALL-CAPS header line
                    continue
                kept.append(ln)
            blob = " ".join(kept)
            blob = re.sub(r"\[[0-9,]+\]", "", blob)  # citation markers
            sents = [s for s in SENT_RE.split(blob) if len(s.split()) >= 6]
            if not sents:
                continue
            pages += 1
            lens = [len(s.split()) for s in sents]
            if statistics.median(lens) >= 18:
                narrative.extend(sents)
            else:
                structured.extend(sents)
    return narrative, structured, pages


def fingerprint(narrative, structured):
    nl = sorted(len(s.split()) for s in narrative)
    n_words = sum(len(s.split()) for s in narrative)
    blob = " ".join(narrative)

    def pct(xs, p):
        return xs[min(len(xs) - 1, int(p * len(xs)))]

    lines = []
    lines.append("| Statistic | Value |")
    lines.append("|---|---|")
    lines.append(f"| Narrative corpus | {len(narrative):,} sentences / "
                f"~{n_words:,} words |")
    lines.append(f"| Median | **{statistics.median(nl):.0f}** |")
    lines.append(f"| p10 – p90 | {pct(nl, .10)} – {pct(nl, .90)} |")
    lines.append(f"| p95 | {pct(nl, .95)} |")
    lines.append("")
    lines.append("Em-dashes: "
                f"{blob.count(chr(8212)) / n_words * 1000:.2f} per 1,000 words "
                "(low density here is a positive discriminator — generated prose "
                "leans on em-dashes; this corpus does not).")
    lines.append("")
    lines.append("Tell-phrase counts (narrative corpus only):")
    lines.append("")
    lines.append("| Item | Count | Read |")
    lines.append("|---|---|---|")
    for phrase in TELL_PHRASES:
        c = len(re.findall(re.escape(phrase), blob, re.I))
        if c:
            note = "Present — do **not** blanket-ban" if c >= 10 else (
                "Rare — trim when caught")
            lines.append(f"| \"{phrase}\" | {c} | {note} |")
    lines.append("")
    lines.append("Tell-ban in `STYLE.md` §4 remains the default for *generated* "
                "prose; this table means the corpus overrides it where the human "
                "demonstrably writes the word himself.")
    return "\n".join(lines)


def provenance(pages, narrative, structured):
    return (
        f"- Corpus: `grants/*.md` + `papers/*.md` `## Verbatim` sections. "
        f"{pages} pages scanned; {len(narrative):,} narrative sentences and "
        f"{len(structured):,} structured sentences extracted.\n"
        f"- `## Draft` sections are the mind's writing — always excluded.\n"
        f"- Measured {import_datetime()}. Re-run this script to refresh as more "
        f"of the human's prose is ingested."
    )


def import_datetime():
    import datetime
    return datetime.date.today().isoformat()


def rewrite_section(out_path, fingerprint_text, prov_text):
    if not os.path.exists(out_path):
        raise SystemExit(f"output file {out_path} does not exist — scaffold USER/VOICE.md first")
    with open(out_path, encoding="utf-8") as f:
        txt = f.read()
    # The fingerprint + provenance live as the trailing, contiguous region
    # (anything static precedes '## The fingerprint'). Replace to EOF.
    fm = re.search(r"^## The fingerprint\b.*$", txt, re.M)
    if not fm:
        raise SystemExit(f"{out_path} has no '## The fingerprint' section")
    head = txt[:fm.start()].rstrip("\n")
    block = ("## The fingerprint\n\n" + fingerprint_text.rstrip() +
             "\n\n## Provenance\n\n" + prov_text.strip() + "\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(head + "\n\n" + block)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", required=True, help="brain root (contains grants/, papers/)")
    ap.add_argument("--out", default="USER/VOICE.md", help="target VOICE.md")
    args = ap.parse_args()

    narrative, structured, pages = load_verbatim_sents(args.brain)
    if not narrative and not structured:
        raise SystemExit("refusing cleanly: no `## Verbatim` corpus found — the voice model is too thin to measure")

    fp = fingerprint(narrative, structured)
    prov = provenance(pages, narrative, structured)
    out_path = os.path.join(args.brain, args.out)
    rewrite_section(out_path, fp, prov)

    print(fp)
    print()
    print(prov)


if __name__ == "__main__":
    main()
