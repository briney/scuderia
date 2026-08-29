# oiko — the lab-manager profile (STUB)

*oikos*: household — the root of both *economics* and *ecology*. Budgets and
compliance.

oiko is the second scuderia profile: a brain for running a lab rather than running
a research program. Biosafety and IRB/IACUC protocols, budgets and spending,
personnel and equipment — a page-kind set that shares almost nothing with
mnemo's, which is exactly why scuderia is profile-pluggable rather than
scope-extended.

**This is a stub by design** (scuderia spec §12): a real template is built only
when someone is ready to run an oiko instance — half-real templates rot. When
that day comes, an oiko profile needs the same five things mnemo ships:

1. `schema.yaml` + `conventions/` — oiko's page kinds (protocol? budget?
   order?) and their frontmatter contract.
2. `skills/` — the oiko job set (procurement tracking, compliance calendars,
   budget cards for the feed).
3. `SOUL.md` / `STYLE.md` / `USER/` templates — the lab-manager character is
   a different voice from the research thought partner.
4. `manifest.yaml` + `example-instance/` — the install contract.
5. Card types for the feed (budget/protocol cards), declared in the schema.

The platform machinery (capability contract, linter, CLI, feed renderer) is
already profile-agnostic; nothing in `core/` needs to change for oiko to
exist.
