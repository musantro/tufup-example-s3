import os
from pathlib import Path
import logging

from dotenv import load_dotenv
from tufup.repo import DEFAULT_KEY_MAP, DEFAULT_KEYS_DIR_NAME, DEFAULT_REPO_DIR_NAME

# project directory
PROJECT_DIR = Path(__file__).resolve().parent

# load environment variables from .env
load_dotenv()

# rclone config
RCLONE_CONF = PROJECT_DIR / '.rclone.conf'
os.environ['RCLONE_CONFIG_FILE'] = str(RCLONE_CONF)

logger = logging.getLogger(__name__)

"""

DISCLAIMER 

For convenience, this example uses a single key pair for all TUF roles, 
and the private key is unencrypted and stored locally. This approach is *not* 
safe and should *not* be used in production. 

"""

# For development
DEV_DIR = PROJECT_DIR / '.tmp'
PYINSTALLER_DIST_DIR_NAME = 'dist'
DIST_DIR = DEV_DIR / PYINSTALLER_DIST_DIR_NAME

# Local repo path and keys path (would normally be offline)
KEYS_DIR = DEV_DIR / DEFAULT_KEYS_DIR_NAME
REPO_DIR = DEV_DIR / DEFAULT_REPO_DIR_NAME

# remotes
PRIVATE_REMOTE = os.environ['PRIVATE_REMOTE']
CLIENT_REMOTE = os.environ['CLIENT_REMOTE']

# Key settings
KEY_NAME = 'my_key'
PRIVATE_KEY_PATH = KEYS_DIR / KEY_NAME
KEY_MAP = {role_name: [KEY_NAME] for role_name in DEFAULT_KEY_MAP.keys()}
ENCRYPTED_KEYS = []
THRESHOLDS = dict(root=1, targets=1, snapshot=1, timestamp=1)
EXPIRATION_DAYS = dict(root=365, targets=7, snapshot=7, timestamp=1)
