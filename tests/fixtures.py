# pylint: skip-file
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
import logging

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from lisette.core import database, models
from lisette.core.database import SESSION


@pytest.fixture()
async def dbglog(caplog):
    caplog.set_level(logging.DEBUG, logger="lisette")
    caplog.set_level(logging.DEBUG, logger="sqlalchemy.engine")


@pytest.fixture()
async def db_session():
    """
    Get a database session
    """
    engine = await database.initalize("")
    session = SESSION()
    yield session
    await session.rollback()
    await session.close()
    await engine.dispose()


@pytest.fixture
async def task_list():
    lst = models.TaskList("list 1", 0, msg_id=0)
    lst.insert(models.Task("do something"))
    lst.insert(models.Task("do something else"))
    lst.insert(models.Task("do a third thing"))

    return lst


@pytest.fixture
async def task_lists():
    lsts = (
        models.TaskList("list 1", 0, msg_id=0),
        models.TaskList("list 2", 0, msg_id=0),
        models.TaskList("list 3", 1, msg_id=0),
    )
    return lsts
