#!/usr/bin/env python3
"""validate_identifiers.py — pre-dispatch validation of paper identifiers.

Given a citation triple (title, first-author surname, year) plus candidate
identifiers (pmid / doi / pmcid), verify that each identifier resolves to
the intended paper BEFORE a subagent is dispatched to ingest it.

Motivation: identifiers harvested from a review's bibliography (Semantic
Scholar references API, LLM transcription) are wrong at observed rates of
~70% (ebolavirus dive, 2026-08-05: 7/10 Tier-1 task contexts had a wrong
PMID, DOI, or both). Subagents self-correct via PubMed identity resolution,
but every wrong dispatch costs a full subagent round of wasted work and
risks a page filed under the wrong identity. Validating pre-dispatch is
~2 API calls and <2s per citation.

Resolution sources (landscape-verified 2026-08-05):
  DOI   -> OpenAlex /works/doi:<doi> (fast ~0.3s, returns ids.pmid/pmcid
           AND is_retracted in one call; Crossref /works/<doi> as fallback)
  PMID  -> PubMed esummary, batched (one call for all PMIDs; returns
           title/authors/year/articleids incl. DOI)
  PMCID -> NCBI idconv (NOTE: covers only PMC-archive articles — "not
           found" here does NOT mean invalid; route to esummary)

Match rule (citation-matching best practice: GROBID/anystyle converge on
token-based scoring corroborated by author+year):
  PASS   = token_set_ratio >= 90 AND first-author surname match AND year +/-1
  REVIEW = 75-89, or >=90 with exactly one of surname/year failing
  FAIL   = <75, or surname AND year both wrong
Never pass on title alone (corrections/replies/sister papers share titles).

Recovery (on non-PASS, with --recover): Europe PMC TITLE:"..." exact-phrase
search (best free title lookup in live testing) -> PubMed esearch ladder
(strict -> lenient) as fallback. Crossref query.bibliographic is NOT used —
live testing shows it matches reference lists and returns commentaries.
Accepted recovery requires the full PASS rule, then identifiers are
REPLACED with the recovered ones.

Also surfaces `retracted: true` when OpenAlex (Retraction Watch-sourced)
or Europe PMC pubTypeList says so — cheap early warning for ingest.

Stdlib only. Rate: ~2-3 API calls per citation; a 20-citation batch takes
well under a minute including politeness sleeps. NCBI: <=3 req/s without
an API key (10/s with one); OpenAlex polite pool via mailto.

Usage:
  python3 validate_identifiers.py --title "Structure of the Ebola virus ..." \
      --author Lee --year 2008 --pmid 18615077 --doi 10.1038/nature07082
  python3 validate_identifiers.py --batch citations.json
      where citations.json is [{"title":..., "author":..., "year":...,
                                 "pmid":..., "doi":..., "pmcid":...}, ...]
  python3 validate_identifiers.py --batch citations.json --recover
Exit code: 0 if every citation is PASS or RECOVERED, 1 otherwise.
"""

import argparse
import difflib
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

UA = "mnemo-validate-identifiers/1.1 (mailto:bryan.briney@gmail.com)"  # set your contact
MAILTO = "bryan.briney@gmail.com"  # set your contact — NCBI asks for a real mailto
TIMEOUT = 30

STOP = set("the a an of in on for and or to with by from at as is are was were be been its their we our".split())

PASS_SCORE = 90.0
REVIEW_SCORE = 75.0


def fetch_json(url, retries=2, backoff=4.0):
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
    if last is not None:
        raise last
    raise RuntimeError("fetch failed without exception: %s" % url)


# ------------------------------------------------------------------ matching

def norm_title(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))  # EPMC titles carry inline HTML
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t.lower()).split())


def content_tokens(t):
    return [x for x in norm_title(t).split() if x not in STOP]


def token_set_ratio(a, b):
    """stdlib re-implementation of rapidfuzz.fuzz.token_set_ratio.
    Handles reordered words and subset titles (paraphrases)."""
    A, B = set(content_tokens(a)), set(content_tokens(b))
    if not A or not B:
        return 0.0
    inter = sorted(A & B)
    rest_a = sorted(A - B)
    rest_b = sorted(B - A)
    t0 = " ".join(inter)
    t1 = " ".join(inter + rest_a)
    t2 = " ".join(inter + rest_b)

    def ratio(x, y):
        return difflib.SequenceMatcher(None, x, y).ratio() * 100 if x and y else 0.0

    return max(ratio(t0, t1), ratio(t0, t2), ratio(t1, t2))


def surname_of(name, name_format="surname_first"):
    """Extract surname. PubMed esummary gives 'Lee JE' (surname first);
    OpenAlex display_name gives 'Jeffrey E. Lee' (surname last);
    Crossref supplies family name directly (pass name_format='family')."""
    parts = norm_title(name).split()
    if not parts:
        return None
    if name_format == "surname_last":
        return parts[-1]
    return parts[0]


def match_grade(rec, expected_title, expected_surname, expected_year):
    """Grade one resolved record against the intended citation.
    rec: {title, first_author, year, name_format?}
    Returns (grade, detail) with grade in PASS/REVIEW/FAIL."""
    score = token_set_ratio(expected_title, rec.get("title", ""))
    rec_surname = surname_of(rec.get("first_author", ""),
                             rec.get("name_format", "surname_first"))
    surname_ok = (not expected_surname) or (rec_surname == expected_surname)
    try:
        yr_ok = (not expected_year) or (not rec.get("year")) or \
                abs(int(expected_year) - int(str(rec["year"])[:4])) <= 1
    except (ValueError, TypeError):
        yr_ok = True  # unparseable year is not evidence against
    if score >= PASS_SCORE and surname_ok and yr_ok:
        grade = "PASS"
    elif score < REVIEW_SCORE or (not surname_ok and not yr_ok):
        grade = "FAIL"
    else:
        grade = "REVIEW"
    return grade, {"score": round(score, 1), "surname_match": surname_ok,
                   "year_ok": yr_ok, "resolved_title": rec.get("title", "")[:100],
                   "resolved_first_author": rec.get("first_author", "")}


# ------------------------------------------------------------------ sources

def pubmed_esummary_batch(pmids):
    """One esummary call for many PMIDs. Returns {pmid: record-dict}."""
    if not pmids:
        return {}
    u = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
         f"?db=pubmed&id={','.join(pmids)}&retmode=json")
    d = fetch_json(u)
    out = {}
    for pid in pmids:
        rec = d.get("result", {}).get(str(pid), {})
        if not rec or rec.get("error"):
            out[pid] = {"error": rec.get("error", "not found")}
            continue
        auths = rec.get("authors") or []
        out[pid] = {
            "title": rec.get("title", ""),
            "first_author": auths[0].get("name", "") if auths else "",
            "year": (rec.get("pubdate", "") or "")[:4],
            "doi": next((a["value"] for a in rec.get("articleids", [])
                         if a.get("idtype") == "doi"), None),
            "pmcid": next((a["value"] for a in rec.get("articleids", [])
                           if a.get("idtype") == "pmc"), None),
            "pubtypes": rec.get("pubtype", []),
            "name_format": "surname_first",
        }
    return out


def openalex_work(doi):
    """Best single DOI validator: fast, returns canonical ids + is_retracted."""
    u = (f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}"
         f"?mailto={MAILTO}")
    try:
        m = fetch_json(u)
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    auths = m.get("authorships") or []
    ids = m.get("ids") or {}
    pmid = (ids.get("pmid") or "").rstrip("/").split("/")[-1] or None
    pmcid = (ids.get("pmcid") or "").rstrip("/").split("/")[-1] or None
    return {
        "title": m.get("title", ""),
        "first_author": (auths[0].get("author", {}) or {}).get("display_name", "") if auths else "",
        "year": str(m.get("publication_year", "")),
        "pmid": pmid,
        "pmcid": pmcid,
        "retracted": bool(m.get("is_retracted")),
        "name_format": "surname_last",
    }


def crossref_work(doi):
    u = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    try:
        m = fetch_json(u)["message"]
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    auths = m.get("author") or []
    return {
        "title": (m.get("title") or [""])[0],
        "first_author": (auths[0].get("family", "") if auths else ""),
        "year": str((m.get("issued", {}).get("date-parts") or [[""]])[0][0]),
        "name_format": "family",
    }


def idconv(ids, idtype=None):
    """NCBI ID converter (endpoint moved 2026: now under pmc.ncbi.nlm.nih.gov;
    urllib follows the 301). COVERS ONLY PMC-ARCHIVE ARTICLES — 'not found'
    here does NOT mean the identifier is invalid. ids must be homogeneous
    type (all PMID, all PMCID, or all DOI); max 200 per call."""
    q = f"ids={','.join(ids)}&format=json&tool=mnemo&email={MAILTO}"
    if idtype:
        q += f"&idtype={idtype}"
    u = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?{q}"
    return fetch_json(u).get("records", [])


# ------------------------------------------------------------------ validate

def validate_citation(cit, pmid_cache):
    """cit: {title, author, year, pmid?, doi?, pmcid?}. Returns report dict."""
    expected_title = cit.get("title", "")
    expected_surname = surname_of(cit.get("author", ""), "surname_first")
    expected_year = str(cit.get("year", ""))[:4] or None
    rep = {"input": {k: v for k, v in cit.items() if not k.startswith("_")},
           "checks": [], "recovered": None, "verdict": None}

    pmid = str(cit.get("pmid") or "").strip()
    if pmid:
        rec = pmid_cache.get(pmid, {})
        if rec.get("error"):
            rep["checks"].append({"source": "pubmed:PMID", "grade": "FAIL",
                                  "error": rec["error"]})
        else:
            grade, det = match_grade(rec, expected_title, expected_surname,
                                     expected_year)
            det.update({"source": "pubmed:PMID", "grade": grade,
                        "resolved_doi": rec.get("doi"),
                        "resolved_pmcid": rec.get("pmcid")})
            rep["checks"].append(det)

    doi = (cit.get("doi") or "").strip().lower().rstrip(".")
    if doi:
        rec = openalex_work(doi)
        source = "openalex:DOI"
        if rec.get("error"):
            rec = crossref_work(doi)
            source = "crossref:DOI"
        if rec.get("error"):
            rep["checks"].append({"source": source, "grade": "FAIL",
                                  "error": rec["error"]})
        else:
            grade, det = match_grade(rec, expected_title, expected_surname,
                                     expected_year)
            det.update({"source": source, "grade": grade})
            if rec.get("retracted"):
                det["retracted"] = True
            rep["checks"].append(det)
            if rec.get("pmid"):
                rep.setdefault("canonical", {})["pmid"] = rec["pmid"]
            if rec.get("pmcid"):
                rep.setdefault("canonical", {})["pmcid"] = rec["pmcid"]

    pmcid = (cit.get("pmcid") or "").strip()
    if pmcid:
        try:
            recs = idconv([pmcid], idtype="pmcid")
            r = recs[0] if recs else {}
            if r.get("status") == "error":
                # NOT proof of invalidity — idconv covers only the PMC archive.
                rep["checks"].append({"source": "idconv:PMCID", "grade": "REVIEW",
                                      "note": f"idconv: {r.get('errmsg', 'not found')} "
                                              "(covers PMC archive only — not conclusive)"})
            else:
                conv_pmid = str(r.get("pmid", ""))
                conv_doi = (r.get("doi") or "").lower()
                consistent = True
                if pmid and conv_pmid and conv_pmid != pmid:
                    consistent = False
                if doi and conv_doi and conv_doi != doi:
                    consistent = False
                rep["checks"].append({"source": "idconv:PMCID",
                                      "grade": "PASS" if consistent else "FAIL",
                                      "pmcid_resolves_to_pmid": conv_pmid or None,
                                      "pmcid_resolves_to_doi": conv_doi or None})
        except Exception as e:
            rep["checks"].append({"source": "idconv:PMCID", "grade": "REVIEW",
                                  "error": str(e)})

    # Cross-consistency: supplied PMID and DOI must point at the same record.
    if pmid and doi:
        pm_rec = pmid_cache.get(pmid, {})
        pm_doi = (pm_rec.get("doi") or "").lower()
        if pm_doi:
            rep["checks"].append({"source": "pmid<->doi consistency",
                                  "grade": "PASS" if pm_doi == doi else "FAIL",
                                  "pmid_doi": pm_doi, "input_doi": doi})

    id_checks = [c for c in rep["checks"]
                 if c["source"].split(":")[0] in ("pubmed", "openalex", "crossref")]
    if not id_checks:
        rep["verdict"] = "NOIDS"
    else:
        grades = [c["grade"] for c in id_checks]
        if all(g == "PASS" for g in grades):
            rep["verdict"] = "PASS"
        elif all(g == "FAIL" for g in grades):
            rep["verdict"] = "FAIL"
        else:
            rep["verdict"] = "MIXED"
    return rep


# ------------------------------------------------------------------ recovery

def recover(cit):
    """Title-based recovery. Primary: Europe PMC exact-phrase TITLE search
    (best free title lookup in live testing 2026-08-05). Fallback: PubMed
    esearch ladder. Acceptance requires the full PASS rule."""
    expected_title = cit.get("title", "")
    expected_surname = surname_of(cit.get("author", ""), "surname_first")
    expected_year = str(cit.get("year", ""))[:4] or None

    def accept(rec):
        grade, det = match_grade(rec, expected_title, expected_surname,
                                 expected_year)
        return (grade == "PASS"), det

    # --- Path A: Europe PMC exact-phrase title search
    try:
        q = urllib.parse.quote(f'TITLE:"{expected_title}"')
        u = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search"
             f"?query={q}&format=json&resultType=core")
        results = fetch_json(u).get("resultList", {}).get("result", [])
        best, best_det = None, None
        for r in results[:5]:
            auths = (r.get("authorString") or "").split(",")
            rec = {"title": r.get("title", ""),
                   "first_author": auths[0].strip() if auths else "",
                   "year": str(r.get("pubYear", "")),
                   "name_format": "surname_first"}
            ok, det = accept(rec)
            if ok and (best_det is None or det["score"] > best_det["score"]):
                pubtypes = (r.get("pubTypeList") or {}).get("pubType", [])
                best = {"pmid": r.get("pmid"), "doi": (r.get("doi") or "").lower() or None,
                        "pmcid": r.get("pmcid"), "title": rec["title"],
                        "first_author": rec["first_author"], "year": rec["year"],
                        "source": "europepmc-title",
                        "retracted": any("retract" in str(p).lower() for p in pubtypes)}
                best_det = det
        if best and best_det:
            best["score"] = best_det["score"]
            return best
    except Exception:
        pass
    time.sleep(0.34)

    # --- Path B: PubMed esearch ladder (strict -> lenient)
    toks = sorted(set(content_tokens(expected_title)), key=len, reverse=True)[:6]
    if not toks:
        return None
    base = " ".join(toks) + "[Title]"
    variants = []
    if expected_surname and expected_year:
        variants.append(f"{base} AND {expected_surname}[Author] AND {expected_year}[PDAT]")
    if expected_surname:
        variants.append(f"{base} AND {expected_surname}[Author]")
    variants.append(base)
    ids = []
    for q in variants:
        u = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
             f"?db=pubmed&retmode=json&retmax=5&term={urllib.parse.quote(q)}")
        try:
            ids = fetch_json(u)["esearchresult"].get("idlist", [])
        except Exception:
            ids = []
        if ids:
            break
        time.sleep(0.34)
    if not ids:
        return None
    cands = pubmed_esummary_batch(ids)
    best, best_det = None, None
    for pid, rec in cands.items():
        if rec.get("error"):
            continue
        ok, det = accept(rec)
        if ok and (best_det is None or det["score"] > best_det["score"]):
            best = {"pmid": pid, "doi": rec.get("doi"), "pmcid": rec.get("pmcid"),
                    "title": rec.get("title"), "first_author": rec.get("first_author"),
                    "year": rec.get("year"), "source": "pubmed-esearch",
                    "retracted": any("retract" in str(p).lower()
                                     for p in rec.get("pubtypes", []))}
            best_det = det
    if best and best_det:
        best["score"] = best_det["score"]
    return best


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title")
    ap.add_argument("--author", help="first-author surname")
    ap.add_argument("--year")
    ap.add_argument("--pmid")
    ap.add_argument("--doi")
    ap.add_argument("--pmcid")
    ap.add_argument("--batch", help="JSON file: list of citation dicts")
    ap.add_argument("--recover", action="store_true",
                    help="attempt title-based recovery for non-PASS citations")
    args = ap.parse_args()

    if args.batch:
        with open(args.batch) as f:
            citations = json.load(f)
    elif args.title:
        citations = [{"title": args.title, "author": args.author,
                      "year": args.year, "pmid": args.pmid,
                      "doi": args.doi, "pmcid": args.pmcid}]
    else:
        ap.error("provide --title (single citation) or --batch (JSON file)")

    # Pre-pass: PMCID-only citations get their PMID via NCBI idconv so the
    # PubMed validation path applies. (PMCID alone only supports a
    # consistency check, which cannot confirm the intended paper.)
    for cit in citations:
        if cit.get("pmcid") and not cit.get("pmid"):
            try:
                recs = idconv([str(cit["pmcid"]).strip()], idtype="pmcid")
                if recs and recs[0].get("pmid"):
                    cit["pmid"] = str(recs[0]["pmid"])
                    cit["_pmid_from_pmcid"] = True
            except Exception:
                pass  # leave as-is; will surface as NOIDS

    # Batch esummary for all supplied PMIDs in one call (NCBI allows it).
    all_pmids = [str(c.get("pmid")).strip() for c in citations if c.get("pmid")]
    pmid_cache = {}
    for i in range(0, len(all_pmids), 100):
        pmid_cache.update(pubmed_esummary_batch(all_pmids[i:i + 100]))
        if i + 100 < len(all_pmids):
            time.sleep(0.34)

    reports = []
    for idx, cit in enumerate(citations):
        rep = validate_citation(cit, pmid_cache)
        if rep["verdict"] in ("FAIL", "MIXED", "NOIDS") and args.recover \
                and rep["verdict"] != "NOIDS":
            rec = recover(cit)
            if rec:
                rep["recovered"] = rec
                rep["verdict"] = "RECOVERED"
        reports.append(rep)
        if idx < len(citations) - 1:
            time.sleep(0.4)  # politeness across OpenAlex/Crossref/NCBI calls

    summary = {
        "total": len(reports),
        "pass": sum(1 for r in reports if r["verdict"] == "PASS"),
        "fail": sum(1 for r in reports if r["verdict"] == "FAIL"),
        "mixed": sum(1 for r in reports if r["verdict"] == "MIXED"),
        "recovered": sum(1 for r in reports if r["verdict"] == "RECOVERED"),
        "noids": sum(1 for r in reports if r["verdict"] == "NOIDS"),
    }
    # Dispatch-ready block: for each citation, the identifiers to actually
    # send to the subagent (validated, or recovered if validation failed).
    dispatch = []
    for r in reports:
        cit = r["input"]
        if r["verdict"] == "PASS":
            item = {"title": cit.get("title"), "author": cit.get("author"),
                    "year": cit.get("year"), "pmid": cit.get("pmid"),
                    "doi": cit.get("doi"), "pmcid": cit.get("pmcid"),
                    "status": "validated"}
        elif r["verdict"] == "RECOVERED" and r["recovered"]:
            rec = r["recovered"]
            item = {"title": rec["title"], "author": cit.get("author"),
                    "year": rec.get("year"), "pmid": rec.get("pmid"),
                    "doi": rec.get("doi"), "pmcid": rec.get("pmcid"),
                    "status": "recovered",
                    "note": f"input identifiers wrong; corrected via {rec['source']} "
                            f"(score {rec['score']})"}
        else:
            item = {"title": cit.get("title"), "author": cit.get("author"),
                    "year": cit.get("year"), "status": "HOLD",
                    "note": "validation failed and recovery unsuccessful — "
                            "do not dispatch; resolve manually"}
        for c in r["checks"]:
            if c.get("retracted"):
                item["retracted"] = True
        if r.get("recovered", {}) and r["recovered"].get("retracted"):
            item["retracted"] = True
        dispatch.append(item)

    out = {"summary": summary, "dispatch": dispatch, "reports": reports}
    print(json.dumps(out, indent=2))
    sys.exit(0 if summary["fail"] == 0 and summary["mixed"] == 0 else 1)


if __name__ == "__main__":
    main()
