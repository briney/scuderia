#!/usr/bin/env python3
"""Derive author slugs from names, handling diacritics and PubMed name misparsing.

Slug convention: <surname>-<given> with the FULL first name, ASCII-folded.
Examples:
  slugify("Ciesiołkiewicz", "Łukasz")  ->  ciesiokiewicz-lukasz
  slugify("Heo", "Tae Won")            ->  heo-tae-won
  slugify("Lo Surdo", "Paola")         ->  lo-surdo-paola

PubMed sometimes misparses Asian names (splitting "Tae Won Heo" as
LastName="Won Heo", ForeName="Tae") and Italian particle surnames
(Lo Surdo -> LastName="Surdo", ForeName="Paola Lo"). When CrossRef
given/family data is available, it is authoritative for these cases.

Usage:
  # Single name
  python3 slugify_name.py --family "Ciesiołkiewicz" --given "Łukasz"

  # With CrossRef cross-check (detects/fixes name misparsing)
  python3 slugify_name.py --family "Won Heo" --given "Tae" \\
    --crossref-family "Heo" --crossref-given "Tae Won"

  # Batch from PubMed XML (outputs JSON array)
  python3 slugify_name.py --pubmed-xml /tmp/pmid.xml

  # Token-filter ledger entries for short surnames (avoids substring false positives)
  python3 slugify_name.py --filter-surname "Yi" --ledger-file people/_ledger.yaml
"""

import argparse
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

# ── Diacritic pre-map ──────────────────────────────────────────────
# NFKD decomposes most accented Latin chars (á→a, ü→u) but NOT these.
# Without the pre-map, .encode('ascii','ignore') strips them entirely:
# Łukasz→ukasz (should be lukasz), Søren→Sren (should be soren).
_PRE_MAP = {
    'ł': 'l', 'Ł': 'l', 'ø': 'o', 'Ø': 'o', 'đ': 'd', 'Đ': 'd',
    'ð': 'd', 'Ð': 'd', 'ı': 'i', 'İ': 'i', 'ß': 'ss', 'þ': 'th',
    'Þ': 'th', 'æ': 'ae', 'Æ': 'ae', 'œ': 'oe', 'Œ': 'oe',
    'ŋ': 'n', 'Ŋ': 'n', 'ə': 'e', 'Ə': 'e',
}


def slugify(text: str) -> str:
    """ASCII-fold and slugify a name component."""
    for k, v in _PRE_MAP.items():
        text = text.replace(k, v)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def make_slug(family: str, given: str) -> str:
    """Build <surname>-<given> slug from family and given names."""
    return f"{slugify(family)}-{slugify(given)}"


def make_display_name(family: str, given: str) -> str:
    """Build display name (retains diacritics)."""
    return f"{given} {family}".strip()


# ── Name misparsing detection ──────────────────────────────────────

_ITALIAN_PARTICLES = {"lo", "la", "di", "de", "della", "dello"}


def detect_misparse(pubmed_lastname: str, pubmed_forename: str,
                    crossref_family: str | None = None,
                    crossref_given: str | None = None):
    """Detect PubMed name misparsing; return corrected (family, given) if found.

    Detection signals:
    - Korean/Asian: PubMed LastName contains a space (two words) — almost
      always a misparse where a two-syllable given name was absorbed into
      the surname. CrossRef family/given is authoritative.
    - Italian particle: PubMed ForeName ends with an Italian particle
      (Lo, La, Di, De, Della, Dello) — the particle was misplaced from
      the surname into the given name. CrossRef family/given is authoritative.
    """
    if crossref_family and crossref_given:
        # Korean/Asian misparse: LastName has a space
        if ' ' in pubmed_lastname.strip():
            return crossref_family, crossref_given, "asian_name_misparse"
        # Italian particle misparse: ForeName ends with a particle
        forename_tokens = pubmed_forename.strip().split()
        if forename_tokens and forename_tokens[-1].lower() in _ITALIAN_PARTICLES:
            return crossref_family, crossref_given, "italian_particle_misparse"
    return pubmed_lastname, pubmed_forename, None


# ── Short-surname token filtering ──────────────────────────────────

def filter_token_matches(surname: str, entries: list) -> list:
    """Filter ledger entries to token-match (not substring-match) the surname.

    A bare grep 'name:.*Yi' matches Yiyang, Yiming, Yin, Ying — dozens of
    false positives. This filters to entries whose name field contains the
    surname as a discrete token.
    """
    surname_lower = surname.lower()
    results = []
    for entry in entries:
        name = entry.get('name', '')
        eslug = entry.get('slug', '')
        # Token match on name
        if surname_lower in name.lower().split():
            results.append(entry)
        # Slug prefix match (less prone to substring noise)
        elif eslug.startswith(surname_lower + '-'):
            results.append(entry)
    return results


# ── PubMed XML batch extraction ────────────────────────────────────

def extract_authors_from_pubmed_xml(xml_path: str) -> list:
    """Extract all authors from a PubMed XML file.

    Returns list of dicts: {family, given, orcid, slug, display_name}
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Scope to the article's own AuthorList (not reference-list authors)
    authors = []
    for author in root.findall('.//AuthorList/Author'):
        lastname = (author.findtext('LastName') or '').strip()
        forename = (author.findtext('ForeName') or '').strip()
        orcid_el = author.find(".//Identifier[@Source='ORCID']")
        orcid = orcid_el.text.strip() if orcid_el is not None and orcid_el.text else None

        if not lastname:
            # Collective/corporate authorship
            collectivename = (author.findtext('CollectiveName') or '').strip()
            if collectivename:
                slug = slugify(collectivename)
                authors.append({
                    'family': collectivename, 'given': '',
                    'orcid': orcid, 'slug': slug,
                    'display_name': collectivename,
                    'note': 'corporate authorship',
                })
            continue

        slug = make_slug(lastname, forename)
        display = make_display_name(lastname, forename)
        authors.append({
            'family': lastname, 'given': forename,
            'orcid': orcid, 'slug': slug,
            'display_name': display,
        })
    return authors


# ── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Derive author slugs from names.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--family', help='Surname (single-name mode)')
    group.add_argument('--pubmed-xml', help='PubMed XML file (batch mode)')
    group.add_argument('--filter-surname', help='Short surname to token-filter')
    parser.add_argument('--given', default='', help='Given name (single-name mode)')
    parser.add_argument('--crossref-family', help='CrossRef family name (cross-check)')
    parser.add_argument('--crossref-given', help='CrossRef given name (cross-check)')
    parser.add_argument('--ledger-file', help='Ledger YAML file (for --filter-surname)')
    args = parser.parse_args()

    if args.family:
        family, given = args.family, args.given
        correction = None
        if args.crossref_family and args.crossref_given:
            family, given, correction = detect_misparse(
                args.family, args.given,
                args.crossref_family, args.crossref_given)
        slug = make_slug(family, given)
        display = make_display_name(family, given)
        result = {'slug': slug, 'name': display,
                  'family': family, 'given': given}
        if correction:
            result['corrected'] = True
            result['correction'] = correction
            result['original_pubmed'] = f"{args.family} / {args.given}"
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.pubmed_xml:
        authors = extract_authors_from_pubmed_xml(args.pubmed_xml)
        print(json.dumps(authors, ensure_ascii=False, indent=2))

    elif args.filter_surname:
        if not args.ledger_file:
            print("--filter-surname requires --ledger-file", file=sys.stderr)
            sys.exit(1)
        # Parse ledger entries (simple YAML — just extract name/slug pairs)
        import re as _re
        with open(args.ledger_file) as f:
            content = f.read()
        # Naive extraction: find all - slug: ... name: ... pairs
        entries = []
        for m in _re.finditer(
            r'-\s+slug:\s*(\S+)\s*\n\s*name:\s*(.+)',
            content
        ):
            entries.append({'slug': m.group(1), 'name': m.group(2).strip()})
        matches = filter_token_matches(args.filter_surname, entries)
        print(json.dumps(matches, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
