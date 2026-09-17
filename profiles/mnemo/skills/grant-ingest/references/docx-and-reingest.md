# DOCX extraction and archived-source recovery

Load for DOCX inputs or an authorized re-ingest from archived originals.
The parent skill retains the format-independent fidelity and completion gates.

## DOCX prose, captions and bibliography

A `python-docx` top-level paragraph walk can miss floating textbox captions,
tables and note parts. Inspect the original OOXML rather than treating a
successful paragraph extraction as the complete document:

- Walk `word/document.xml` body paragraphs/tables and `w:txbxContent` text
  (`w:t`; namespace `http://schemas.openxmlformats.org/wordprocessingml/2006/main`).
  Keep paragraph boundaries and source ordering. Check tracked changes and
  alternate representations rather than silently choosing source wording.
- Deduplicate captions only when they are verified identical representations
  of one `mc:AlternateContent` Choice/Fallback object. Do not collapse arbitrary
  repeated text. Preserve each caption verbatim after the first body paragraph
  referring to its figure, using `[Figure N — image omitted; original in R2]`
  plus the caption. If placement is unresolved, retain its source locator and
  flag placement rather than dropping the caption or guessing a figure.
- Inspect `word/endnotes.xml`, `word/footnotes.xml` and the actual body for
  references. A `_with-refs.docx` filename is not evidence of a bibliography.
  Nonempty notes and a numbered tail (`^\d{1,3}\.\s+[A-Z]`) are candidate
  signals only; empty notes or failure of that pattern do not establish absence.

If no recoverable bibliography is present, request the missing source. When
supplied, archive it with `role: bibliography`, append its `sources:` pointer,
and record the actual date/reason for the later addition. Never reconstruct
citation entries from numbered prose plus inferred Crossref/PubMed matches.
Only source-backed entries seed paper identity resolution.

## Re-ingest from R2 (any source format)

Read the existing page and fetch each exact `sources[].r2_key` to a uniquely
named scratch file, not a destination directory:

```text
rclone copyto <instance>-r2:<instance>-drops/<r2_key> /tmp/<workdir>/<exact-filename> --timeout 120s --contimeout 10s
```

Verify the retrieved bytes against the recorded source hash and use the parser
appropriate to that format. If the expected remote is absent, check the HOME/
`RCLONE_CONFIG` binding per `raw-source-archive.md`; do not infer a new credential
or remote. Keep recovered originals and prior Verbatim until the replacement
passes source-to-page checks. The page's distilled Review is never substituted
for an original summary statement. Archive/read-back must precede source cleanup.
