from __future__ import annotations

import os
from logging import getLogger
from pathlib import Path

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

LOG = getLogger(__name__)


def get_auth() -> GoogleAuth:
    """Authenticate with Google Drive using local or service credentials.

    Returns:
        An authenticated GoogleAuth instance.

    """
    if Path("settings.yaml").exists():
        LOG.info("Using settings.yaml")
        auth = GoogleAuth("settings.yaml")
        auth.LocalWebserverAuth()
    else:
        if not Path("service-secrets.json").exists():
            service_secrets = os.environ.get("GDRIVE_SERVICE_SECRETS")
            if service_secrets is not None:
                LOG.info("Using GDRIVE_SERVICE_SECRETS")
                Path("service-secrets.json").write_text(service_secrets, encoding="utf-8")
            else:
                LOG.info("Using default settings")
                auth = GoogleAuth()
                auth.LocalWebserverAuth()
                return auth
        LOG.info("Using service-secrets.json")
        auth = GoogleAuth(
            settings={
                "client_config_backend": "service",
                "service_config": {
                    "client_json_file_path": "service-secrets.json",
                },
            }
        )
        auth.ServiceAuth()
    return auth


def get_drive() -> GoogleDrive:
    """Create an authenticated Google Drive client.

    Returns:
        An authenticated GoogleDrive instance.

    """
    return GoogleDrive(get_auth())
