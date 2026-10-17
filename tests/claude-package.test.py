import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('claude_package', ROOT / 'scripts/package-claude.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ClaudePackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='magist-claude-package-')
        self.work = Path(self.tmp.name)
        self.source = self.work / 'source'
        names = ['LICENSE', 'bin/magist-mcp-server.js',
                 'integrations/claude-desktop/manifest.json', 'integrations/claude-desktop/README.md']
        names += [module.PLUGIN + '/' + n for n in module.PLUGIN_FILES]
        for n in names:
            p = self.source / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((ROOT / n).read_bytes())

    def tearDown(self):
        self.tmp.cleanup()

    def test_reproducible_allowlists_no_private_or_executable_plugin_files(self):
        (self.source / 'private.env').write_text('SYNTHETIC_DO_NOT_INCLUDE')
        for kind in ['plugin', 'desktop']:
            a, b = self.work / (kind + 'a.zip'), self.work / (kind + 'b.zip')
            module.package(self.source, a, kind)
            module.package(self.source, b, kind)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as archive:
                self.assertEqual(set(archive.namelist()), set(module.payloads(self.source, kind)))
                self.assertNotIn('private.env', archive.namelist())
                self.assertNotIn('bin/magist-mcp-server.js', archive.namelist())
                if kind == 'plugin':
                    self.assertNotIn('server/bridge.mjs', archive.namelist())
                    self.assertEqual(json.loads(archive.read('.claude-plugin/plugin.json'))['version'], '0.1.1')

    def test_cannot_overwrite_output_or_output_symlink(self):
        p = self.work / 'keep'
        p.write_bytes(b'KEEP')
        for kind in ['plugin', 'desktop']:
            with self.assertRaises(ValueError): module.package(self.source, p, kind)
        self.assertEqual(p.read_bytes(), b'KEEP')
        link = self.work / 'dangling.zip'
        link.symlink_to(self.work / 'missing')
        with self.assertRaises(ValueError): module.package(self.source, link, 'plugin')

    def test_rejects_symlink_parent(self):
        source = self.source / module.PLUGIN / 'skills'
        shutil.rmtree(source)
        source.symlink_to(ROOT / 'skills', target_is_directory=True)
        with self.assertRaises(ValueError): module.payloads(self.source, 'plugin')

    def test_rejects_skill_drift_and_license_drift(self):
        p = self.source / module.PLUGIN / 'skills/magist-research/SKILL.md'
        reviewed = p.read_bytes()
        # A fabricated success claim in the example must not enter an archive.
        p.write_bytes(reviewed.replace(b'not an executed Claude-host result', b'an executed Claude-host result'))
        with self.assertRaises(ValueError): module.payloads(self.source, 'plugin')
        p.write_bytes(reviewed)
        (self.source / module.PLUGIN / 'LICENSE').write_text('a different grant')
        with self.assertRaises(ValueError): module.payloads(self.source, 'plugin')

    def test_rejects_old_version_on_new_claude_content(self):
        p = self.source / module.PLUGIN / '.claude-plugin/plugin.json'
        manifest = json.loads(p.read_text())
        manifest['version'] = '0.1.0'
        p.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError): module.payloads(self.source, 'plugin')

    def test_rejects_changed_endpoint_bridge_or_desktop_launcher(self):
        p = self.source / module.PLUGIN / '.mcp.json'
        d = json.loads(p.read_text()); d['mcpServers']['magist']['url'] = 'https://other.example'
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError): module.payloads(self.source, 'plugin')
        p = self.source / 'bin/magist-mcp-server.js'
        p.write_text('changed bridge')
        with self.assertRaises(ValueError): module.payloads(self.source, 'desktop')
        p.write_bytes((ROOT / 'bin/magist-mcp-server.js').read_bytes())
        p = self.source / 'integrations/claude-desktop/manifest.json'
        d = json.loads(p.read_text()); d['server']['mcp_config']['command'] = 'npx'
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError): module.payloads(self.source, 'desktop')

    def test_extracted_bundled_bridge_stdio_and_failure_semantics_on_local_fixture(self):
        # No hosted API, Claude process, provider inference or package download.
        observed = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                message = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                observed.append(message)
                if 'id' not in message:
                    self.send_response(202); self.end_headers(); return
                self.send_response(200); self.end_headers()
                if message['method'] == 'bad-json': self.wfile.write(b'not-json'); return
                if message['method'] == 'empty': return
                self.wfile.write(json.dumps({'jsonrpc': '2.0', 'id': message['id'],
                                            'result': {'method': message['method']}}).encode())
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            archive = self.work / 'desktop.mcpb'
            module.package(self.source, archive, 'desktop')
            with zipfile.ZipFile(archive) as z: z.extractall(self.work / 'unpacked')
            commands = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize'},
                        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
                        {'jsonrpc': '2.0', 'id': 3, 'method': 'bad-json'},
                        {'jsonrpc': '2.0', 'id': 4, 'method': 'empty'}]
            env = dict(os.environ, MAGIST_MCP_URL='http://127.0.0.1:' + str(server.server_port))
            proc = subprocess.run([os.environ.get('MAGIST_TEST_NODE', 'node'),
                                   str(self.work / 'unpacked/server/bridge.mjs')],
                                  input='\n'.join(map(json.dumps, commands)) + '\n{bad json}\n',
                                  capture_output=True, text=True, env=env, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            replies = list(map(json.loads, proc.stdout.splitlines()))
            self.assertEqual(len(replies), 5)
            self.assertEqual({r['id'] for r in replies}, {None, 1, 2, 3, 4})
            by_id = {r['id']: r for r in replies}
            self.assertEqual(by_id[1]['result']['method'], 'initialize')
            self.assertEqual(by_id[2]['result']['method'], 'tools/list')
            self.assertEqual(by_id[3]['error']['code'], -32700)
            self.assertEqual(by_id[4]['error']['code'], -32603)
            self.assertEqual(by_id[None]['error']['code'], -32700)
            self.assertEqual(observed, commands)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__ == '__main__': unittest.main(verbosity=2)
