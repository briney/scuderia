---
name: arxiv-retrieval
description: arXiv paper retrieval — API, HTML fallback, and metadata field mapping. Loaded by paper-ingest.
---

# arXiv retrieval — API, HTML, and fallback paths

The arXiv API endpoint (`export.arxiv.org/api/query?id_list=<id>`) is the
canonical way to resolve an arXiv preprint's metadata (title, authors, DOI,
submission date, subjects). But it is slow and sometimes times out (observed
60s+ timeouts on both `http://` and `https://` in July 2026). When it fails,
fall back to browsing the arXiv website directly.

## Resolution path

### 1. Try the API first (preferred)

```bash
curl -sL "https://export.arxiv.org/api/query?id_list=2510.01329,2601.15165" \
  -H "User-Agent: <your-tool>/1.0 (mailto:you@example.com)"
```

Returns Atom XML with `<entry>` elements containing `<title>`, `<author>`,
`<arxiv:doi>`, `<published>`, `<summary>`. Multi-ID queries return entries
in **reverse order** of the input list.

**Timeout:** If the API doesn't respond in ~30s, abandon it and go to step 2.
Don't retry the API with a longer timeout — it's a server-side issue, not a
network issue.

### 2. Browse the abstract page (fallback for metadata)

```
https://arxiv.org/abs/<arxiv_id>
```

The abstract page carries: title, authors (as links), abstract (blockquote),
submission history (version dates + sizes), DOI link, subjects, and access
links (PDF, HTML, TeX Source). All extractable from the browser snapshot.

Use `browser_navigate` to load the page, then read the snapshot. The DOI is
in the "Cite as" table row as `https://doi.org/10.48550/arXiv.<id>`.

### 3. Browse the HTML version (fallback for full text)

```
https://arxiv.org/html/<arxiv_id>
```

arXiv renders an experimental HTML version of most recent submissions. Load
it with `browser_navigate`, then extract the article text with:

```javascript
// browser_console expression
(() => {
  const article = document.querySelector('article') || document.body;
  return article.innerText.substring(0, 50000);
})()
```

This returns the full paper text (abstract through references) as plain text.
The HTML version may have conversion warnings (some LaTeX packages not
supported), but the core text is always present. Math renders as Unicode or
MathML which `innerText` captures as readable approximations.

**For distillation:** The HTML text is sufficient for Phase 4 (distill against
structure). You get the abstract, introduction, methods, results, and
references. Figures are not extracted as images via this path — use
`browser_vision` or `browser_get_images` if figure content is load-bearing.

### 4. PDF download (when HTML is unavailable)

If the HTML version doesn't exist (older papers), download the PDF:

```bash
curl -sL "https://arxiv.org/pdf/<arxiv_id>" -o /tmp/paper.pdf
```

Then extract text with `pdftotext` or `pymupdf`. This is the slowest path
and should only be used when steps 1-3 all fail.

## Metadata field mapping

| Field | API (Atom XML) | Abstract page (browser) |
|-------|----------------|--------------------------|
| `doi` | `<arxiv:doi>` | `https://doi.org/10.48550/arXiv.<id>` link |
| `arxiv` | the `<id>` field | the URL path segment |
| `title` | `<title>` | `<h1>` heading |
| `authors` | `<author><name>` elements | author links in byline |
| `year` | `<published>` date | "[Submitted on DD Mon YYYY]" text |
| `venue` | always `arXiv` | always `arXiv` |
| `status` | always `preprint` | always `preprint` |
| `abstract` | `<summary>` | `<blockquote>` element |

## Key notes

- arXiv preprints all have DOIs of the form `10.48550/arXiv.<arxiv_id>`. This
  is the primary identifier — always populate the `doi` field.
- Version info: the abstract page shows submission history (v1, v2, ...).
  Use the latest version's date for `year`. The arXiv ID stays the same across
  versions.
- The HTML version may use a different template depending on the paper's
  LaTeX class file. Some templates produce conversion warnings but the text
  content is always extracted.
- Multi-ID API queries return entries in **reverse order** of the input list.
  If you query `id_list=A,B`, you get B first, then A.
