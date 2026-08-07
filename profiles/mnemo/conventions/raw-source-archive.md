# Convention: the raw-source archive and git pointers

The markdown brain is a *distillation*. Behind it sits the primary-source
material it was derived from — papers as PDFs, past grants and reviewer critiques
as PDF or DOCX, other documents. These are ground truth and must never be lost.
Authoritative source: `docs/north-star/DESIGN.md` §8.

> **Capability.** Skills name `raw-source-archive-upload`; this convention
> documents the contract that capability satisfies. The Hermes binding is
> `rclone copyto` to Cloudflare R2, documented in §"Upload mechanism" below
> and in [`docs/harnesses/hermes.md`](../../docs/harnesses/hermes.md). Under
> other harnesses, the binding is whatever that harness provides — see
> `conventions/capabilities.md` and the per-harness adapter.

## Where sources live

Every raw source goes to an **S3-compatible object store (Cloudflare R2)**,
**write-once and content-addressed**, with no file-size limits. Nothing binary
enters git — binaries bloat every clone and every Syncthing transfer, and the
portability the markdown corpus protects is a *markdown* property.

Raw email is archived the same way — not because it is binary but because it
is *correspondence*: it does not belong in a git-pushed repository, and the
archive exists so the brain can be re-derived. See "Email sources" below.

The archive is immutable so the brain can be re-derived — re-chunked, re-embedded,
re-summarised — whenever models improve. A distillation is only as safe as the
source it can fall back to.

## The git pointer

What git keeps is a lightweight **pointer per archived source** — enough to record
that the source existed and how to fetch it. The pointer schema:

| Field | Meaning |
|---|---|
| `hash` | Content hash of the original file (the content-addressed key) |
| `r2_key` | The storage key / path in the R2 bucket |
| `filename` | The original filename, as dropped |
| `ingested` | Date the source was ingested (`YYYY-MM-DD`) |
| `provenance` | Where it came from — a short free-text note |

The pointer is carried in the frontmatter of the brain page(s) distilled from
that source, as a `sources:` list:

```yaml
sources:
  - hash: sha256-1a2b3c…
    r2_key: papers/1a2b3c….pdf
    filename: "Smith-2025-antibody-lm-scaling.pdf"
    ingested: 2026-05-18
    provenance: "dropped via _drop/, 2026-05-18"
```

A source distilled into several pages is referenced from each; the pointer is
small by design. The pointer is committed; the binary it points to is not.

## Multi-document sources

The inverse case also happens: one brain page distilled from *several* source
documents. A grant is the standard example — a single `grant` page is distilled
from a whole application package (Specific Aims, Research Strategy, budget,
summary statement, and the rest). Here the page carries **one `sources:` entry
per document**, and each entry adds an optional `role:` field naming what that
document is:

```yaml
sources:
  - role: research-strategy
    hash: sha256-…
    r2_key: grants/….pdf
    filename: "R01-draft-research-strategy.docx"
    ingested: 2026-05-18
    provenance: "ingested grant package, 2026-05-18"
  - role: summary-statement
    hash: sha256-…
    r2_key: grants/….pdf
    filename: "R01-summary-statement.pdf"
    ingested: 2026-05-18
    provenance: "ingested grant package, 2026-05-18"
```

`role:` is free text — the document kinds vary across funders and need no fixed
vocabulary. The skill that ingests the package owns its role values.

## How sources get in

See `_drop/README.md`: a file dropped into `_drop/` is carried to the host by
Syncthing, ingested (text extracted, brain pages filed with citations), uploaded
to R2, recorded with a pointer, and then cleared from `_drop/`. Non-markdown
formats are *sources*, never brain pages — the original stays in the archive and
only its distillation is committed.

## Upload mechanism — rclone

The host wires R2 access through **`rclone`**. The remote is configured once at
host setup (credentials live in `~/.config/rclone/rclone.conf`, never in git or
`.env`); every ingestion skill shells out to `rclone` and never touches an SDK
or raw S3 client.

**Host-specific values** (set at host setup; rebind here if the host changes):

| Setting | Value |
|---|---|
| rclone remote name | `<instance>-r2` (configured per instance) |
| bucket | `<instance>-drops` (configured per instance) |
| key prefix per source stream | `papers/`, `grants/`, `media/`, `meetings/`, `email/` (decided by the ingest skill). Prefixes name the **source stream**, not the page kind — `meetings/` holds Granola transcripts and predates the `meeting` → `interaction` rename (2026-08-01); existing objects are not migrated |

### The four operations every ingest skill needs

```bash
# 1. Hash the source — sha256 is the content-addressed key.
HASH=$(shasum -a 256 "<source-path>" | cut -d' ' -f1)

# 2. Decide the key. Prefix by kind; extension preserved from the source.
EXT="${SOURCE##*.}"           # pdf | docx | mp3 | …
KEY="grants/${HASH}.${EXT}"   # or papers/, media/, etc.

# 3. Upload. `rclone copyto` writes to an exact destination key —
#    use copyto, NOT copy, when you control the key.
#    --timeout / --contimeout are mandatory: rclone otherwise blocks
#    indefinitely on a stalled connection with no useful output.
rclone copyto "<source-path>" "<instance>-r2:<instance>-drops/${KEY}" \
  --timeout 120s --contimeout 10s

# 4. Verify round-trip before deleting the source from _drop/.
rclone lsf "<instance>-r2:<instance>-drops/${KEY}" --timeout 30s >/dev/null
# Non-zero exit means the upload didn't land — do NOT clear _drop/.
```

**Always pass `--timeout` and `--contimeout` on every `rclone` call** — copyto,
lsf, cat, delete. Without them, a network stall hangs the process with no
output until the agent-level command timeout kills it, and you can't tell
upload failure from connectivity failure. 120s for transfers, 30s for
metadata operations, 10s connect is a sane default.

`HASH` and `KEY` then go into the brain-page frontmatter as the `hash` and
`r2_key` fields of the corresponding `sources:` entry.

### Pitfalls

- **The token is object-scoped, not bucket-scoped.** `rclone lsd <instance>-r2:`
  returns HTTP 403 (it tries `ListBuckets`, which the token doesn't grant). That
  is normal and not a sign of broken credentials. Test connectivity with a
  round-trip into a specific key (`rclone copyto … && rclone cat … && rclone
  delete …`) — never with `lsd` at the bucket root.
- **Never `rm` from `_drop/` until `rclone lsf` confirms the key landed.** A
  silent upload failure plus a confident `rm` is how raw sources go missing.
- **Don't write the rclone config to `.env`.** rclone reads
  `~/.config/rclone/rclone.conf` directly; that file is the credential store,
  not Hermes's. Rotation is documented in the profile's `INTEGRATION.md`.
- **Watch the agent's `HOME`.** On some hosts the agent process runs with a
  shimmed `HOME` (e.g. `~/.hermes/profiles/<profile>/home/`) and `rclone` will
  fail to find the config — `rclone listremotes` returns empty and every call
  silently uses defaults. If that happens, export
  `RCLONE_CONFIG=/Users/<user>/.config/rclone/rclone.conf` (or the host's real
  path) once at the top of the shell session and every subsequent call will
  pick up the remote. Don't rely on `HOME` resolution.

## Email sources

Raw email (Bryan's work account only — personal accounts are excluded at the
CLI) is archived **one object per message**: threads grow, and the archive is
write-once, so a thread is assembled at distill time, never stored as a
mutable whole. Key shape: `email/<sha256>.<ext>`, hashed from the raw message
exactly as exported by the source adapter.

**Archive everything the account returns; triage happens at distillation,
never at pull time.** Storage is cheap; a pull-time filter that eats a real
message is unrecoverable.

The pointer convention is unchanged: each brain page distilled from a message
carries a `sources:` entry for it (`hash`, `r2_key`, `filename`, `ingested`,
`provenance`). Messages that produce no pages (newsletters, notifications,
admin churn) simply have no pointers — the archive keeps them regardless.
