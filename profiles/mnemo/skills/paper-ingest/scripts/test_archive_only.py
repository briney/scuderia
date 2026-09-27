"""Archive-only pages retain evidence remotely and use external working directories."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import figure_embeds as fe
import initial_ingest as ii
import reenrich as rr
import final_products as fp
import test_figure_embeds as fixture_figures

class ArchiveOnly(unittest.TestCase):
    def test_remove_owned_figures_preserves_prose_and_archive_pointer(self):
        fixture=fixture_figures.FigureEmbeds('runTest');fixture.setUp();self.addCleanup(fixture.doCleanups)
        original=fixture.text+'Article archive: ../docs/publication.json\nSource package: ../source-packages/main/manifest.json\nEnrichment products: ../source-packages/main/results.json\n'
        rendered=fe.render(original,fixture.manifest,fixture.page)
        result=fe.archive_only(rendered)
        self.assertIn('Unchanged research.',result)
        self.assertIn('Article archive: ../docs/publication.json',result)
        self.assertNotIn('paper-figure',result);self.assertNotIn('## Figures',result)
        self.assertNotIn('source-packages',result)
        edited=rendered.replace('**Figure 1**','**Edited figure**')
        with self.assertRaisesRegex(ValueError,'figure-block-edited'):fe.archive_only(edited)

    def test_work_roots_cannot_create_source_material_inside_instance(self):
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp);brain=root/'brain';brain.mkdir();(brain/'instance.yaml').write_text('name: synthetic\n')
            page=brain/'papers/synthetic.md';page.parent.mkdir()
            with self.assertRaisesRegex(ValueError,'article-work-must-be-outside-instance'):
                ii.plan('synthetic',page=page,work_root=brain/'source-packages/work',identity=None)
            self.assertFalse((brain/'source-packages').exists())
            page.write_text('---\nkind: paper\nslug: synthetic\n---\n## Findings\nExisting research.\n')
            with self.assertRaisesRegex(ValueError,'article-work-must-be-outside-instance'):
                rr.plan(rr.Request('synthetic',page=page),work_root=brain/'scratch/work',fixture=True)
            plan=rr.plan(rr.Request('synthetic',page=page),work_root=root/'work',fixture=True)
            self.assertFalse(plan['figure_embeds']);self.assertEqual(plan['page_storage'],'archive-only-v1')

    def test_archive_only_ingest_rejects_local_payload_links(self):
        manifest=dict(article=dict(slug='synthetic'),source_status=dict(fixture=False),
            initial_ingest=dict(production_complete=True,page_storage='archive-only-v1',figure_embeds=False,
                readiness=dict(page_ready=True,holds=[]),qualifications=''))
        with patch.object(fp,'verify',return_value=manifest):
            fp.verify_ingest('/unused',dict(slug='synthetic'),'Article archive: receipt.json',require_publication=False)
            for text in ('Source package: /tmp/manifest.json','![Figure](crop.png)','<!-- paper-figure {} -->'):
                with self.assertRaisesRegex(ValueError,'archive-only-page'):
                    fp.verify_ingest('/unused',dict(slug='synthetic'),text,require_publication=False)

    def test_archived_page_requires_restore_before_refresh_plan(self):
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp);page=root/'paper.md'
            page.write_text('---\nkind: paper\nslug: synthetic\n---\n## Findings\nResearch.\n## Ingest log\nArticle archive: receipt.json\n')
            with self.assertRaisesRegex(ValueError,'archived-page-requires-external-restore'):
                rr.route('synthetic',page=page,work_root=root/'work',fixture=True)
            self.assertFalse((root/'work').exists())
