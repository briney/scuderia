# example-instance

The minimal valid mnemo instance, per the instance contract (soma spec §5):

1. `instance.yaml` parses: `{name, profile, profile_version, schema_version,
   created}`.
2. Every page directory the profile's `schema.yaml` declares exists (may be
   empty — hence the `.gitkeep` files).
3. `skills/` exists (may be empty) — instance-private skills live here and
   override template skills by name.
4. Every version pin is satisfiable by the bound soma checkout.

`soma init --profile mnemo --name <name> --path <dir>` scaffolds exactly this
tree, templating `{{INSTANCE_NAME}}` and `{{CREATED}}` in `instance.yaml` and
copying the character templates (`SOUL.md`, `STYLE.md`, `USER/` (the user model)) from the
profile root with the instance name substituted.

What is deliberately NOT here: page content, program state (`RESEARCH.md`),
and the user model's contents — those are the instance's own life, not the
template's business.
