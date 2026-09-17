# Verify a task brief against the source

Load when the brief's venue, vocabulary, findings, or sibling-page attribution
disagrees with retrieved evidence. Identity can be correct while the narrative
is wrong. The main skill requires the check for every distillation; this
reference supplies the disagreement procedure, not a second approval gate.

1. Compare the brief's claim to the relevant source passage/figure/table.
   A venue-only mismatch does not by itself identify a different paper:
   check the article's metadata and record the corrected venue.
2. Search unfamiliar terms in the full source, including synonyms and
   abbreviations. Zero literal matches can mean alternate vocabulary or
   incomplete extraction. Read the passage before declaring a contradiction.
3. If the concept is in this paper under another name, use the source's
   terminology and explain the mapping. If it belongs to another paper,
   name the source-supported conflation. A targeted literature search can
   help locate that source, but zero search results do not establish that
   a term never exists in the field. Record unsupported framing as such.
4. Write the actual paper's findings and explicitly flag the brief discrepancy
   for the parent/human. Do not silently edit the parent's working document
   or turn the brief's narrative into a source claim.
5. When a brief names sibling pages, search them for the current paper's
   identifiers. A different author/title attached to the same DOI/PMCID is
   an attribution problem to investigate. Record the exact source and sibling
   location for citation-fixer/entity-resolution; page-only workers do not
   repair other pages themselves.

A prior source check (2026-09-04) found correct paper identifiers paired with
a wrong journal name, imported epitope terminology, and an inconsistent
sibling citation. The reusable checks above address those independent failure
classes without making the private brief or corpus pages required reading.

For quantities repeated differently across source sections, report the
experiment's value with the conflicting restatement and locations. Never
average them or silently correct the paper. Erratum-driven reassignment and
satellite-vault identity handling remain in `paper-ingest-vault-modes`;
XML/caption/resource-table extraction mechanics belong to `pmc-xml-tools`.
