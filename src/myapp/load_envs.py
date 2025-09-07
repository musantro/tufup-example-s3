import os
import sys

from dotenv import load_dotenv

env_file_name = '.env'


print('Loading configuration...')
if getattr(sys, 'frozen', False):
    # we are running in a bundle
    print('Running in a bundle.')
    bundle_dir = sys._MEIPASS  # type: ignore
    dotenv_path = os.path.join(bundle_dir, env_file_name)
else:
    # we are running in a normal Python environment
    print('Running in a normal Python environment.')
    bundle_dir = os.getcwd()
    dotenv_path = os.path.join(bundle_dir, env_file_name)

load_dotenv(verbose=True, dotenv_path=dotenv_path)
print('Configuration loaded.')
