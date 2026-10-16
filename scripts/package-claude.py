#!/usr/bin/env python3
"""Build bounded Claude plugin/MCPB archives without network or installation."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

PLUGIN = 'integrations/claude'
BRIDGE_SHA256 = '6a1a51030fbebc3816319fea2f1efaa7a351bd7abba3dc7b864fe5b450524621'
PLUGIN_FILES = ('.claude-plugin/plugin.json', '.mcp.json', 'README.md',
                'LICENSE', 'skills/magist-research/SKILL.md')


def read(root, relative):
    path = root / relative
    if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise ValueError('Symlink in source path: ' + relative)
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError('Expected regular in-root file: ' + relative)
    return path.read_bytes()


def payloads(root, kind):
    root = root.resolve()
    if kind == 'plugin':
        files = {n: read(root, PLUGIN + '/' + n) for n in PLUGIN_FILES}
        manifest = json.loads(files['.claude-plugin/plugin.json'])
        if manifest.get('name') != 'magist-research' or manifest.get('version') != '0.1.0':
            raise ValueError('Unexpected Claude plugin identity')
        if json.loads(files['.mcp.json']) != {'mcpServers': {'magist': {
                'type': 'http', 'url': 'https://magist.io/api/mcp'}}}:
            raise ValueError('Unexpected Claude connector')
        if files['skills/magist-research/SKILL.md'] != read(root, 'skills/magist-research/SKILL.md'):
            raise ValueError('Claude skill has drifted from the reviewed public skill')
        if len(files['README.md'].decode().split()) < 40:
            raise ValueError('Claude README is too short')
    elif kind == 'desktop':
        bridge = read(root, 'bin/magist-mcp-server.js')
        if hashlib.sha256(bridge).hexdigest() != BRIDGE_SHA256:
            raise ValueError('Bridge differs from the pinned published 0.1.1 bytes')
        files = {'manifest.json': read(root, 'integrations/claude-desktop/manifest.json'),
                 'README.md': read(root, 'integrations/claude-desktop/README.md'),
                 'LICENSE': read(root, 'LICENSE'), 'server/bridge.mjs': bridge}
        manifest = json.loads(files['manifest.json'])
        if manifest.get('manifest_version') != '0.3' or manifest.get('version') != '0.1.1':
            raise ValueError('Unexpected Desktop manifest identity')
        if manifest.get('server') != {'type': 'node', 'entry_point': 'server/bridge.mjs',
                'mcp_config': {'command': 'node', 'args': ['${__dirname}/server/bridge.mjs'],
                               'env': {'MAGIST_MCP_URL': 'https://magist.io/api/mcp'}}}:
            raise ValueError('Unexpected Desktop launch configuration')
        if manifest.get('privacy_policies') != ['https://magist.io/privacy']:
            raise ValueError('Desktop bundle must disclose the hosted privacy policy')
    else:
        raise ValueError('Unknown package kind')
    if files['LICENSE'] != read(root, 'LICENSE'):
        raise ValueError('Bundled license has drifted')
    return files


def package(root, output, kind):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists')
    files = payloads(Path(root), kind)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, body in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, body)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() or archive.namelist() != sorted(files):
            raise ValueError('Archive boundary verification failed')
        for name, body in files.items():
            if archive.read(name) != body:
                raise ValueError('Archive roundtrip failed')
    return {'kind': kind, 'bytes': output.stat().st_size,
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'members': {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}
                        for n, b in sorted(files.items())},
            'scope': 'Local package checks only; no host, portal or directory approval'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['plugin', 'desktop'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(Path(__file__).resolve().parents[1], args.output, args.kind), indent=2))
