# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Provides database setup and access helper functions"""
import logging

import sqlalchemy.ext.asyncio as sqlaio

from lisette.core import models

log = logging.getLogger(__name__)

SESSION: sqlaio.async_sessionmaker[sqlaio.AsyncSession] = sqlaio.async_sessionmaker(
    expire_on_commit=False
)
ENGINE: sqlaio.AsyncEngine | None = None


async def initalize(path: str, debug: bool = False) -> sqlaio.AsyncEngine:
    """Make connection manager to database at a path.

    Path is of the style ('/path'), that is, prefixed with a /.
    """
    if debug:
        sql_log = logging.getLogger("sqlalchemy.engine")
        sql_log.setLevel(logging.DEBUG)
    url = "".join(("sqlite+aiosqlite://", path))
    global ENGINE  # pylint: disable=global-statement
    ENGINE = sqlaio.create_async_engine(url)
    SESSION.configure(bind=ENGINE)

    async with ENGINE.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    return ENGINE
