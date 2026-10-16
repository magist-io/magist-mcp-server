#!/usr/bin/env python3
"""One manual, exact-payload publication using ephemeral GitHub Actions OIDC."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_SHA = '25877b9d2682de0263b2b8aaeb296a8eef9f7f62d1f46cbad9171d579f659736'
ASSET_SHA = 'a06c9096dcb9727c13555b6be26c7effa707b01f06a4c561ba7a3635443cf2cc'
ASSET = 'https://github.com/modelcontextprotocol/registry/releases/download/v1.8.1/mcp-publisher_linux_amd64.tar.gz'
VERSION_URL = 'https://registry.modelcontextprotocol.io/v0.1/servers/io.github.magist-io%2Fmagist/versions/0.1.1'
NAME = 'io.github.magist-io/magist'


def version_state():
    """Only a structured exact-version 404 establishes eligibility to publish."""
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=30) as response:
            body = response.read(2 * 1024 * 1024 + 1)
            if len(body) > 2 * 1024 * 1024:
                raise ValueError('oversized listing')
            data = json.loads(body)
            expected = json.loads(checked_payload(ROOT / 'server.json'))
            if data.get('server') != expected:
                raise ValueError('listing differs from reviewed payload')
            official = data.get('_meta', {}).get('io.modelcontextprotocol.registry/official', {})
            if official.get('status') != 'active':
                raise ValueError('listing is not authoritatively active')
            return 'exists'
    except urllib.error.HTTPError as error:
        body = error.read(8193)
        if error.code == 404 and len(body) <= 8192:
            data = json.loads(body)
            if data.get('status') == 404 and data.get('detail') == 'Server not found':
                return 'absent'
        raise ValueError('registry read did not establish eligibility') from None


def checked_payload(path):
    raw = path.read_bytes()
    if len(raw) != 695 or hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA:
        raise ValueError('payload differs from reviewed bytes')
    return raw


def require_dispatch():
    expected = os.environ.get('REVIEWED_SHA', '')
    if not (os.environ.get('GITHUB_ACTIONS') == 'true'
            and os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'
            and os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
            and os.environ.get('GITHUB_REPOSITORY') == 'magist-io/magist-mcp-server'
            and os.environ.get('GITHUB_REF') == 'refs/heads/main'
            and re.fullmatch(r'[0-9a-f]{40}', expected)
            and expected == os.environ.get('GITHUB_SHA')):
        raise ValueError('not the intended reviewed manual dispatch')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if actual != expected:
        raise ValueError('checkout is not reviewed dispatch commit')


def publisher_binary(directory):
    with urllib.request.urlopen(ASSET, timeout=60) as response:
        archive = response.read(8 * 1024 * 1024 + 1)
    if len(archive) > 8 * 1024 * 1024 or hashlib.sha256(archive).hexdigest() != ASSET_SHA:
        raise ValueError('publisher archive checksum mismatch')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as bundle:
        matches = [entry for entry in bundle.getmembers() if entry.name == 'mcp-publisher']
        if len(matches) != 1 or not matches[0].isfile() or matches[0].size > 32 * 1024 * 1024:
            raise ValueError('unexpected publisher archive member')
        stream = bundle.extractfile(matches[0])
        if stream is None:
            raise ValueError('publisher missing')
        raw = stream.read(32 * 1024 * 1024 + 1)
    binary = directory / 'mcp-publisher'
    binary.write_bytes(raw)
    binary.chmod(0o700)
    return binary


def run_private(command, directory, env):
    # Never print publisher output: authentication errors can contain raw tokens.
    try:
        result = subprocess.run(command, cwd=directory, env=env, capture_output=True,
                                timeout=180, check=False)
        return result.returncode
    except subprocess.TimeoutExpired:
        return None


def main():
    require_dispatch()
    payload = checked_payload(ROOT / 'server.json')
    if version_state() == 'exists':
        print('Exact version already exists; no authentication or publication performed.')
        return 0
    with tempfile.TemporaryDirectory(prefix='magist-registry-') as temporary:
        directory = Path(temporary)
        directory.chmod(0o700)
        binary = publisher_binary(directory)
        (directory / 'server.json').write_bytes(payload)
        env = dict(os.environ, HOME=str(directory), XDG_CONFIG_HOME=str(directory / 'config'),
                   XDG_STATE_HOME=str(directory / 'state'))
        login = run_private([str(binary), 'login', 'github-oidc'], directory, env)
        print('OIDC login command exit:', login)
        if login != 0:
            print('Authentication failed or timed out; no publication attempted. No automatic retry.')
            return 1
        result = run_private([str(binary), 'publish', 'server.json'], directory, env)
        print('One publication command exit:', result)
        # A zero exit is not a public-listing receipt; a timeout may have committed.
        try:
            visible = version_state()
        except Exception:
            visible = 'unknown'
        print('Independent exact-version listing:', visible)
        if result != 0 or visible != 'exists':
            print('Publication not fully verified; stop for reconciliation, never automatically retry.')
            return 1
        print('Exact version independently visible; publication verified.')
        return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        # Keep potentially sensitive exception strings and remote bodies out of logs.
        print('Publication stopped by a prerequisite or network error. No automatic retry.')
        raise SystemExit(1)
