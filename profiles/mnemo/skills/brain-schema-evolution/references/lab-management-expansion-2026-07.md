# Worked example: research capability versus lab operations

Load for a proposal to represent lab membership, expertise or project state.
This is a schema-decision example, not permission to expand an instance's scope
or populate its pages. Private organization and rollout records stay private.

## Decompose the request

Research capability can inform grant personnel, facilities, progress reports
and scientific planning. Ordering, equipment logistics and managing meeting
cadence are different work. If the current instance excludes the requested
content, obtain an explicit scope revision before changing its schema.

## Extend identity and relationships

- A lab member, author and eventual alumnus can be the same person. Keep one
  `person` identity; membership or alumni status does not justify a new kind.
- Distinguish institutional affiliation from lab membership with the current
  `affiliation` and `member_of` fields. `lab_status`, `expertise`, `pillar`
  and `pillar_role` describe supported relationships/capabilities; the actual
  org model and assignments are instance decisions, not template defaults.
- Use `works_on` for person-to-project edges. Project personnel, funding and
  milestones belong on the project when they do not need independent identity
  and inbound links. A milestone with only one parent is not a new graph hub.
- A lab institution page can describe its research capabilities. Preserve
  former members' pages and historical edges; do not delete them on departure.

Consult current `frontmatter.md`, `page-kinds.md` and the schema for field
shapes. Do not infer that an optional field is populated or maintained merely
because the schema permits it. An authorized change follows the parent skill's
coordinated schema/convention/template/linter update and reviewed pilot;
this reference owns no separate migration or project-state schedule.
