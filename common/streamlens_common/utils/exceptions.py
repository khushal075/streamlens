class StreamLensError(Exception):
    """Base class for all StreamLens exceptions."""
    pass

class IngestionError(StreamLensError):
    """Raised when a log fails initial validation."""
    pass

class StorageError(StreamLensError):
    """Raised when ClickHouse or Redis is unreachable."""
    pass