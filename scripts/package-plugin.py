#!/usr/bin/env python3
"""Build an allowlisted portable research plugin ZIP; no install or network.

The plugin has its own identity/version, separate from the npm stdio bridge.
Only newly public plugin files and this repository's existing MIT license enter
the archive. No .git, npm bridge executable, dependency, private source or asset
is included. This is packaging, not a marketplace validator or host QA result.
"""
import argparse
import json
import pathlib
import zipfile

FILES = (
    'LICENSE',
    'assets/magist-icon.png',
    'mcp.json',
    'plugin.json',
    'skills/magist-research/SKILL.md',
    'skills/magist-research/agents/openai.yaml',
)

def package(root, output):
    root = root.resolve()
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists')
    payloads = {}
    for name in FILES:
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError('Package requires regular in-root file: ' + name)
        payloads[name] = path.read_bytes()
    plugin = json.loads(payloads['plugin.json'])
    mcp = json.loads(payloads['mcp.json'])
    if plugin.get('name') != 'magist-research' or plugin.get('version') != '0.1.1':
        raise ValueError('Unexpected plugin identity; review packaging on a release change')
    if plugin.get('license') != 'MIT':
        raise ValueError('Unexpected package license')
    server = mcp.get('mcpServers', {}).get('magist', {})
    if server.get('type') != 'streamable-http' or server.get('url') != 'https://magist.io/api/mcp':
        raise ValueError('Unexpected remote transport or endpoint')
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        for name, body in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, body)
    with zipfile.ZipFile(output) as archive:
        if archive.namelist() != sorted(FILES):
            raise ValueError('Unexpected archive paths')
        for name, body in payloads.items():
            if archive.read(name) != body:
                raise ValueError('Archive roundtrip failed')
    return {'name': plugin['name'], 'version': plugin['version'],
            'output': str(output), 'files': sorted(FILES),
            'scope': 'Portable package structure only; not directory acceptance or host rendering proof.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        result = package(pathlib.Path(__file__).resolve().parent.parent, args.output)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(2, str(exc) + '\n')
    print(json.dumps(result, indent=2))
