#!/usr/bin/env python3
"""Schema-driven frontmatter linter for scuderia brains.

Validates a brain against a profile schema (``profiles/<name>/schema.yaml``):

  - Every *.md in page-kind directories has frontmatter matching the schema:
    spine required fields, per-kind required fields, enums, conditional
    requirements, slug shape, kind/directory agreement, slug/filename
    agreement, duplicate slugs.
  - Link-shaped fields (schema ``link_fields``) are lists of
    ``<kind-dir>/<slug>`` strings; targets are existence-checked in a second
    pass (warn-only — broken back-links are recoverable; this surfaces them).
  - The author ledger (schema ``ledger:``), when present, parses; every entry
    carries the required schema; citations resolve; no ledger slug collides
    with a page.
  - Skill frontmatter (schema ``skills:``) matches the declared contract.
  - Named warn-only checks enabled in schema ``checks:``.

Usage:
  lint-frontmatter.py --instance <instance-root> [--schema <schema.yaml>]
                      [--skills-root <dir>]
                      [--paths <file> <file> ... | --changed-since <rev>]
                      [--base <rev>]

Defaults: --instance is the cwd; --schema is profiles/mnemo/schema.yaml
relative to this script's repo checkout; --skills-root is the schema's sibling
``skills/`` directory. ``--brain`` is accepted as a deprecated alias for
``--instance``.

Modes:
  full (default)    lint every page in every page-kind directory. This is
                    what CI runs; it is the only mode whose results are
                    complete (link existence needs the whole graph).
  --paths /         lint only the given files (paths may be absolute or
  --changed-since   instance-relative). ``--changed-since <rev>`` expands to
                    ``git diff --name-only <rev> -- '*.md'`` inside the
                    instance, plus any files that no longer parse
                    (structure is checked everywhere, field content only on
                    the selected files). Use this mode from producers and
                    pre-commit gates: it is the difference between a
                    40-second full run and a sub-second check that still
                    catches the fields a producer actually writes.

Scoped modes check page structure (frontmatter parses, fence intact) on
every page but defer field/content checks (spine, per-kind, enums, links,
ledger, skills) to the selected files only. Link-existence findings for
unselected files are suppressed — they are reported by the next full run.
Exit codes are identical to full mode.

Exit codes:
  0 — no errors (warnings allowed)
  1 — errors (CI gate fails)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

# Conservative list of common first names. Data for the built-in
# `people_slug_order` check — surname-first is the mnemo convention. False
# negatives are fine; the list is small to minimize false positives.
COMMON_FIRST_NAMES = frozenset({
    "aaron", "adam", "alan", "alex", "alice", "amy", "andrew", "ann", "anna",
    "anthony", "barbara", "ben", "bob", "brian", "bruce", "bryan", "carl",
    "carol", "charles", "chris", "christopher", "dan", "daniel", "david",
    "dennis", "donald", "ed", "edward", "elizabeth", "emily", "eric",
    "frank", "fred", "george", "gregory", "ian", "jack", "james", "jane",
    "jason", "jeff", "jennifer", "jessica", "joe", "joel", "john",
    "jonathan", "joseph", "joshua", "karen", "katherine", "ken", "kenneth",
    "kevin", "larry", "laura", "linda", "lisa", "mark", "mary", "matt",
    "matthew", "michael", "michelle", "nancy", "nicole", "patricia",
    "patrick", "paul", "peter", "rachel", "raj", "rebecca", "richard",
    "rob", "robert", "ronald", "ryan", "samuel", "sarah", "scott", "stephen",
    "steve", "steven", "susan", "thomas", "tim", "timothy", "tom", "william",
})

BRAIN_ROOT: Path  # set in main(); used for relative paths in the report


class Report:
    def __init__(self) -> None:
        self.errors: list[tuple[Path, str]] = []
        self.warnings: list[tuple[Path, str]] = []
        # orphans: target → list of (referring_path, field)
        self.orphans: dict[str, list[tuple[Path, str]]] = defaultdict(list)

    def error(self, path: Path, msg: str) -> None:
        self.errors.append((path, msg))

    def warn(self, path: Path, msg: str) -> None:
        self.warnings.append((path, msg))

    def orphan(self, target: str, path: Path, field: str) -> None:
        self.orphans[target].append((path, field))

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(BRAIN_ROOT))
        except ValueError:
            return str(path)

    def emit(self) -> None:
        by_file: dict[Path, list[tuple[str, str]]] = defaultdict(list)
        for path, msg in self.errors:
            by_file[path].append(("ERROR", msg))
        for path, msg in self.warnings:
            by_file[path].append(("WARN", msg))

        if by_file:
            print("\n=== per-file findings ===")
            for path in sorted(by_file):
                print(f"\n{self._rel(path)}")
                for level, msg in by_file[path]:
                    print(f"  [{level}] {msg}")

        if self.orphans:
            by_kind: dict[str, list[str]] = defaultdict(list)
            for target in self.orphans:
                kind_dir = target.split("/", 1)[0]
                by_kind[kind_dir].append(target)

            print("\n=== orphan link targets (warn) ===")
            for kind_dir in sorted(by_kind):
                targets = sorted(by_kind[kind_dir])
                # Cap noise from the people bucket (mostly paper-author stubs)
                if kind_dir == "people" and len(targets) > 20:
                    total_refs = sum(len(self.orphans[t]) for t in targets)
                    print(
                        f"\n{kind_dir}/: {len(targets)} orphan targets, "
                        f"{total_refs} references — showing top 20 by ref count"
                    )
                    targets = sorted(
                        targets, key=lambda t: -len(self.orphans[t])
                    )[:20]
                else:
                    print(f"\n{kind_dir}/:")
                for target in targets:
                    refs = self.orphans[target]
                    print(f"  {target}  ({len(refs)} ref)")
                    for path, field in refs[:3]:
                        print(f"    - {self._rel(path)}  ({field})")
                    if len(refs) > 3:
                        print(f"    ... and {len(refs) - 3} more")

        total_warn = len(self.warnings) + sum(len(v) for v in self.orphans.values())
        print("\n=== summary ===")
        print(f"{len(self.errors)} error(s), {total_warn} warning(s)")


def load_schema(path: Path) -> dict:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        sys.exit(f"fatal: could not load schema {path}: {e}")
    if not isinstance(doc, dict) or "kinds" not in doc:
        sys.exit(f"fatal: {path} is not a profile schema (missing `kinds:`)")
    return doc


def parse_frontmatter(path: Path) -> tuple[dict | None, str | None]:
    """Return (frontmatter_dict, error_message). One is None."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"could not read file: {e}"
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, "missing leading frontmatter block (---)"
    m = re.search(r"\n---\s*(\n|$)", text[4:])
    if not m:
        return None, "missing closing frontmatter block (---)"
    fm_text = text[4 : 4 + m.start()]
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    if fm is None:
        return {}, None
    if not isinstance(fm, dict):
        return None, "frontmatter is not a mapping"
    return fm, None


def check_enums(
    path: Path,
    fm: dict,
    kind_spec: dict,
    report: Report,
) -> None:
    list_enums = set(kind_spec.get("list_enums", []))
    for field, allowed in kind_spec.get("enums", {}).items():
        value = fm.get(field)
        if value is None:
            continue
        if field in list_enums:
            if not isinstance(value, list):
                report.error(path, f"`{field}` is not a list")
                continue
            bad = [v for v in value if v not in allowed]
            if bad:
                report.error(
                    path, f"{field} value(s) {bad} not in {sorted(allowed)}"
                )
        elif value not in allowed:
            report.error(
                path, f"{field} `{value}` not in {sorted(allowed)}"
            )


def lint_page(
    path: Path,
    fm: dict,
    dir_name: str,
    schema: dict,
    all_slugs: set[str],
    report: Report,
) -> None:
    dir_to_kind = {spec["dir"]: kind for kind, spec in schema["kinds"].items()}
    expected_kind = dir_to_kind[dir_name]
    kind_spec = schema["kinds"][expected_kind]
    slug_re = re.compile(schema.get("slug_pattern", r"^[a-z0-9]+(?:-[a-z0-9]+)*$"))

    for f in schema["spine"]["required"]:
        if f not in fm:
            report.error(path, f"missing required field `{f}`")

    kind = fm.get("kind")
    if kind and kind != expected_kind:
        report.error(
            path,
            f"kind `{kind}` does not match directory `{dir_name}/` "
            f"(expected `{expected_kind}`)",
        )

    slug = fm.get("slug")
    if slug is not None:
        if not isinstance(slug, str):
            report.error(path, "slug is not a string")
            slug = None
        else:
            if not slug_re.match(slug):
                report.error(
                    path,
                    f"slug `{slug}` is not lowercase, hyphen-separated, "
                    f"ASCII-only",
                )
            if slug != path.stem:
                report.error(
                    path,
                    f"slug `{slug}` does not match filename `{path.stem}`",
                )
            full_id = f"{dir_name}/{slug}"
            if full_id in all_slugs:
                report.error(path, f"duplicate slug `{full_id}`")
            else:
                all_slugs.add(full_id)

    # Validated optional spine fields (e.g. importance: number in [0,1]).
    for field, rule in schema["spine"].get("validated_optional", {}).items():
        if field not in fm:
            continue
        value = fm[field]
        if rule.get("type") == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                report.error(path, f"{field} `{value!r}` is not a number")
                continue
            lo, hi = rule.get("range", [float("-inf"), float("inf")])
            if not (lo <= float(value) <= hi):
                report.error(path, f"{field} `{value}` outside [{lo}, {hi}]")

    for f in kind_spec.get("required", []):
        if f not in fm:
            report.error(path, f"missing required `{expected_kind}` field `{f}`")

    check_enums(path, fm, kind_spec, report)

    for cond in kind_spec.get("conditional_required", []):
        when = cond["when"]
        if all(fm.get(k) == v for k, v in when.items()) and cond["field"] not in fm:
            when_str = ", ".join(f"{k}: {v}" for k, v in when.items())
            report.error(
                path,
                f"`{cond['field']}` is required when {when_str}",
            )

    # Shape check on link-shaped fields. Existence is the second pass.
    for field in schema.get("link_fields", []):
        v = fm.get(field)
        if v is None:
            continue
        if not isinstance(v, list):
            report.error(path, f"`{field}` is not a list")
            continue
        for i, item in enumerate(v):
            if not isinstance(item, str):
                report.error(path, f"{field}[{i}] is not a string: {item!r}")
            elif "/" not in item:
                report.error(
                    path,
                    f"{field}[{i}] `{item}` not shaped `<kind-dir>/<slug>`",
                )

    # Named built-in checks (warn-only), enabled by schema `checks:`.
    checks = schema.get("checks", {})

    if checks.get("people_slug_order") and expected_kind == "person" and isinstance(slug, str):
        tokens = slug.split("-")
        if len(tokens) == 2 and tokens[0] in COMMON_FIRST_NAMES:
            report.warn(
                path,
                f"people slug `{slug}` may be misordered — first token "
                f"`{tokens[0]}` looks like a first name; convention is "
                f"surname-first (try `{tokens[1]}-{tokens[0]}`)",
            )

    if checks.get("concept_thesis_updated") and expected_kind == "concept":
        if "thesis_updated" not in fm:
            try:
                body = path.read_text(encoding="utf-8")
            except OSError:
                body = ""
            if "## Shifts" in body:
                report.warn(
                    path,
                    "concept has a `## Shifts` section but no `thesis_updated` "
                    "field — concept-refresh cannot tell when the Thesis was "
                    "last synthesized",
                )

    if checks.get("paper_identifiers") and expected_kind == "paper":
        check_paper_identifiers(path, fm, report)


DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
# doi suffix must not carry a trailing dot (punctuation bleed from citations)
PLACEHOLDERS = frozenset({"", "null", "none", "n/a", "tbd"})


def _clean_id(value):
    """Normalize a frontmatter identifier; None for absent/placeholder."""
    if value is None or isinstance(value, bool):
        return None
    s = str(value).strip()
    if s.lower() in PLACEHOLDERS:
        return None
    return s


def check_paper_identifiers(path: Path, fm: dict, report: Report) -> None:
    """Identifier format sanity for paper pages (warn-only).

    Errors of fact — wrong DOI, wrong PMID, truncated authors — need
    canonical-source verification and live in
    ``skills/paper-ingest/scripts/verify_ingest.py`` (Phase 10). This check
    is the cheap structural layer: well-formed identifiers, no placeholder
    strings, DOI not stored as a URL, pmcid prefixed. A malformed
    identifier silently defeats every downstream dedup query that keys on
    it — that is what makes it worth a warning, not trivia.
    """
    # doi: bare form, not a URL, not a placeholder string
    doi = fm.get("doi")
    if doi is not None:
        s = str(doi).strip()
        if s.lower() in PLACEHOLDERS:
            report.warn(
                path,
                f"doi is the placeholder string `{doi!r}` — use explicit "
                f"`doi: null` for papers with no DOI (papers with no DOI "
                f"exist; placeholder strings defeat DOI-keyed dedup)",
            )
        elif s.lower().startswith(("http://", "https://", "doi.org", "dx.doi.org")):
            report.warn(
                path,
                f"doi `{s}` is a URL — store the bare DOI "
                f"(`10.xxxx/suffix`); URL-form defeats DOI-keyed dedup",
            )
        elif not DOI_RE.match(s):
            report.warn(
                path,
                f"doi `{s}` is not shaped `10.<suffix>` — verify against "
                f"the canonical record (Phase 1)",
            )
        elif s != s.rstrip("."):
            report.warn(path, f"doi `{s}` has a trailing period")

    # pmid: a number, or explicit null
    pmid = fm.get("pmid")
    if pmid is not None and not isinstance(pmid, bool):
        s = str(pmid).strip()
        if s.lower() in PLACEHOLDERS:
            report.warn(
                path,
                f"pmid is the placeholder string `{pmid!r}` — use explicit "
                f"`pmid: null`",
            )
        elif not s.isdigit():
            report.warn(
                path,
                f"pmid `{s}` is not a bare integer — verify against PubMed "
                f"(Phase 1)",
            )

    # pmcid: PMC-prefixed
    pmcid = fm.get("pmcid")
    if pmcid is not None:
        s = str(pmcid).strip()
        if s.lower() in PLACEHOLDERS:
            report.warn(
                path,
                f"pmcid is the placeholder string `{pmcid!r}` — use explicit "
                f"`pmcid: null`",
            )
        elif not s.startswith("PMC") or not s[3:].isdigit():
            report.warn(
                path,
                f"pmcid `{s}` is not shaped `PMC<number>` — a bare number "
                f"here is usually a PMID or an article-version integer "
                f"(the PMCID extraction pitfalls in paper-ingest Phase 4 "
                f"produce this class)",
            )

    # arxiv: bare id, not a URL or DOI
    arxiv = fm.get("arxiv")
    if arxiv is not None:
        s = str(arxiv).strip()
        if s.lower() in PLACEHOLDERS:
            report.warn(
                path,
                f"arxiv is the placeholder string `{arxiv!r}` — use explicit "
                f"`arxiv: null`",
            )
        elif not ARXIV_ID_RE.match(s):
            report.warn(
                path,
                f"arxiv `{s}` is not a bare arXiv id "
                f"(`<YYMM>.<NNNNN>` optionally versioned)",
            )


def check_paper_duplicates(
    page_data: list[tuple[Path, dict]],
    report: Report,
) -> None:
    """Corpus-level duplicate-identity check for paper pages.

    Two papers pages sharing a DOI (or a PMID) are the same real-world
    object filed twice. The per-ingest dedup search (paper-ingest Phase
    2) is prose guidance with no mechanical support, so this check is
    the corpus-level net. Reports the *second and later* occurrences; the
    first (canonical) page is named in each message so the merge target
    is visible.
    """
    seen: dict[tuple[str, str], Path] = {}
    for path, fm in page_data:
        if fm.get("kind") != "paper":
            continue
        for field in ("doi", "pmid"):
            v = _clean_id(fm.get(field))
            if v is None:
                continue
            if field == "doi":
                v = v.lower()
            key = (field, v)
            first = seen.get(key)
            if first is None:
                seen[key] = path
            elif first != path:
                report.error(
                    path,
                    f"duplicate `{field}` `{v}` — also on "
                    f"{first.name} (same real-world paper filed twice; "
                    f"merge per paper-ingest Phase 2 stub-replacement)",
                )


def check_link_existence(
    path: Path,
    fm: dict,
    schema: dict,
    all_slugs: set[str],
    ledger_slugs: set[str],
    report: Report,
) -> None:
    ledger_prefix = schema.get("ledger", {}).get("ref_prefix", "people/")
    for field in schema.get("link_fields", []):
        v = fm.get(field)
        if not isinstance(v, list):
            continue
        for item in v:
            if not isinstance(item, str) or "/" not in item:
                continue
            if item in all_slugs:
                continue
            if item.startswith(ledger_prefix) and item in ledger_slugs:
                continue
            report.orphan(item, path, field)


def lint_ledger(
    brain: Path,
    schema: dict,
    all_slugs: set[str],
    report: Report,
) -> set[str]:
    """Validate the author ledger and return the set of ledger slugs.

    Returns an empty set if the ledger is absent or unparseable.
    """
    spec = schema.get("ledger")
    if not spec:
        return set()
    ledger_path = brain / spec["path"]
    if not ledger_path.exists():
        return set()

    required = tuple(spec.get("entry_required", []))
    allowed = frozenset(required + tuple(spec.get("entry_optional", [])))
    cite_prefix = spec.get("citation_prefix", "papers/")
    ref_prefix = spec.get("ref_prefix", "people/")
    slug_re = re.compile(schema.get("slug_pattern", r"^[a-z0-9]+(?:-[a-z0-9]+)*$"))

    try:
        text = ledger_path.read_text(encoding="utf-8")
    except OSError as e:
        report.error(ledger_path, f"could not read ledger: {e}")
        return set()
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        report.error(ledger_path, f"YAML parse error: {e}")
        return set()

    if doc is None:
        return set()
    if not isinstance(doc, dict):
        report.error(ledger_path, "ledger root is not a mapping")
        return set()

    entries = doc.get("entries")
    if entries is None:
        report.error(ledger_path, "missing top-level `entries:` key")
        return set()
    if not isinstance(entries, list):
        report.error(ledger_path, "`entries` is not a list")
        return set()

    ledger_slugs: set[str] = set()
    seen_slugs: set[str] = set()

    for i, entry in enumerate(entries):
        loc = f"entries[{i}]"
        if not isinstance(entry, dict):
            report.error(ledger_path, f"{loc} is not a mapping")
            continue

        extras = set(entry.keys()) - allowed
        if extras:
            report.error(
                ledger_path,
                f"{loc} has unexpected field(s) {sorted(extras)} — "
                f"allowed: {sorted(allowed)}",
            )

        for f in required:
            if f not in entry:
                report.error(ledger_path, f"{loc} missing required `{f}`")

        slug = entry.get("slug")
        if slug is not None:
            if not isinstance(slug, str):
                report.error(ledger_path, f"{loc} slug is not a string")
            elif not slug_re.match(slug):
                report.error(
                    ledger_path,
                    f"{loc} slug `{slug}` is not lowercase, "
                    f"hyphen-separated, ASCII-only",
                )
            else:
                if slug in seen_slugs:
                    report.error(ledger_path, f"{loc} duplicate slug `{slug}`")
                seen_slugs.add(slug)
                full_id = f"{ref_prefix}{slug}"
                if full_id in all_slugs:
                    report.error(
                        ledger_path,
                        f"{loc} slug `{slug}` collides with existing "
                        f"`{full_id}.md` — promoted entries must be "
                        f"removed from the ledger",
                    )
                else:
                    ledger_slugs.add(full_id)

        name = entry.get("name")
        if name is not None and not isinstance(name, str):
            report.error(ledger_path, f"{loc} name is not a string")

        orcid = entry.get("orcid")
        if orcid is not None and not isinstance(orcid, str):
            report.error(ledger_path, f"{loc} orcid is not a string")

        affiliations = entry.get("affiliations")
        if affiliations is not None:
            if not isinstance(affiliations, list):
                report.error(ledger_path, f"{loc} affiliations is not a list")
            else:
                for j, aff in enumerate(affiliations):
                    if not isinstance(aff, str):
                        report.error(
                            ledger_path,
                            f"{loc} affiliations[{j}] is not a string",
                        )

        citations = entry.get("citations")
        if citations is not None:
            if not isinstance(citations, list):
                report.error(ledger_path, f"{loc} citations is not a list")
            elif not citations:
                report.error(
                    ledger_path,
                    f"{loc} citations is empty — an entry exists only "
                    f"to track citations, so the list must be non-empty",
                )
            else:
                seen_cites: set[str] = set()
                for j, cite in enumerate(citations):
                    cloc = f"{loc} citations[{j}]"
                    if not isinstance(cite, str):
                        report.error(ledger_path, f"{cloc} is not a string")
                        continue
                    if not cite.startswith(cite_prefix):
                        report.error(
                            ledger_path,
                            f"{cloc} `{cite}` is not shaped "
                            f"`{cite_prefix}<slug>`",
                        )
                        continue
                    if cite in seen_cites:
                        report.error(
                            ledger_path,
                            f"{cloc} `{cite}` is a duplicate within "
                            f"this entry",
                        )
                    seen_cites.add(cite)
                    if cite not in all_slugs:
                        report.error(
                            ledger_path,
                            f"{cloc} `{cite}` does not resolve to an "
                            f"existing paper page",
                        )

    return ledger_slugs


def lint_skill(path: Path, fm: dict, spec: dict, report: Report) -> None:
    required = frozenset(spec.get("required", []))
    missing = required - set(fm.keys())
    for f in sorted(missing):
        report.error(path, f"missing required skill field `{f}`")

    if not spec.get("allow_extra_fields", False):
        allowed = required | frozenset(spec.get("optional", []))
        extras = set(fm.keys()) - allowed
        if extras:
            report.error(
                path,
                f"unexpected top-level field(s) {sorted(extras)} — skill "
                f"frontmatter is {sorted(required)} only",
            )

    if spec.get("name_matches_dir", True):
        name = fm.get("name")
        if name and path.parent.name != name:
            report.error(
                path,
                f"name `{name}` does not match directory `{path.parent.name}`",
            )

    triggers = fm.get("triggers")
    if triggers is not None and not isinstance(triggers, list):
        report.error(path, "triggers is not a list")


def main() -> int:
    global BRAIN_ROOT

    script_repo = Path(__file__).resolve().parents[1].parent  # core/tools → repo root
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0]
    )
    parser.add_argument("--instance", "--brain", dest="instance", type=Path,
                        default=Path.cwd(),
                        help="instance root to lint (default: cwd); "
                             "--brain is a deprecated alias")
    parser.add_argument("--schema", type=Path,
                        default=script_repo / "profiles" / "mnemo" / "schema.yaml",
                        help="profile schema.yaml")
    parser.add_argument("--skills-root", type=Path, default=None,
                        help="directory containing skills/ to lint "
                             "(default: schema's sibling skills/ dir)")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--paths", nargs="+", type=Path, metavar="FILE",
                       help="lint only these files (instance-relative or "
                            "absolute); structure is still checked everywhere")
    scope.add_argument("--changed-since", dest="changed_since", metavar="REV",
                       help="lint only files changed since git rev REV "
                            "(structure checked everywhere)")
    args = parser.parse_args()

    brain = args.instance.resolve()
    BRAIN_ROOT = brain
    schema = load_schema(args.schema.resolve())
    skills_root = args.skills_root or args.schema.resolve().parent / "skills"

    # --- resolve the scoped file set ---
    selected: set[Path] | None = None
    if args.paths is not None:
        selected = set()
        for raw in args.paths:
            p = raw.resolve()
            if not p.exists():
                sys.exit(f"fatal: --paths file not found: {raw}")
            if brain not in p.parents:
                sys.exit(f"fatal: --paths file outside instance: {raw}")
            selected.add(p)
    elif args.changed_since:
        try:
            out = subprocess.run(
                ["git", "diff", "--name-only", args.changed_since, "--", "*.md"],
                cwd=brain, capture_output=True, text=True, check=True,
            ).stdout
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            sys.exit(f"fatal: --changed-since needs a git repo at {brain}: {e}")
        selected = {(brain / line).resolve() for line in out.splitlines() if line}

    report = Report()
    all_slugs: set[str] = set()
    page_data: list[tuple[Path, dict]] = []

    for spec in schema["kinds"].values():
        dir_path = brain / spec["dir"]
        if not dir_path.is_dir():
            continue
        for path in sorted(dir_path.glob("*.md")):
            if path.name in ("README.md", "INDEX.md"):
                continue
            fm, err = parse_frontmatter(path)
            if err:
                report.error(path, err)
                continue
            assert fm is not None
            if schema.get("checks", {}).get("temp_file_in_page_dir") \
                    and path.name.startswith("_tmp"):
                report.warn(
                    path,
                    "temp-prefixed file in a page directory — promote to a "
                    "real slug or move to working-docs/; snapshotter commit "
                    "was the failure mode (see conventions/quality.md)",
                )
            if selected is not None and path.resolve() not in selected:
                # scoped mode: structure parsed fine. Still index the page's
                # identity — link existence and ledger citations resolve
                # against all_slugs, which must span the whole graph even
                # when content checks are deferred.
                slug = fm.get("slug")
                if isinstance(slug, str) and slug == path.stem:
                    all_slugs.add(f"{spec['dir']}/{slug}")
                continue
            lint_page(path, fm, spec["dir"], schema, all_slugs, report)
            page_data.append((path, fm))

    ledger_slugs = lint_ledger(brain, schema, all_slugs, report)

    # Corpus-level duplicate-identity net (errors). Runs only in full mode —
    # in scoped mode page_data holds just the selected files, and a
    # duplicate is a property of the corpus, not of one file.
    if selected is None and schema.get("checks", {}).get("paper_duplicates"):
        check_paper_duplicates(page_data, report)

    for path, fm in page_data:
        check_link_existence(path, fm, schema, all_slugs, ledger_slugs, report)

    skills_spec = schema.get("skills")
    if skills_spec and skills_root.is_dir():
        for skill_md in sorted(skills_root.glob("*/SKILL.md")):
            if selected is not None and skill_md.resolve() not in selected:
                continue
            fm, err = parse_frontmatter(skill_md)
            if err:
                report.error(skill_md, err)
                continue
            assert fm is not None
            lint_skill(skill_md, fm, skills_spec, report)

    report.emit()
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
