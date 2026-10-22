"""Pick where the app reads tickets and articles from, using the DATA_SOURCE setting."""

from src import config
from src.connectors.base import DataSource


def get_data_source(name: str | None = None) -> DataSource:
    name = (name or config.DATA_SOURCE).lower()
    if name == "local":
        from src.connectors.local_files import LocalFilesSource
        return LocalFilesSource()
    if name == "google":
        from src.connectors.google_drive import GoogleDriveSource
        return GoogleDriveSource()
    if name == "hubspot":
        from src.connectors.hubspot import HubSpotSource
        return HubSpotSource()
    raise ValueError(f"Unknown DATA_SOURCE '{name}'. Use local, google or hubspot.")
