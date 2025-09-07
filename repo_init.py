import logging
from pathlib import Path
import shutil

from rclone_python import rclone
from tufup.repo import Repository

from myapp.settings import APP_NAME
from repo_settings import (
    ENCRYPTED_KEYS,
    EXPIRATION_DAYS,
    KEY_MAP,
    KEYS_DIR,
    REPO_DIR,
    THRESHOLDS,
    PRIVATE_REMOTE,
    CLIENT_REMOTE,
)

logger = logging.getLogger(__name__)

"""

DISCLAIMER 

For convenience, this example uses a single key pair for all TUF roles, 
and the private key is unencrypted and stored locally. This approach is *not* 
safe and should *not* be used in production. 

"""


def main():
    logging.basicConfig(level=logging.INFO)

    # Create repository instance
    repo = Repository(
        app_name=APP_NAME,
        app_version_attr='myapp.__version__',
        repo_dir=REPO_DIR,
        keys_dir=KEYS_DIR,
        key_map=KEY_MAP,
        expiration_days=EXPIRATION_DAYS,
        encrypted_keys=ENCRYPTED_KEYS,
        thresholds=THRESHOLDS,
    )

    # Save configuration (JSON file)
    repo.save_config()

    # Initialize repository (creates keys and root metadata, if necessary)
    repo.initialize()

    rclone.sync('.tufup-repo-config', PRIVATE_REMOTE)
    rclone.sync(str(REPO_DIR), CLIENT_REMOTE)
    rclone.sync(str(KEYS_DIR), f'{PRIVATE_REMOTE}/keystore')

    # delete .tufup-repo-config, REPO_DIR and KEYS_DIR for security

    Path('.tufup-repo-config').unlink()
    shutil.rmtree(REPO_DIR)
    shutil.rmtree(KEYS_DIR)


if __name__ == '__main__':
    main()
