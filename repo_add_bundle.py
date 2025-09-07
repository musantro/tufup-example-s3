import logging
from pathlib import Path
import shutil
import sys

import subprocess
from rclone_python import rclone
from tufup.repo import Repository

from repo_settings import DIST_DIR, KEYS_DIR, REPO_DIR, PRIVATE_REMOTE, CLIENT_REMOTE

logger = logging.getLogger(__name__)


def main():
    rclone.sync(f'{PRIVATE_REMOTE}/keystore', str(KEYS_DIR))
    rclone.sync(f'{PRIVATE_REMOTE}/.tufup-repo-config', '.')

    rclone.sync(f'{CLIENT_REMOTE}/metadata', str(REPO_DIR / 'metadata'))

    subprocess.run(
        [
            'pyinstaller',
            'main.spec',
            ' --clean',
            '-y',
            '--distpath',
            '.tmp/dist',
            '--workpath',
            '.tmp/build',
        ]
    )

    # create archive from latest pyinstaller bundle (assuming we have already
    # created a pyinstaller bundle, and there is only one)
    try:
        bundle_dirs = [path for path in DIST_DIR.iterdir() if path.is_dir()]
    except FileNotFoundError:
        sys.exit(f'Directory not found: {DIST_DIR}\nDid you run pyinstaller?')
    if len(bundle_dirs) != 1:
        sys.exit(f'Expected one bundle, found {len(bundle_dirs)}.')
    bundle_dir = bundle_dirs[0]
    print(f'Adding bundle: {bundle_dir}')

    # Create repository instance from config file (assuming the repository
    # has already been initialized)
    repo = Repository.from_config()

    repo.initialize()

    # Add new app bundle to repository (automatically reads myapp.__version__)
    repo.add_bundle(
        new_bundle_dir=bundle_dir,
        skip_patch=True,
        # [optional] custom metadata can be any dict (default is None)
        custom_metadata={'changes': ['new feature x added', 'bug y fixed']},
    )
    repo.publish_changes(private_key_dirs=[KEYS_DIR])

    rclone.sync('.tufup-repo-config', PRIVATE_REMOTE)
    rclone.sync(str(REPO_DIR / 'metadata'), f'{CLIENT_REMOTE}/metadata')
    rclone.sync(str(KEYS_DIR), f'{PRIVATE_REMOTE}/keystore')
    rclone.copy(str(REPO_DIR / 'targets'), f'{CLIENT_REMOTE}/targets')

    Path('.tufup-repo-config').unlink()
    shutil.rmtree(REPO_DIR)
    shutil.rmtree(KEYS_DIR)

    print('Done.')


if __name__ == '__main__':
    main()
