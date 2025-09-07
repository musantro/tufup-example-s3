import logging
import shutil
from tufup.client import Client

from myapp import settings


def main():
    # The app must ensure dirs exist
    for dir_path in [settings.INSTALL_DIR, settings.METADATA_DIR, settings.TARGET_DIR]:
        dir_path.mkdir(exist_ok=True, parents=True)

    # The app must be shipped with a trusted "root.json" metadata file,
    # which is created using the tufup.repo tools. The app must ensure
    # this file can be found in the specified metadata_dir. The root metadata
    # file lists all trusted keys and TUF roles.
    if not settings.TRUSTED_ROOT_DST.exists():
        shutil.copy(src=settings.TRUSTED_ROOT_SRC, dst=settings.TRUSTED_ROOT_DST)
        logger.info('Trusted root metadata copied to cache.')

    client = Client(
        app_name=settings.APP_NAME,
        app_install_dir=settings.INSTALL_DIR,
        current_version=settings.APP_VERSION,
        metadata_dir=settings.METADATA_DIR,
        metadata_base_url=settings.METADATA_BASE_URL,
        target_dir=settings.TARGET_DIR,
        target_base_url=settings.TARGET_BASE_URL,
        refresh_required=False,
    )

    pre = None

    # Perform update
    client.check_for_updates(pre=pre)
    # [optional] use custom metadata, if available
    # apply the update
    client.download_and_apply_update(
        # WARNING: Be very careful with `purge_dst_dir=True`, because
        # this will *irreversibly* delete *EVERYTHING* inside the
        # `app_install_dir`, except any paths specified in
        # `exclude_from_purge`. So, *ONLY* use `purge_dst_dir=True` if
        # you are absolutely certain that your `app_install_dir` does not
        # contain any unrelated content.
        skip_confirmation=True,  # You are agreeing to setup if you launch setup.exe!
        purge_dst_dir=False,
        exclude_from_purge=None,
        log_file_name='install.log',
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    main()
