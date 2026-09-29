import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOLS))

class LegacyBoundary(unittest.TestCase):
    def test_compat_reader_has_no_execution_surface(self):
        from article_archive_compat import reader, retired
        self.assertTrue(callable(reader.verify))
        self.assertEqual(retired.refuse()['blocking_reason'], 'retired-workflow')
        for name in ('article_enrichment', 'reenrich', 'portable_articles'):
            module = importlib.import_module('article_archive_compat.' + name)
            for forbidden in ('execute', 'advance', 'publish', 'plan', 'route', 'build_manifest'):
                self.assertFalse(hasattr(module, forbidden), (name, forbidden))

    def test_fixture_and_corruption(self):
        from article_archive_compat import portable_articles as pa, reader
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()/'input'; root.mkdir(); source = root/'original.pdf'; source.write_bytes(b'synthetic')
            h = pa.sha(source); article = dict(slug='synthetic', doi=None, pmid=None)
            manifest = dict(schema=pa.SCHEMA, package_id='fixture', article=article,
                article_key=pa.article_key(article), files=[dict(role='source-original',key='source.pdf',sha256=h,size=9)],total_objects=1,
                documents=[dict(identity='main',source_sha256=h,source_version='1',complete=False,fixture=True,raw_key='source.pdf')],
                common_dependencies=['source.pdf'],elements=[],source_status=dict(complete=False,fixture=True,acquisition_verified=False,extraction_verified=False,holds=[]),dispositions=[],provenance=dict(fixture=True))
            pa.save(root/'manifest.json',manifest)
            pa.save(root/'local-map.json',dict(schema='portable-article-local-map-v2',manifest_sha256=pa.sha(root/'manifest.json'),sources={'source.pdf':dict(root=str(root),path='original.pdf')}))
            self.assertEqual(reader.verify(root/'manifest.json')['article'],article)
            restored=root.parent/'restored'; reader.restore(root/'manifest.json',restored)
            self.assertEqual(reader.verify(restored/'manifest.json')['article'],article)
            source.write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError,'corrupt'):
                reader.verify(root/'manifest.json')

if __name__ == '__main__': unittest.main()

class SelectiveLegacy(unittest.TestCase):
    def test_original_reuse_excludes_derived_body_and_enrichment(self):
        from article_archive_compat import portable_articles as pa
        from manuscript_ingest import archive
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); source=root/'source.pdf'; source.write_bytes(b'original')
            text=root/'body.txt'; text.write_text('derived body')
            rows=[dict(role='source-original',key=p.name,sha256=pa.sha(p),size=p.stat().st_size) for p in (source,text)]
            article=dict(slug='synthetic',doi=None,pmid=None,version='Corrected proof')
            m=dict(schema=pa.SCHEMA,package_id='fixture',article=article,article_key=pa.article_key(article),files=rows,total_objects=2,
                documents=[dict(identity='main',source_role='manuscript',source_sha256=pa.sha(source),source_version='Corrected proof',complete=False,fixture=True,raw_key=source.name)],
                source_documents=[dict(identity='main',role='manuscript',key=source.name),dict(identity='body',role='body',key=text.name)],
                common_dependencies=[source.name],elements=[],source_status=dict(complete=False,fixture=True,acquisition_verified=False,extraction_verified=False,holds=[]),dispositions=[],provenance=dict(fixture=True))
            pa.save(root/'manifest.json',m)
            pa.save(root/'local-map.json',dict(schema='portable-article-local-map-v2',manifest_sha256=pa.sha(root/'manifest.json'),sources={p.name:dict(root=str(root),path=p.name) for p in (source,text)}))
            out=archive.open_sources(root/'manifest.json',root/'selected',identity={'version':'corrected-proof'})
            self.assertEqual(len(out['inputs']),1); self.assertFalse((root/'selected/body.txt').exists())
            with self.assertRaisesRegex(ValueError,'version'):
                archive.open_sources(root/'manifest.json',root/'conflict',identity={'version':'preprint v2'})
            self.assertFalse((root/'conflict/source.pdf').exists())
