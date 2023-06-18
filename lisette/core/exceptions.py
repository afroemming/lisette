class LisetteError(Exception):
    """Base exception for Lisette."""


class CancelledError(LisetteError):
    """User cancelled interaction."""
