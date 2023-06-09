"""Various useful collections."""
from typing import NamedTuple


class MsgUpdate(NamedTuple):
    """Tuple holding new content for a message"""

    id: int
    content: str
