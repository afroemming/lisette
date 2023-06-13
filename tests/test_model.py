# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
import pytest
import sqlalchemy as sql
import sqlalchemy.exc as sqlexc
from sqlalchemy.ext.asyncio import AsyncSession

import lisette.core.database as database
import lisette.core.models as models
from lisette.core.database import SESSION
from tests.fixtures import db_session, task_list, task_lists


async def test_lookup_task_list(db_session: AsyncSession, task_list: models.TaskList) -> None:
    db_session.add(task_list)
    await db_session.commit()
    lst = await models.TaskList.lookup(db_session, 0, "list 1")
    assert lst.name == "list 1"


async def test_lookup_task(db_session: AsyncSession, task_list) -> None:
    db_session.add(task_list)
    await db_session.commit()
    tsk = await models.Task.lookup(db_session, 0, "list 1", 0)
    assert tsk.content == "do something"


async def test_task_pretty_txt() -> None:
    tsk = models.Task(content="do something")
    answer = "☐  {0}\n".format("do something")
    assert tsk.pretty_txt() == answer


async def test_too_long_task_raises(
    db_session: AsyncSession, task_list: models.TaskList
) -> None:
    db_session.add(task_list)
    await db_session.commit()
    lst = await models.TaskList.lookup(db_session, 0, "list 1")
    tsk = models.Task("hi" * 3000)
    try:
        with pytest.raises(ValueError):
            await lst.insert(tsk)
    except:
        await db_session.rollback()


async def test_delete_task(db_session: AsyncSession, task_list: models.TaskList) -> None:
    db_session.add(task_list)
    await db_session.commit()
    tsk = await models.Task.lookup(db_session, 0, "list 1", 1)
    await tsk.delete(db_session)
    await db_session.commit()
    tsk1 = await models.Task.lookup(db_session, 0, "list 1", 1)
    assert tsk1.content == "do a third thing"


async def test_guild_all(db_session: AsyncSession, task_lists: tuple[models.TaskList]) -> None:
    db_session.add_all(task_lists)
    await db_session.commit()
    lsts = await models.TaskList.guild_all(db_session, 0)
    names = [lst.name for lst in lsts]
    assert "list 1" in names
    assert "list 2" in names
    assert not "list 3" in names

async def test_guild_all_names(db_session: AsyncSession, task_lists: tuple[models.TaskList]) -> None:
    db_session.add_all(task_lists)
    await db_session.commit()
    names = await models.TaskList.guild_all_names(db_session, 0)
    assert "list 1" in names
    assert "list 2" in names
    assert not "list 3" in names