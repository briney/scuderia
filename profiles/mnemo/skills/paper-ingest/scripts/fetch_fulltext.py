#!/usr/bin/env python3
"""fetch_fulltext.py — executable form of the paper-ingest full-text decision tree.

Walks the retrieval ladder for a paper and writes the body text to a file,
printing a JSON summary (with the provenance tag for the paper page's
`fulltext_source:` frontmatter field) to stdout.

Ladder order (mirrors skills/paper-ingest-full-text-access/SKILL.md):
  0. Europe PMC REST gate (OA flags + PMCID discovery)
  1. PMC E-utilities XML            -> provenance: pmc-xml
  1b. Europe PMC PDF render         -> provenance: epmc-pdf
  1c/1d. bioRxiv via api.biorxiv.org version check + r.jina.ai reader
                                      -> provenance: biorxiv-jina
  2. Publisher page via r.jina.ai   -> provenance: publisher-jina
  2b. Wayback Machine snapshot      -> provenance: wayback
  (nothing found)                   -> provenance: none  (abstract-only path)

Stdlib only, except PDF extraction which needs pymupdf (pip install pymupdf).

Usage:
  python3 fetch_fulltext.py --pmid 41280071 --out /tmp/wang2026
  python3 fetch_fulltext.py --doi 10.1101/2025.10.27.684659 --out /tmp/pre
  python3 fetch_fulltext.py --pmcid PMC9278498 --out /tmp/leem --figures
  python3 fetch_fulltext.py --doi 10.1146/annurev-virology-092818-015550 \
      --publisher-url https://www.annualreviews.org/content/journals/10.1146/annurev-virology-092818-015550 \
      --out /tmp/greber

Exit code is 0 even when provenance is "none" — the caller branches on the
JSON summary, not the exit code.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.response
import xml.etree.ElementTree as ET
import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path

from source_package import absolute, new_directory, public_url, put, save

UA = "mnemo-fetch-fulltext/1.0 (mailto:you@example.com)"  # set your contact
TIMEOUT = 60
EVIDENCE = None


class EvidenceError(RuntimeError):
    """Fail closed: missing durable evidence cannot become a quiet route miss."""


class AcquisitionEvidence:
    def __init__(self, directory):
        self.root = new_directory(directory)
        self.sequence = 0

    def open(self, req):
        try:
            public_url(req.full_url)
            self.sequence += 1
            attempt = new_directory(self.root / f'attempt-{self.sequence:06d}')
            save(attempt/'request.json', dict(url=req.full_url, method=req.get_method(),
                 started_at=datetime.now(timezone.utc).isoformat(),
                 headers_retained=False, authentication='none supplied by helper'))
        except (OSError, ValueError) as exc:
            raise EvidenceError('cannot reserve safe acquisition evidence') from exc
        counter = 0

        class Capture(urllib.request.HTTPErrorProcessor):
            def http_response(handler, request, response):
                nonlocal counter
                counter += 1
                try:
                    public_url(request.full_url)
                    directory = new_directory(attempt/f'response-{counter:04d}')
                    status = response.code
                    record = dict(url=request.full_url, status=status,
                                  observed_at=datetime.now(timezone.utc).isoformat(), headers_retained=False)
                    # Save status even if reading the response body later fails.
                    save(directory/'response.json', record)
                    try:
                        raw = response.read()
                    except Exception as exc:
                        partial = getattr(exc, 'partial', None)
                        if isinstance(partial, bytes):
                            put(directory/'partial-body.bin', partial)
                            save(directory/'partial.json',dict(sha256=hashlib.sha256(partial).hexdigest(),complete=False))
                        raise
                    put(directory/'body.bin',raw)
                    save(directory/'body.json',dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),complete=True))
                    replacement = urllib.response.addinfourl(io.BytesIO(raw),response.headers,response.geturl(),status)
                    replacement.msg = getattr(response,'msg','')
                    response.close()
                except OSError as exc:
                    raise EvidenceError('response evidence persistence/read failed') from exc
                return super().http_response(request,replacement)
            https_response = http_response

        class Redirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(handler, request, response, code, msg, headers, newurl):
                try:
                    public_url(newurl)
                except ValueError as exc:
                    raise EvidenceError('credential-bearing redirect rejected') from exc
                return super().redirect_request(request,response,code,msg,headers,newurl)

        try:
            # No cookies or authentication handlers. Capture runs before HTTP
            # status handling, including every redirect and every retry body.
            response = urllib.request.build_opener(Capture(),Redirect()).open(req,timeout=TIMEOUT)
            try:
                save(attempt/'complete.json',dict(ended_at=datetime.now(timezone.utc).isoformat(),
                     status=response.code,response_count=counter,transport_success=True))
            except OSError as exc:
                response.close()
                raise EvidenceError('cannot retain acquisition completion') from exc
            return response
        except Exception as exc:
            try:
                save(attempt/'error.json',dict(ended_at=datetime.now(timezone.utc).isoformat(),
                     error_type=type(exc).__name__,status=getattr(exc,'code',None),response_count=counter,
                     transport_success=False,error_detail='Exception text omitted to avoid reflected credentials'))
            except OSError as failure:
                raise EvidenceError('cannot retain acquisition error') from failure
            raise


def open_request(req):
    return EVIDENCE.open(req) if EVIDENCE is not None else urllib.request.urlopen(req,timeout=TIMEOUT)


def write_download(path, raw):
    if EVIDENCE is None:
        with open(path,'wb') as stream:
            stream.write(raw)
    else:
        p = absolute(path)
        if not p.is_relative_to(EVIDENCE.root/'derived'):
            raise EvidenceError('derived outputs must stay under evidence-dir/derived')
        try:
            put(p,raw)
        except OSError as exc:
            raise EvidenceError('derived output must be new and durable') from exc


def fetch(url, binary=False, retries=2, backoff=4.0):
    """GET with UA, timeout, and retry/backoff for 429/5xx."""
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with open_request(req) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
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


def fetch_quiet(url, **kw):
    try:
        return fetch(url, **kw)
    except EvidenceError:
        raise
    except Exception:
        return None


# ---------------------------------------------------------------- PMC XML

def pmc_xml_to_text(xml_str):
    """PMC JATS XML -> structured markdown-ish text. Returns '' if no <body>."""
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return ""
    body = root.find(".//body")
    if body is None:
        return ""
    out = []

    def text_of(el):
        return " ".join("".join(el.itertext()).split())

    def walk(el, depth=2):
        for child in el:
            tag = child.tag.split("}")[-1]
            if tag == "sec":
                title = child.find("title")
                if title is not None:
                    out.append("#" * min(depth, 6) + " " + text_of(title))
                walk(child, depth + 1)
            elif tag == "p":
                t = text_of(child)
                if t:
                    out.append(t)
            elif tag == "preformat":
                # Older PMC XML (pre-~2000) wraps full body text in
                # <preformat preformat-type="pmc-pdf-text"> instead of
                # <sec>/<p> structure. Extract the raw text directly.
                t = (child.text or "").strip()
                if t:
                    out.append(t)
            elif tag == "fig":
                cap = child.find("caption")
                label = child.find("label")
                if cap is not None:
                    lab = text_of(label) if label is not None else "Figure"
                    out.append("[%s] %s" % (lab, text_of(cap)))
            elif tag in ("table-wrap",):
                cap = child.find("caption")
                label = child.find("label")
                if cap is not None:
                    lab = text_of(label) if label is not None else "Table"
                    out.append("[%s] %s" % (lab, text_of(cap)))
            elif tag in ("title", "xref", "label"):
                continue
            else:
                walk(child, depth)

    walk(body)
    return "\n\n".join(out)


# ---------------------------------------------------------------- ladder steps

def epmc_gate(pmid=None, doi=None):
    """Branch 0: Europe PMC REST OA flags. Returns dict or {}."""
    if pmid:
        q = "EXT_ID:%s" % pmid
    elif doi:
        q = 'DOI:"%s"' % doi
    else:
        return {}
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%s"
           "&resultType=core&format=json" % urllib.parse.quote(q))
    raw = fetch_quiet(url)
    if not raw:
        return {}
    try:
        res = json.loads(raw).get("resultList", {}).get("result", [])
        return res[0] if res else {}
    except json.JSONDecodeError:
        return {}


def try_pmc_xml(pmcid):
    """Branch 1: PMC E-utilities full-text XML."""
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
           "?db=pmc&id=%s&rettype=xml" % pmcid)
    xml = fetch_quiet(url)
    if not xml:
        return None
    text = pmc_xml_to_text(xml)
    return text if len(text) > 2000 else None


def try_epmc_pdf(pmcid, out_prefix):
    """Branch 1b: Europe PMC PDF render endpoint (works for embargoed inPMC:Y)."""
    url = "https://europepmc.org/api/getPdf?pmcid=%s" % pmcid
    data = fetch_quiet(url, binary=True)
    if not data or len(data) < 10000 or not data.startswith(b"%PDF"):
        return None
    pdf_path = out_prefix + ".pdf"
    write_download(pdf_path, data)
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        text = "\n\n".join(str(page.get_text()) for page in doc)
    except ImportError:
        return {"text": None, "pdf_path": pdf_path}
    if len(text) < 2000:
        return None
    return {"text": text, "pdf_path": pdf_path}


def biorxiv_latest_version(doi):
    """Step 0 for preprints: api.biorxiv.org (not Cloudflare-blocked)."""
    url = "https://api.biorxiv.org/details/biorxiv/%s" % doi
    raw = fetch_quiet(url)
    if not raw:
        return None
    try:
        coll = json.loads(raw).get("collection", [])
        if not coll:
            return None
        versions = [int(c.get("version", 1)) for c in coll]
        return max(versions)
    except (json.JSONDecodeError, ValueError):
        return None


def try_jina(target_url):
    """Branch 1d: r.jina.ai reader proxy. Defeats Cloudflare bot-detection."""
    url = "https://r.jina.ai/%s" % target_url
    text = fetch_quiet(url, retries=1, backoff=6.0)
    if not text or len(text) < 3000:
        return None
    head = text[:500].lower()
    if "too many requests" in head or "captcha" in head:
        return None
    return text


def resolve_doi(doi):
    """Follow doi.org redirect to the publisher URL (HEAD-ish GET)."""
    url = "https://doi.org/%s" % doi
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA},
                                     method="HEAD")
        with open_request(req) as r:
            return r.geturl()
    except EvidenceError:
        raise
    except Exception:
        return None


def strip_html(html):
    """Crude HTML->text for Wayback snapshots: drop script/style, keep blocks."""
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    # Block-level breaks
    html = re.sub(r"(?i)</(p|div|section|article|h[1-6]|li|tr)>", "\n\n", html)
    html = re.sub(r"(?i)<br[^>]*>", "\n", html)
    text = re.sub(r"<[^>]+>", "", html)
    import html as html_mod
    text = html_mod.unescape(text)
    lines = [" ".join(l.split()) for l in text.splitlines()]
    return "\n\n".join(l for l in lines if l)


def try_wayback(target_url):
    """Branch 2b: Wayback Machine snapshot of the article page."""
    api = ("https://archive.org/wayback/available?url=%s"
           % urllib.parse.quote(target_url, safe=""))
    raw = fetch_quiet(api, retries=3, backoff=5.0)
    snap_url = None
    if raw:
        try:
            snap_url = (json.loads(raw).get("archived_snapshots", {})
                        .get("closest", {}).get("url"))
        except json.JSONDecodeError:
            snap_url = None
    if not snap_url:
        # Guess the redirect form (nearest snapshot)
        snap_url = "https://web.archive.org/web/2/%s" % target_url
    html = fetch_quiet(snap_url, retries=1)
    if not html:
        return None
    text = strip_html(html)
    return text if len(text) > 5000 else None


# ---------------------------------------------------------------- figures

def fetch_pmc_figures(pmcid, out_prefix):
    """--figures: scrape the PMC article page for CDN figure URLs and download.

    Why not oa.fcgi: NCBI's bulk-package host (oa_package tar.gz over
    ftp/https) refuses this host (404/550 verified 2026-08-05 for two OA
    packages). The PMC article HTML page itself is reachable and embeds
    cdn.ncbi.nlm.nih.gov/pmc/blobs/... URLs for every figure image — and
    this works for free-in-PMC articles, not just the OA subset.
    """
    page = fetch_quiet("https://pmc.ncbi.nlm.nih.gov/articles/%s/" % pmcid)
    if not page:
        return None
    urls = sorted(set(re.findall(
        r"https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^\"'\s]+?\.(?:jpe?g|png|gif)",
        page)))
    if not urls:
        return None
    figdir = out_prefix + "_figures"
    os.makedirs(figdir, exist_ok=True)
    n = 0
    for u in urls:
        data = fetch_quiet(u, binary=True, retries=1)
        if not data or len(data) < 1000:
            continue
        name = os.path.basename(urllib.parse.urlparse(u).path)
        write_download(os.path.join(figdir, name), data)
        n += 1
    return figdir if n else None



# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pmid")
    ap.add_argument("--doi")
    ap.add_argument("--pmcid")
    ap.add_argument("--publisher-url",
                    help="Publisher article URL (skips doi.org resolution)")
    ap.add_argument("--out", required=True,
                    help="Output prefix; text goes to <out>.txt")
    ap.add_argument("--figures", action="store_true",
                    help="Also fetch PMC OA figure bundle (needs pmcid)")
    ap.add_argument("--skip-publisher", action="store_true",
                    help="Stop before branch 2 (never touch the publisher page)")
    ap.add_argument('--evidence-dir', help='NEW absolute acquisition evidence directory; --out must be below its derived/ directory')
    args = ap.parse_args()
    global EVIDENCE
    EVIDENCE = None
    if args.evidence_dir:
        directory = absolute(args.evidence_dir)
        prefix = absolute(args.out)
        if not prefix.is_relative_to(directory/'derived'):
            ap.error('--out must be an absolute prefix below --evidence-dir/derived')
        EVIDENCE = AcquisitionEvidence(directory)
    notes = []
    result = {"provenance": "none", "chars": 0,
              "text_file": None, "figures_dir": None, "notes": notes}

    def succeed(provenance, text):
        path = args.out + ".txt"
        if EVIDENCE is None:
            with open(path, "w") as f:
                f.write(text)
        else:
            write_download(path,text.encode('utf-8'))
        result.update(provenance=provenance, chars=len(text), text_file=path)
        return True

    # ---- branch 0: Europe PMC gate
    gate = epmc_gate(pmid=args.pmid, doi=args.doi)
    pmcid = args.pmcid or gate.get("pmcid")
    if pmcid:
        pmcid = pmcid if str(pmcid).startswith("PMC") else "PMC%s" % pmcid
    if gate:
        notes.append("epmc gate: inPMC=%s isOpenAccess=%s hasPDF=%s pmcid=%s"
                     % (gate.get("inPMC"), gate.get("isOpenAccess"),
                        gate.get("hasPDF"), pmcid))

    # ---- branch 1: PMC XML
    if pmcid:
        text = try_pmc_xml(pmcid)
        if text:
            succeed("pmc-xml", text)
        else:
            notes.append("pmc-xml: no <body> (metadata-only or blocked)")

    # ---- branch 1b: Europe PMC PDF render
    if result["provenance"] == "none" and pmcid and gate.get("inPMC") == "Y":
        r = try_epmc_pdf(pmcid, args.out)
        if r and r.get("text"):
            succeed("epmc-pdf", r["text"])
        elif r:
            notes.append("epmc-pdf: PDF saved to %s but pymupdf missing — extract manually"
                         % r["pdf_path"])
        else:
            notes.append("epmc-pdf: no PDF returned")

    # ---- branch 1c/1d: bioRxiv preprint via version check + jina
    is_biorxiv = bool(args.doi and args.doi.startswith("10.1101/"))
    if result["provenance"] == "none" and is_biorxiv:
        ver = biorxiv_latest_version(args.doi)
        if ver:
            notes.append("biorxiv api: latest version v%s" % ver)
            target = "https://www.biorxiv.org/content/%sv%s.full" % (args.doi, ver)
        else:
            notes.append("biorxiv api: version lookup failed; trying v1")
            target = "https://www.biorxiv.org/content/%sv1.full" % args.doi
        text = try_jina(target)
        if text:
            succeed("biorxiv-jina", text)
        else:
            notes.append("biorxiv-jina: jina missed; wayback attempted below")
            text = try_wayback(target)
            if text:
                succeed("wayback", text)
            else:
                notes.append("wayback: no usable snapshot of %s" % target)

    # ---- branch 2: publisher page via jina
    if result["provenance"] == "none" and not args.skip_publisher and not is_biorxiv:
        pub_url = args.publisher_url
        if not pub_url and args.doi:
            pub_url = resolve_doi(args.doi)
            if pub_url:
                notes.append("doi.org resolved to %s" % pub_url)
        if pub_url:
            text = try_jina(pub_url)
            if text:
                succeed("publisher-jina", text)
            else:
                notes.append("publisher-jina: jina missed or paywalled")
                # ---- branch 2b: wayback of publisher page
                text = try_wayback(pub_url)
                if text:
                    succeed("wayback", text)
                else:
                    notes.append("wayback: no usable snapshot of %s" % pub_url)

    # ---- figures (optional)
    if args.figures and pmcid:
        figdir = fetch_pmc_figures(pmcid, args.out)
        if figdir:
            result["figures_dir"] = figdir
            notes.append("figures: extracted to %s" % figdir)
        else:
            notes.append("figures: none found on PMC page for %s" % pmcid)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    sys.exit(main())
