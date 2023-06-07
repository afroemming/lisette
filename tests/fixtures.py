# pylint: skip-file
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
import pytest
from lisette.core import database
from lisette.core import models
from lisette.core.database import SESSION
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture()
async def db_session():
    """
    Get a database session
    """
    await database.initalize("")
    session = SESSION()
    yield session
    await session.rollback()
    await session.close()


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
