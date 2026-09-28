from test_publication import Publication, MemoryTransport
from manuscript_ingest import workflow as w, archive, sources
from unittest.mock import patch
from pathlib import Path


class ExternalReceipts(Publication):
    def test_publish_restores_from_remote_pointer_without_brain_sidecar(self):
        job = self.staged()
        with patch.object(archive.pa, 'RcloneTransport', MemoryTransport), patch.object(w, 'integration_check', return_value=[]):
            result = w.publish(job, 1, runtime_root=self.runtime)
            self.assertEqual(result['status'], 'complete')
            self.assertEqual(list(self.page.parent.glob('*.json')), [])
            pointer = self.page.read_text().split('Article archive: ')[1].strip()
            self.assertTrue(pointer.startswith('r2://fixture/article-packages/receipts/'))
            receipt = Path(result['artifacts']['receipt'])
            self.assertFalse(receipt.is_relative_to(self.brain))
            self.assertEqual(MemoryTransport.objects[pointer.split('r2://fixture/')[1]], receipt.read_bytes())
            # A fresh runtime has no receipt cache or original job state.
            fresh = self.root/'fresh'; fresh.mkdir(); w.save(fresh/'config.json', w.config(self.runtime))
            refresh = w.start(self.page, runtime_root=fresh)['job_id']
            restored = sources.prepare(refresh, None, runtime_root=fresh)
            self.assertEqual(len(restored['artifacts']['sources']), 2)

    def test_receipt_upload_failure_does_not_apply_page_and_can_resume(self):
        job = self.staged(); original = self.page.read_bytes()
        class FailReceipt(MemoryTransport):
            def upload(self, path, key, h, size):
                if '/receipts/' in key: raise OSError('receipt upload failed')
                return super().upload(path, key, h, size)
        with patch.object(archive.pa, 'RcloneTransport', FailReceipt), patch.object(w, 'integration_check', return_value=[]):
            self.assertEqual(w.publish(job, 1, runtime_root=self.runtime)['status'], 'publication-pending')
        self.assertEqual(self.page.read_bytes(), original)
        self.assertEqual(list(self.page.parent.glob('*.json')), [])
        with patch.object(archive.pa, 'RcloneTransport', MemoryTransport), patch.object(w, 'integration_check', return_value=[]):
            self.assertEqual(w.publish(job, 1, runtime_root=self.runtime)['status'], 'complete')

    def test_migrated_receipt_hash_and_destination_are_checked(self):
        job = self.staged(); settings = w.config(self.runtime)['archive']
        with patch.object(archive.pa, 'RcloneTransport', MemoryTransport), patch.object(w, 'integration_check', return_value=[]):
            result = w.publish(job, 1, runtime_root=self.runtime)
            receipt = Path(result['artifacts']['receipt'])
            pointer = archive.retain_receipt(receipt, destination=settings)
            self.assertIn(w.sha(receipt), pointer)
            old_pointer = self.page.read_text().split('Article archive: ')[1].strip()
            self.page.write_text(self.page.read_text().replace(old_pointer, pointer))
            snapshot = w.job_path(job,self.runtime)/'archives/1/page.md'
            self.assertTrue(archive.page_matches(snapshot,self.page,receipt))
            self.assertEqual(w.publish(job,1,runtime_root=self.runtime)['status'],'complete')
            self.page.write_text(self.page.read_text()+'Human edit\n')
            self.assertFalse(archive.page_matches(snapshot,self.page,receipt))
            loaded = archive.resolve_receipt(pointer, self.root/'cache', transport=settings)
            self.assertEqual(loaded.read_bytes(), receipt.read_bytes())
            with self.assertRaisesRegex(ValueError, 'archive-pointer'):
                archive.resolve_receipt(pointer.replace('r2://fixture/', 'r2://other/'), self.root/'other', transport=settings)
            key = pointer.split('r2://fixture/')[1]
            MemoryTransport.objects[key] = b'{}'
            with self.assertRaises((ValueError, AssertionError)):
                archive.resolve_receipt(pointer, self.root/'corrupt', transport=settings)


from test_jobs import only_local_tests
def load_tests(loader, tests, pattern): return only_local_tests(__name__)
