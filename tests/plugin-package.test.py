import importlib.util
import json
import pathlib
import shutil
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('plugin_package', ROOT / 'scripts/package-plugin.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PluginPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='magist-plugin-test-')
        self.work = pathlib.Path(self.tmp.name)
        self.source = self.work / 'source'
        for name in module.FILES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
    def tearDown(self):
        self.tmp.cleanup()
    def test_reproducible_zip_excludes_unlisted_material(self):
        (self.source / '.env').write_text('SYNTHETIC_NOT_A_SECRET=excluded')
        (self.source / 'bin').mkdir()
        (self.source / 'bin/bridge.js').write_text('throw new Error("must not execute")')
        a, b = self.work / 'a.zip', self.work / 'b.zip'
        module.package(self.source, a)
        module.package(self.source, b)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with zipfile.ZipFile(a) as archive:
            self.assertEqual(len(archive.namelist()), 6)
            self.assertIn('plugin.json', archive.namelist())
            self.assertIn('skills/magist-research/SKILL.md', archive.namelist())
            self.assertFalse(any(name.startswith(('.', 'bin/')) for name in archive.namelist()))
            self.assertEqual(archive.read('LICENSE'), (ROOT / 'LICENSE').read_bytes())
            manifest = json.loads(archive.read('plugin.json'))
            metadata = manifest['extensions']['com.openai']
            self.assertEqual(len(metadata['review']['test_cases']['positive']), 5)
            self.assertEqual(len(metadata['review']['test_cases']['negative']), 3)
            for key in ['logo', 'composerIcon']:
                self.assertIn(metadata['interface'][key].removeprefix('./'), archive.namelist())
            self.assertNotIn('demo_recording_url', metadata['review'])
    def test_rejects_symlink_and_missing_skill(self):
        p = self.source / 'skills/magist-research/SKILL.md'
        p.unlink()
        with self.assertRaises(ValueError):
            module.package(self.source, self.work / 'missing.zip')
        p.symlink_to(ROOT / 'skills/magist-research/SKILL.md')
        with self.assertRaises(ValueError):
            module.package(self.source, self.work / 'link.zip')
    def test_rejects_external_parent_symlink(self):
        shutil.rmtree(self.source / 'skills')
        (self.source / 'skills').symlink_to(ROOT / 'skills', target_is_directory=True)
        with self.assertRaises(ValueError):
            module.package(self.source, self.work / 'parent-link.zip')
    def test_never_overwrites_existing_output(self):
        output = self.work / 'existing.zip'
        output.write_bytes(b'KEEP')
        with self.assertRaises(ValueError):
            module.package(self.source, output)
        self.assertEqual(output.read_bytes(), b'KEEP')
    def test_rejects_changed_endpoint_and_bridge_identity(self):
        path = self.source / 'mcp.json'
        data = json.loads(path.read_text())
        data['mcpServers']['magist']['url'] = 'https://unrelated.example/mcp'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            module.package(self.source, self.work / 'endpoint.zip')
        shutil.copyfile(ROOT / 'mcp.json', path)
        path = self.source / 'plugin.json'
        data = json.loads(path.read_text())
        data['name'] = '@magist/mcp-server'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            module.package(self.source, self.work / 'identity.zip')

if __name__ == '__main__':
    unittest.main(verbosity=2)
