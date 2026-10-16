import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

spec = importlib.util.spec_from_file_location('publisher', Path(__file__).parents[1] / 'scripts/publish-registry.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublisherSafetyTests(unittest.TestCase):
    def test_changed_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'server.json'
            path.write_text('{}')
            with self.assertRaises(ValueError):
                publisher.checked_payload(path)

    def test_only_structured_exact_404_allows_publish(self):
        for status, body, accepted in [
            (404, {'status': 404, 'detail': 'Server not found'}, True),
            (404, {'status': 404, 'detail': 'Something else'}, False),
            (401, {'status': 401, 'detail': 'Server not found'}, False),
        ]:
            error = urllib.error.HTTPError(publisher.VERSION_URL, status, 'error', {}, io.BytesIO(json.dumps(body).encode()))
            with self.subTest(status=status, body=body), patch.object(publisher.urllib.request, 'urlopen', side_effect=error):
                if accepted:
                    self.assertEqual(publisher.version_state(), 'absent')
                else:
                    with self.assertRaises(ValueError):
                        publisher.version_state()

    def test_listing_must_match_submitted_fields_and_be_active(self):
        expected = json.loads((publisher.ROOT / 'server.json').read_text())
        good = {'server': expected, '_meta': {'io.modelcontextprotocol.registry/official': {'status': 'active'}}}
        variants = [good]
        changed_remote = copy.deepcopy(good)
        changed_remote['server']['remotes'][0]['url'] = 'https://example.com/wrong'
        variants.append(changed_remote)
        changed_package = copy.deepcopy(good)
        changed_package['server']['packages'][0]['version'] = '9.9.9'
        variants.append(changed_package)
        for status in ['deprecated', 'deleted', None]:
            inactive = copy.deepcopy(good)
            inactive['_meta']['io.modelcontextprotocol.registry/official']['status'] = status
            variants.append(inactive)
        for index, variant in enumerate(variants):
            with self.subTest(index=index), patch.object(publisher.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(variant).encode())):
                if index == 0:
                    self.assertEqual(publisher.version_state(), 'exists')
                else:
                    with self.assertRaises(ValueError):
                        publisher.version_state()

    def test_local_or_wrong_commit_dispatch_is_rejected(self):
        with patch.dict(publisher.os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                publisher.require_dispatch()

    def test_automatic_rerun_is_rejected(self):
        env = {'GITHUB_ACTIONS': 'true', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
               'GITHUB_RUN_ATTEMPT': '2', 'GITHUB_REPOSITORY': 'magist-io/magist-mcp-server',
               'GITHUB_REF': 'refs/heads/main', 'REVIEWED_SHA': 'a' * 40, 'GITHUB_SHA': 'a' * 40}
        with patch.dict(publisher.os.environ, env, clear=True):
            with self.assertRaises(ValueError):
                publisher.require_dispatch()

    def test_existing_version_performs_no_auth_or_publish(self):
        with patch.object(publisher, 'require_dispatch'), patch.object(publisher, 'checked_payload', return_value=b'payload'), patch.object(publisher, 'version_state', return_value='exists'), patch.object(publisher, 'publisher_binary') as binary:
            self.assertEqual(publisher.main(), 0)
            binary.assert_not_called()

    def test_failed_login_never_publishes(self):
        with patch.object(publisher, 'require_dispatch'), patch.object(publisher, 'checked_payload', return_value=b'payload'), patch.object(publisher, 'version_state', return_value='absent'), patch.object(publisher, 'publisher_binary', return_value=Path('/fake/publisher')), patch.object(publisher, 'run_private', return_value=1) as run:
            self.assertEqual(publisher.main(), 1)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][-2:], ['login', 'github-oidc'])


if __name__ == '__main__':
    unittest.main()
