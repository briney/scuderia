# Worked example: source stream versus content kind

Load when adding a communication source or considering a kind rename.
A new transport does not itself authorize a new content domain, page kind or
scheduled ingestion campaign.

## Separate source, content and identity

Email is a source stream. Apply the same research-program scope and notability
rules as other inputs; account-level restrictions are deployment prerequisites,
not assumptions about every installation. A notable discussion may warrant an
`interaction` page with `channel: email`; routine facts or commitments may
update an existing person/project/grant or an authorized task instead.

A kind called `meeting` can be too narrow if it already covers talks and will
also hold correspondence. `interaction` expresses the shared event identity;
`participants` works across channels better than `attendees`. Preserve existing
identity/edges and repair live consumers when a rename is approved. Do not
backfill unknown historical channels from guesses.

## Keep archival identity separate

The raw-source archive is immutable and content-addressed. Email threads grow,
so archive each message independently and assemble thread context at read time.
`raw-source-archive.md` owns retention and pointer details; `email-ingest` owns
adapter behavior, completeness, triage and watermark handling.

Archive prefixes identify source streams, not current graph kinds. Existing
`meetings/` objects need not move when graph pages become `interactions/`;
retain their recorded keys. Historical design records may keep old names;
repair operative skills, templates, schema and other current consumers.

The author ledger illustrates separation of an identity record from a curated
person page. It does not authorize an email contacts ledger or new promotion
thresholds. Use the actual email-ingestion contract; any new ledger or rollout
requires its own approved design. Follow the parent skill's pilot and validation
procedure rather than treating an old build-out plan as current work.
