# Tufup example for production (S3, or any filesystem)

This repository demonstrates using the `tufup` package to perform automated
application updates with a modern, more production ready example app (`myapp`)
and an rclone-backed repository that can simulate local or remote storage (S3,
remote filesystems, etc.). The examples are intended to be closer to a
production workflow while remaining easy to run locally for development and
testing.

This is an iteration of the great `tufup-example` project.

## Important highlights

- The example app lives in `src/myapp`.
- Repository provisioning and publishing scripts use `rclone` to simulate
  private and client remotes (`PRIVATE_REMOTE` and `CLIENT_REMOTE`).
- Configuration lives in `repo_settings.py` and can be controlled with
  environment variables and a local `.rclone.conf` (see below).
- The example uses PyInstaller for creating a distributable bundle, but `tufup`
  itself is bundle-agnostic — any archive/directory representing your app works.

## Security disclaimer

This example is intentionally simple to make it easy to follow the flow. For
convenience it uses an unencrypted private key file and a single key for all
roles. This is NOT secure for production. Do not reuse this key strategy for
real deployments. See TUF docs for best practices.

## Quick prerequisites

- Python 3.10+ (or the version this project targets)
- `uv` (for installing Python dependencies)

Install project requirements

```
uv sync
```

rclone configuration

- A project-local rclone config file is expected at `./.rclone.conf` (the
  project sets `RCLONE_CONFIG_FILE` to `repo_settings.RCLONE_CONF`). Copy the
  `./.rclone.conf.example` to get started.

- Create remotes in that config (named however you like) and then set the
  environment variables `PRIVATE_REMOTE` and `CLIENT_REMOTE` before running the
  repo scripts. Example `.env` entries:

  PRIVATE_REMOTE=myremote:private-bucket/my_app
  CLIENT_REMOTE=myremote:public-bucket/my_app BASE_URL=<http://localhost:8000>

The project `repo_settings.py` reads `.env` (via `dotenv`) so you can place
these in a `.env` file in the repo root for convenience.

High-level workflow

1. Initialize repository metadata and keys (`repo_init.py`). This creates the
   repo root metadata and uploads repo config and keystore to the
   `PRIVATE_REMOTE` via `rclone`.
1. Build an application bundle (the example uses `pyinstaller` and `main.spec`).
1. Add the bundle to the repository (`repo_add_bundle.py`) which downloads repo
   state with `rclone`, creates target metadata, publishes changes, and uploads
   updated metadata and targets to remotes.
1. On the client side, the application (when installed) reads
   `BASE_URL`/metadata and downloads targets from `TARGET_BASE_URL` to update
   itself.

Repo-side (step-by-step)

1. Configure `.rclone.conf` and set `PRIVATE_REMOTE` and `CLIENT_REMOTE`, and
   `BASE_URL`.

1. Initialize the repository and keys:

   `uv run repo_init.py`

   - This will create a `.tufup-repo-config` file and the local development repo
     under `.tmp/` (as configured in `repo_settings.py`).
   - `repo_init.py` then uploads `.tufup-repo-config` and the keystore to
     `PRIVATE_REMOTE` and syncs client-readable metadata to `CLIENT_REMOTE`.
   - For security the script removes the local `.tufup-repo-config`, repo dir,
     and keystore after upload.

1. Build a distributable bundle. The example uses PyInstaller and `main.spec`.
   You can build in-place or follow the script used in `repo_add_bundle.py`
   which puts builds under `.tmp/dist`.

   `pyinstaller main.spec --clean -y --distpath .tmp/dist --workpath .tmp/build`

1. Add the bundle to the repo (creates targets metadata and publishes):

   `python repo_add_bundle.py`

   - This script will pull the keystore and repo metadata from the configured
     `PRIVATE_REMOTE` / `CLIENT_REMOTE`, build the required repo objects, and
     publish the changes back up using `rclone`.
   - By default the example sets `skip_patch=True` for faster testing. Check
     `repo_add_bundle.py` for options.

Notes about `repo_add_bundle.py` and `repo_init.py`:

- Both scripts use `tufup.repo.Repository` for repository operations and
  `rclone_python.rclone` for syncing files to/from remotes.
- `repo_settings.py` defines the development locations used by the scripts (e.g.
  `.tmp/`, keys dir, repo dir) and also reads the `RCLONE_CONFIG_FILE`.

Client-side (testing an installed application)

1. To simulate an initial install, obtain a target archive (for example the
   `my_app-1.0.tar.gz` under the `targets` folder in whatever remote you use)
   and extract it to the `INSTALL_DIR` defined in `src/myapp/settings.py`.
   - During development the `INSTALL_DIR` and cache directories are under `.tmp`
     — see `src/myapp/settings.py`.
1. Run the installed app (or run `src/main.py` in non-frozen mode). The app will
   use `BASE_URL` (default `http://localhost:8000`) to fetch metadata and
   targets.
1. To serve metadata and targets for a client to access, you can either:
   - Use a simple static server that points to the `CLIENT_REMOTE` content
     synced locally, for example:

     rclone copy %CLIENT_REMOTE% .tmp/repo_snapshot --config .rclone.conf python
     -m http.server -d .tmp/repo_snapshot 8000

     Then set `BASE_URL=http://localhost:8000` so the client reads
     metadata/targets from that server.

   - Or use `rclone serve http` directly from the remote if your remote supports
     it (see `rclone serve` docs).

Testing the end-to-end update cycle

- A small test helper `test_update_cycle.py` is included as a convenience to run
  through the repo/client flow. Review it before running in your environment.

Troubleshooting and cleaning up

If something gets into an inconsistent state it is easiest to start from a clean
slate:

- Remove the local development repo and build artifacts:

  `rm -rf .tmp del .tufup-repo-config` # on Windows cmd.exe

- Remove cached client data (see `src/myapp/settings.py` for `UPDATE_CACHE_DIR`
  and `INSTALL_DIR`).

- Re-run `repo_init.py` and `repo_add_bundle.py`.

Links and references

- `tufup`: <https://github.com/dennisvang/tufup>
- `tufup-example`: <https://github.com/dennisvang/tufup-example>
- TUF (The Update Framework): <https://theupdateframework.io/>
- PyInstaller: <https://pyinstaller.org/en/stable/>
- rclone: <https://rclone.org/>

If you have questions or encounter issues, check the project issues/discussions.
