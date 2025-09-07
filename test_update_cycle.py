import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import tarfile
import threading
import time
from contextlib import contextmanager
from functools import partial
from pathlib import Path

from rich.console import Console

import repo_init
from myapp import settings

console = Console()

PROJECT_DIR = Path(__file__).parent.resolve()


@contextmanager
def assert_exe_success():
    def run(args, **kwargs):
        proc = subprocess.run(args, **kwargs)
        if proc.returncode != 0:
            console.print('Failed', style='red')
            sys.exit(1)
        return proc

    yield run


def remove_myapp_directory(path, app_name):
    if path.name == app_name:
        if path.exists():
            confirm = input(f'Remove directory {path}? [y]/n: ')
            if confirm in ('', 'y'):
                shutil.rmtree(path)
        else:
            console.print(f'Path does not exist: {path}', style='yellow')
    else:
        console.print(f'{app_name} not in path: {path}', style='yellow')


class Publisher:
    REPO_DIRS = [settings.DEV_DIR]
    SETTINGS_PATH = PROJECT_DIR / 'src' / 'myapp' / 'settings.py'

    @staticmethod
    def purge_previous_state():
        for directory in Publisher.REPO_DIRS:
            remove_myapp_directory(directory, settings.APP_NAME)

    @staticmethod
    def ensure_directories():
        for directory in Publisher.REPO_DIRS:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                console.print(f'Directory created: {directory}', style='green')

    @staticmethod
    def init_tufup_repository():
        console.print(
            f'Initializing tuf repository for {settings.APP_NAME}', style='green'
        )
        repo_init.main()

    @staticmethod
    def serve():
        handler = partial(
            http.server.SimpleHTTPRequestHandler,
            directory=str(settings.DEV_DIR / 'repository'),
        )
        with socketserver.TCPServer(('', 8000), handler) as httpd:
            httpd.serve_forever()

    @staticmethod
    def start_server():
        console.print('Starting update server', style='green')
        server_thread = threading.Thread(target=Publisher.serve, daemon=True)
        server_thread.start()
        time.sleep(1)
        return server_thread

    @staticmethod
    def create_bundle():
        console.print(f'Creating {settings.APP_NAME} bundle', style='green')
        subprocess.run([sys.executable, 'repo_add_bundle.py'], check=True)

    @staticmethod
    def bump_version(from_ver: str, to_ver: str):
        console.print(
            f'Bumping {settings.APP_NAME} version to v{to_ver} (temporary)',
            style='green',
        )
        settings_text = Publisher.SETTINGS_PATH.read_text()
        Publisher.SETTINGS_PATH.write_text(settings_text.replace(from_ver, to_ver))

    @staticmethod
    def cleanup(from_ver: str, to_ver: str):
        console.print('Rolling back temporary source modification', style='green')
        Publisher.SETTINGS_PATH.write_text(
            Publisher.SETTINGS_PATH.read_text().replace(from_ver, to_ver)
        )


class Client:
    APP_INSTALL_DIR = Path(os.environ['LOCALAPPDATA']) / 'Programs' / settings.APP_NAME
    APP_DATA_DIR = Path(os.environ['LOCALAPPDATA']) / settings.APP_NAME
    TARGETS_DIR = APP_DATA_DIR / 'update_cache' / 'targets'
    CLIENT_DIRS = [APP_INSTALL_DIR, APP_DATA_DIR]
    EXE_PATH = APP_INSTALL_DIR / 'main.exe'
    ENABLE_PATCH_UPDATE = True

    @staticmethod
    def install_v1():
        console.print(
            f'Downloading and installing {settings.APP_NAME} v1.0 from server into {Client.APP_INSTALL_DIR}',
            style='green',
        )
        import urllib.request

        url = f'{settings.BASE_URL}/targets/{settings.APP_NAME}-1.0.tar.gz'
        tmp_archive = Client.APP_INSTALL_DIR / f'{settings.APP_NAME}-1.0.tar.gz'
        urllib.request.urlretrieve(url, str(tmp_archive))
        try:
            with tarfile.open(tmp_archive, 'r:gz') as tar:
                tar.extractall(path=Client.APP_INSTALL_DIR)
            if Client.ENABLE_PATCH_UPDATE:
                console.print('Enabling patch update', style='green')
                shutil.copy(tmp_archive, Client.TARGETS_DIR)
        finally:
            try:
                tmp_archive.unlink()
            except FileNotFoundError:
                pass

    @staticmethod
    def run_app():
        console.print(f'Running {settings.APP_NAME} for update...', style='green')
        with assert_exe_success() as run:
            run([str(Client.EXE_PATH)])

    @staticmethod
    def run_app_capture() -> str:
        console.print(
            f'Running {settings.APP_NAME} again to verify version',
            style='green',
        )
        with assert_exe_success() as run:
            proc = run([str(Client.EXE_PATH)], capture_output=True, text=True)
        return proc.stdout

    @staticmethod
    def verify_update(expected_version: str, output: str):
        pattern = f'{settings.APP_NAME} {expected_version}'
        if pattern in output:
            console.print(f'\nSUCCESS: {pattern} found', style='green')
        else:
            console.print(f'\nFAIL: {pattern} not found in:\n{output}', style='red')
            sys.exit(1)

    @staticmethod
    def purge_previous_state():
        for directory in Client.CLIENT_DIRS:
            remove_myapp_directory(directory, settings.APP_NAME)

    @staticmethod
    def ensure_directories():
        for directory in Client.CLIENT_DIRS + [Client.TARGETS_DIR]:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                console.print(f'Directory created: {directory}', style='green')

    @staticmethod
    def cleanup():
        remaining_dirs = [d for d in Client.CLIENT_DIRS if d.exists()]
        for directory in remaining_dirs:
            console.print(
                f'{settings.APP_NAME} files remain in: {directory}', style='yellow'
            )
        if remaining_dirs:
            console.print('Would you like to remove these directories?', style='yellow')
            confirm = input('[y]/n: ')
            if confirm in ('', 'y'):
                for directory in remaining_dirs:
                    remove_myapp_directory(directory, settings.APP_NAME)


def main():
    Publisher.purge_previous_state()
    Client.purge_previous_state()

    Publisher.ensure_directories()
    Client.ensure_directories()

    Publisher.init_tufup_repository()

    Publisher.create_bundle()

    Client.install_v1()

    Publisher.bump_version('1.0', '2.0')

    Publisher.create_bundle()

    Publisher.cleanup('2.0', '1.0')
    Client.run_app()

    input(
        console.render_str(
            '[yellow]hit enter to proceed, after console has closed:[/yellow]'
        )
    )

    output = Client.run_app_capture()

    Client.verify_update('2.0', output)

    Client.cleanup()


if __name__ == '__main__':
    main()
