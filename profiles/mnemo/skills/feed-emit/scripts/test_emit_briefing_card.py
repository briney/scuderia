#!/usr/bin/env python3
"""Isolated tests for the feed-emit briefing producer and its wrapper.

Covers the 2026-09-16 committed-content-only migration:

  * the emitter reads BRIEFING.md / instance.yaml / brain.yaml from the
    resolved HEAD commit (git ls-tree + cat-file), never from the worktree:
    dirty, staged and untracked content is invisible to the feed;
  * a path absent from the committed tree withdraws the old card; an
    uncommitted deletion does NOT;
  * any Git failure (unborn repo, corrupt objects, not-a-repo) preserves the
    existing card and exits nonzero so the wrapper skips sync;
  * committed symlink blobs are rejected, paths cannot escape the repo;
  * no Git index/HEAD/worktree mutation happens (content-hash snapshots);
  * dismissal semantics, card schema, body truncation and date behavior are
    preserved from the pre-migration emitter;
  * feed_sync.sh (run as an isolated COPY in a sandbox with a stub syncer)
    returns nonzero on emitter/syncer failure, skips sync after an emitter
    failure, fails loudly on missing credentials, and prints nothing on a
    clean no-change sync.

Isolation: every test builds throwaway Git repos under tempfile.mkdtemp().
No production vault, profile, credential or network endpoint is read — the
wrapper copy runs with PROFILE_DIR / VAULT / SCUDERIA / LOG pointed into the
sandbox, and the stub syncer only writes a marker file. The only production
bytes touched are the two scripts under test themselves.

RED/GREEN: set FEED_EMIT_TEST_TARGET to a pre-migration copy of the emitter
(e.g. the .pre-edit backup in the migration cache) and run only the
EmitterTests class — the committed-content tests fail (RED). Run the suite
unmodified for GREEN.
"""

import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
EMITTER = pathlib.Path(os.environ.get(
    "FEED_EMIT_TEST_TARGET", str(HERE / "emit_briefing_card.py")))
# The wrapper lives outside scuderia (host profile); tests run an isolated
# COPY of it with every path overridden into a sandbox. Skipped when absent.
WRAPPER = pathlib.Path(os.environ.get("FEED_SYNC_TEST_TARGET", ""))

BRIEFING_V1 = "# Brief\n\n- item one\n- item two\n"
BRIEFING_V2 = "# Brief\n\n- item one CHANGED\n- item three\n"

STUB_SYNC = '''#!/usr/bin/env python3
# Test double for scuderia interface/syncer/sync.py — no network, no D1.
import json
import os
import sys

marker = os.environ.get("SYNC_MARKER")
if marker:
    with open(marker, "a") as fh:
        fh.write(json.dumps({k: os.environ.get(k) for k in (
            "VAULT_ROOT", "FEED_OUTBOX_DIR", "FEED_STATE_FILE", "FEED_URL")})
            + "\\n")
print(os.environ.get("SYNC_STUB_OUTPUT", ""))
sys.exit(int(os.environ.get("SYNC_STUB_RC", "0")))
'''


class RepoTestCase(unittest.TestCase):
    """Base: throwaway Git repo + emitter runner."""

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="feedemit-"))
        self.addCleanup(shutil.rmtree, str(self.root), True)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.vault = self.repo
        self.outbox = self.root / "outbox"
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    # -- helpers ----------------------------------------------------------

    def git(self, *args, cwd=None):
        env = self.git_env()
        proc = subprocess.run(
            ["git", "-C", str(cwd or self.repo)] + list(args),
            capture_output=True, text=True, env=env, timeout=120)
        if proc.returncode != 0:
            self.fail(f"git {args} failed: {proc.stderr.strip()}")
        return proc.stdout

    @staticmethod
    def git_env():
        return {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_OPTIONAL_LOCKS": "0",
        }

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, msg="c", *paths):
        if paths:
            self.git("add", "--", *paths)
        else:
            self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", msg)

    def seed_repo(self, brief=BRIEFING_V1, name="testinst"):
        self.write("instance.yaml", f"name: {name}\n")
        if brief is not None:
            self.write("BRIEFING.md", brief)
        self.commit("seed")

    def run_emitter(self, vault=None, env=None, drop_vault_root=False):
        env_ = self.git_env()
        if not drop_vault_root:
            env_["VAULT_ROOT"] = str(vault or self.vault)
        env_["FEED_OUTBOX_DIR"] = str(self.outbox)
        if env:
            env_.update({k: str(v) for k, v in env.items()})
        proc = subprocess.run(
            [sys.executable, str(EMITTER)], env=env_,
            capture_output=True, text=True, timeout=180)
        return proc.returncode, proc.stdout, proc.stderr

    def card_path(self, inst="testinst"):
        return self.outbox / f"{inst}__briefing__daily.json"

    def read_card(self, inst="testinst"):
        return json.loads(self.card_path(inst).read_text())


class EmitterTests(RepoTestCase):
    """Committed-content-only behavior of emit_briefing_card.py."""

    def test_committed_update_reflects_in_card(self):
        self.seed_repo(BRIEFING_V1)
        rc, out, err = self.run_emitter()
        self.assertEqual((rc, err), (0, ""))
        card = self.read_card()
        self.assertEqual(card["body"], BRIEFING_V1.strip())
        self.assertEqual(card["card_id"], "testinst/briefing/daily")
        self.assertEqual(card["instance"], "testinst")
        # a NEW COMMIT of the briefing updates the card
        self.write("BRIEFING.md", BRIEFING_V2)
        self.commit("v2")
        rc, out, err = self.run_emitter()
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(self.read_card()["body"], BRIEFING_V2.strip())

    def test_worktree_dirty_and_staged_content_ignored(self):
        self.seed_repo(BRIEFING_V1)
        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_card()["body"], BRIEFING_V1.strip())
        # dirty (unstaged) worktree edit
        self.write("BRIEFING.md", "DIRTY\n" + BRIEFING_V2)
        rc, _, _ = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_card()["body"], BRIEFING_V1.strip())
        # staged edit
        self.git("add", "BRIEFING.md")
        rc, _, _ = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_card()["body"], BRIEFING_V1.strip())
        # dirty identity metadata is ignored too
        self.write("instance.yaml", "name: worktreename\n")
        rc, _, _ = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_card()["card_id"],
                         "testinst/briefing/daily")

    def test_untracked_briefing_not_emitted(self):
        self.write("instance.yaml", "name: testinst\n")
        self.write("BRIEFING.md", BRIEFING_V2)  # never committed
        self.commit("meta only", "instance.yaml")
        rc, out, err = self.run_emitter()
        self.assertEqual((rc, err), (0, ""))
        self.assertFalse(self.card_path().exists())
        self.assertIn("nothing to emit", out)

    def test_uncommitted_deletion_does_not_withdraw(self):
        self.seed_repo(BRIEFING_V1)
        rc, _, _ = self.run_emitter()
        self.assertTrue(self.card_path().exists())
        (self.repo / "BRIEFING.md").unlink()  # worktree deletion, uncommitted
        rc, out, err = self.run_emitter()
        self.assertEqual((rc, err), (0, ""))
        self.assertNotIn("withdrawn", out)
        self.assertTrue(self.card_path().exists())
        self.assertEqual(self.read_card()["body"], BRIEFING_V1.strip())

    def test_committed_deletion_withdraws_card(self):
        self.seed_repo(BRIEFING_V1)
        rc, _, _ = self.run_emitter()
        self.assertTrue(self.card_path().exists())
        self.git("rm", "-q", "BRIEFING.md")
        self.git("commit", "-q", "-m", "drop briefing")
        rc, out, err = self.run_emitter()
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("card withdrawn", out)
        self.assertFalse(self.card_path().exists())

    def test_dismissed_card_held_back_until_content_changes(self):
        self.seed_repo(BRIEFING_V1)
        self.run_emitter()
        self.assertTrue(self.card_path().exists())
        digest = hashlib.sha256(BRIEFING_V1.encode()).hexdigest()[:16]
        state = self.outbox / ".state"
        state.mkdir(parents=True, exist_ok=True)
        (state / "dismissed.json").write_text(
            json.dumps({"testinst/briefing/daily": digest}))
        rc, out, err = self.run_emitter()
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("held back", out)
        self.assertFalse(self.card_path().exists())
        # content change (committed) → card reappears
        self.write("BRIEFING.md", BRIEFING_V2)
        self.commit("v2")
        rc, out, err = self.run_emitter()
        self.assertEqual((rc, err), (0, ""))
        self.assertTrue(self.card_path().exists())
        self.assertEqual(self.read_card()["body"], BRIEFING_V2.strip())

    def test_git_corruption_preserves_card_and_fails(self):
        self.seed_repo(BRIEFING_V1)
        rc, _, _ = self.run_emitter()
        self.assertEqual(rc, 0)
        card_before = self.card_path().read_bytes()
        shutil.rmtree(self.repo / ".git" / "objects")
        rc, out, err = self.run_emitter()
        self.assertEqual(rc, 3)
        self.assertIn("git read failed", err)
        self.assertEqual(self.card_path().read_bytes(), card_before)

    def test_unborn_repo_fails_and_preserves_card(self):
        # repo with no commits; worktree content must NOT be emitted
        self.write("instance.yaml", "name: testinst\n")
        self.write("BRIEFING.md", BRIEFING_V1)
        self.outbox.mkdir(parents=True, exist_ok=True)
        old_card = self.card_path()
        old_card.write_text('{"card_id": "testinst/briefing/daily"}\n')
        rc, out, err = self.run_emitter()
        self.assertEqual(rc, 3)
        self.assertIn("git read failed", err)
        self.assertEqual(old_card.read_text(),
                         '{"card_id": "testinst/briefing/daily"}\n')

    def test_vault_outside_any_repo_fails(self):
        plain = self.root / "plain"
        plain.mkdir()
        self.outbox.mkdir(parents=True, exist_ok=True)
        old = self.card_path()
        old.write_text("STALE")
        rc, out, err = self.run_emitter(vault=plain)
        self.assertEqual(rc, 3)
        self.assertIn("git read failed", err)
        self.assertEqual(old.read_text(), "STALE")

    def test_missing_vault_root_fails(self):
        rc, out, err = self.run_emitter(vault=self.root / "nope")
        self.assertEqual(rc, 2)
        self.assertIn("VAULT_ROOT", err)

    def test_unset_vault_root_fails(self):
        rc, out, err = self.run_emitter(drop_vault_root=True)
        self.assertEqual(rc, 2)

    def test_committed_symlink_briefing_rejected(self):
        self.write("real.md", BRIEFING_V1)
        os.symlink("real.md", self.repo / "BRIEFING.md")
        self.write("instance.yaml", "name: testinst\n")
        self.commit("symlink")
        rc, out, err = self.run_emitter()
        self.assertEqual(rc, 3)
        self.assertIn("symlink", err)
        self.assertFalse(self.card_path().exists())

    def test_no_git_or_worktree_mutations(self):
        self.seed_repo(BRIEFING_V1)
        self.run_emitter()
        self.write("BRIEFING.md", BRIEFING_V2)  # leave dirty + staged state
        self.git("add", "BRIEFING.md")

        def snap_tree(base, skip_git=False):
            files = {}
            for path in sorted(base.rglob("*")):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(base))
                if skip_git and rel.startswith(".git/"):
                    continue
                files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
            return files

        status_before = self.git("status", "--porcelain")
        head_before = self.git("rev-parse", "HEAD")
        git_before = snap_tree(self.repo / ".git")
        worktree_before = snap_tree(self.repo, skip_git=True)

        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 0)

        self.assertEqual(head_before, self.git("rev-parse", "HEAD"))
        self.assertEqual(status_before, self.git("status", "--porcelain"))
        self.assertEqual(git_before, snap_tree(self.repo / ".git"))
        self.assertEqual(worktree_before, snap_tree(self.repo, skip_git=True))
        # and the emit still came from the COMMITTED content
        self.assertEqual(self.read_card()["body"], BRIEFING_V1.strip())

    def test_card_schema_truncation_and_date(self):
        long_body = ("# header 2026-01-02\n"
                     + "\n".join(f"line {i} " + "x" * 90
                                 for i in range(80)) + "\n")
        self.seed_repo(long_body)
        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 0)
        card = self.read_card()
        self.assertEqual(
            set(card),
            {"card_id", "instance", "profile", "type", "title", "body",
             "salience", "source_ref", "actions", "state"})
        self.assertEqual(card["title"], "daily briefing — 2026-01-02")
        self.assertEqual(card["type"], "summary")
        self.assertEqual(card["profile"], "mnemo")
        self.assertEqual(card["salience"], 0.6)
        self.assertEqual(card["source_ref"], "BRIEFING.md")
        self.assertEqual(card["actions"], ["dismiss"])
        self.assertEqual(card["state"], "active")
        self.assertTrue(card["body"].endswith(
            "*(truncated — full brief in BRIEFING.md)*"))
        self.assertLessEqual(len(card["body"]), 3500 + 100)
        self.assertTrue(card["body"].startswith("# header 2026-01-02"))

    def test_title_date_defaults_to_today(self):
        self.seed_repo("no dates in this brief\n")
        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(
            self.read_card()["title"],
            f"daily briefing — {dt.date.today().isoformat()}")

    def test_no_temp_files_left_in_outbox(self):
        self.seed_repo(BRIEFING_V1)
        rc, _, _ = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(
            sorted(p.name for p in self.outbox.iterdir()),
            ["testinst__briefing__daily.json"])

    def test_identity_sources(self):
        # committed instance.yaml wins by default
        self.seed_repo(BRIEFING_V1, name="instfile")
        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_card("instfile")["instance"], "instfile")
        # FEED_INSTANCE env overrides committed metadata
        rc, _, err = self.run_emitter(env={"FEED_INSTANCE": "ovr"})
        self.assertEqual(rc, 0)
        self.assertTrue(self.card_path("ovr").exists())

    def test_metadata_object_failure_preserves_card_and_identity(self):
        self.seed_repo(BRIEFING_V1)
        self.assertEqual(self.run_emitter()[0], 0)
        before = {p.name: p.read_bytes() for p in self.outbox.iterdir()}
        oid = self.git("rev-parse", "HEAD:instance.yaml").strip()
        (self.repo / ".git" / "objects" / oid[:2] / oid[2:]).unlink()
        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 3)
        self.assertIn("git read failed", err)
        self.assertEqual({p.name: p.read_bytes() for p in self.outbox.iterdir()}, before)

    def test_committed_symlink_metadata_rejected(self):
        self.write("actual.yaml", "name: testinst\n")
        self.write("BRIEFING.md", BRIEFING_V1)
        os.symlink("actual.yaml", self.repo / "instance.yaml")
        self.commit("symlink metadata")
        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 3)
        self.assertIn("symlink", err)
        self.assertFalse(self.outbox.exists())

    def test_legacy_brain_yaml_identity(self):
        self.write("brain.yaml", "name: legacyname\n")
        self.write("BRIEFING.md", BRIEFING_V1)
        self.commit("legacy")
        rc, _, err = self.run_emitter()
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_card("legacyname")["instance"],
                         "legacyname")

    def test_nested_vault_resolves_committed_paths(self):
        self.write("instance.yaml", "name: toplevel\n")
        self.write("instance/BRIEFING.md", BRIEFING_V1)
        self.write("instance/instance.yaml", "name: nested\n")
        self.write("other/junk.md", "untracked junk\n")
        self.git("add", "instance.yaml", "instance")
        self.git("commit", "-q", "-m", "nested")
        rc, _, err = self.run_emitter(vault=self.repo / "instance")
        self.assertEqual(rc, 0)
        card = self.read_card("nested")
        self.assertEqual(card["body"], BRIEFING_V1.strip())


@unittest.skipUnless(WRAPPER.is_file(), "feed_sync.sh wrapper not available")
class WrapperTests(RepoTestCase):
    """feed_sync.sh behavior, run as an isolated copy in a sandbox.

    The copy runs with PROFILE_DIR / VAULT / SCUDERIA / LOG all pointed into
    a temp sandbox, a stub syncer (no network) and dummy credentials — no
    production path or real credential is ever touched.
    """

    def setUp(self):
        super().setUp()
        # sandbox scuderia tree: copied emitter + stub syncer
        self.scuderia = self.root / "sb" / "scuderia"
        emit_dir = (self.scuderia / "profiles/mnemo/skills/feed-emit/scripts")
        emit_dir.mkdir(parents=True)
        shutil.copyfile(EMITTER, emit_dir / "emit_briefing_card.py")
        sync_dir = self.scuderia / "interface" / "syncer"
        sync_dir.mkdir(parents=True)
        (sync_dir / "sync.py").write_text(STUB_SYNC)
        # isolated wrapper copy
        self.wrapper = self.root / "sb" / "feed_sync.sh"
        shutil.copyfile(WRAPPER, self.wrapper)
        self.wrapper.chmod(0o755)
        # sandbox vault (fresh committed repo)
        self.vault = self.root / "sb" / "vault"
        self.vault.mkdir()
        self.git("init", "-q", cwd=self.vault)
        self.git("config", "user.email", "test@example.com", cwd=self.vault)
        self.git("config", "user.name", "Test", cwd=self.vault)
        (self.vault / "instance.yaml").write_text("name: testinst\n")
        (self.vault / "BRIEFING.md").write_text(BRIEFING_V1)
        self.git("add", "-A", cwd=self.vault)
        self.git("commit", "-q", "-m", "seed", cwd=self.vault)
        # sandbox profile with dummy credentials only
        self.profile = self.root / "sb" / "profile"
        (self.profile / "cache").mkdir(parents=True)
        (self.profile / ".env").write_text(
            "FEED_URL=http://stub.invalid\nFEED_PUSH_KEY=stub-key-not-real\n")
        self.log = self.root / "sb" / "feed-sync.log"
        self.marker = self.root / "sb" / "sync-marker.jsonl"

    def run_wrapper(self, env_extra=None, path_prepend=None,
                    with_profile_env=True):
        if not with_profile_env:
            (self.profile / ".env").unlink()
        env = {
            "PATH": ((str(path_prepend) + os.pathsep if path_prepend else "")
                     + os.environ.get("PATH", "/usr/bin:/bin")),
            "HOME": str(self.root),
            "PROFILE_DIR": str(self.profile),
            "VAULT": str(self.vault),
            "SCUDERIA": str(self.scuderia),
            "LOG": str(self.log),
            "SYNC_MARKER": str(self.marker),
        }
        if env_extra:
            env.update({k: str(v) for k, v in env_extra.items()})
        if self.marker.exists():
            self.marker.unlink()
        return subprocess.run(
            ["bash", str(self.wrapper)], env=env,
            capture_output=True, text=True, timeout=180)

    def sync_calls(self):
        if not self.marker.exists():
            return []
        return [json.loads(line)
                for line in self.marker.read_text().splitlines() if line]

    def test_clean_sync_is_silent_and_runs_producers_first(self):
        proc = self.run_wrapper(env_extra={"SYNC_STUB_RC": 0,
                                           "SYNC_STUB_OUTPUT": ""})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")
        # the producer ran (from COMMITTED content) before the syncer
        card = self.vault / "feed-outbox" / "testinst__briefing__daily.json"
        self.assertTrue(card.is_file(), "emitter did not produce a card")
        card_body = json.loads(card.read_text())["body"]
        self.assertEqual(card_body, BRIEFING_V1.strip())
        calls = self.sync_calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["VAULT_ROOT"], str(self.vault))
        self.assertEqual(calls[0]["FEED_OUTBOX_DIR"],
                         str(self.vault / "feed-outbox"))
        self.assertEqual(calls[0]["FEED_STATE_FILE"],
                         str(self.profile / "cache/feed-sync-state.json"))
        self.assertEqual(calls[0]["FEED_URL"], "http://stub.invalid")
        # the credential is never printed
        self.assertNotIn("stub-key-not-real", proc.stdout + proc.stderr)

    def test_syncer_output_passed_through(self):
        proc = self.run_wrapper(env_extra={
            "SYNC_STUB_RC": 0, "SYNC_STUB_OUTPUT": "pushed 1 card"})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("pushed 1 card", proc.stdout)

    def test_emitter_failure_skips_sync_and_preserves_card(self):
        outbox = self.vault / "feed-outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        old_card = outbox / "testinst__briefing__daily.json"
        old_card.write_text("PRE-EXISTING CARD")
        stubbin = self.root / "sb" / "badgit"
        stubbin.mkdir(parents=True)
        (stubbin / "git").write_text("#!/bin/sh\nexit 1\n")
        (stubbin / "git").chmod(0o755)
        proc = self.run_wrapper(path_prepend=stubbin)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("sync skipped", proc.stdout)
        self.assertEqual(self.sync_calls(), [])  # syncer never ran
        self.assertEqual(old_card.read_text(), "PRE-EXISTING CARD")
        self.assertTrue(self.log.is_file())  # failure detail is in the log

    def test_syncer_failure_is_nonzero(self):
        proc = self.run_wrapper(env_extra={
            "SYNC_STUB_RC": 3, "SYNC_STUB_OUTPUT": "sync exploded"})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("sync exploded", proc.stdout)
        self.assertEqual(len(self.sync_calls()), 1)

    def test_missing_credentials_fail_loudly(self):
        proc = self.run_wrapper(with_profile_env=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FEED_URL", proc.stdout)
        self.assertEqual(self.sync_calls(), [])       # syncer never ran
        self.assertFalse((self.vault / "feed-outbox").exists())


if __name__ == "__main__":
    unittest.main()
