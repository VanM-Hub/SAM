import asyncio
import sys
from pathlib import Path

# add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sam.plugin import PluginManifestLoader, PluginManifestValidator


def main():
    loader = PluginManifestLoader()
    validator = PluginManifestValidator()

    manifest_path = Path('examples/plugins/sample-plugin/manifest.yaml')
    print(f"Loading manifest from: {manifest_path}")
    manifest = loader.load_from_yaml(manifest_path)

    print('\nLoaded manifest:')
    print('  ID:', manifest.id)
    print('  Name:', manifest.name)
    print('  Version:', manifest.version)
    print('  Author:', manifest.author)
    print('  Description:', manifest.description)
    print('  Entrypoint:', manifest.entrypoint)
    print('  Capabilities:', manifest.capabilities)
    print('  Dependencies:', manifest.dependencies)
    print('  Permissions:', manifest.permissions)
    print('  Network allowlist:', manifest.network_allowlist)
    print('  Filesystem paths:', manifest.filesystem_paths)

    print('\nValidating manifest...')
    ok = validator.validate_and_log(manifest)
    print('Valid:', ok)


if __name__ == '__main__':
    main()
