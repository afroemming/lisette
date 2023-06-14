# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
import pytest
import sqlalchemy as sql
import sqlalchemy.exc as sqlexc
from sqlalchemy.ext.asyncio import AsyncSession

import lisette.core.database as database
import lisette.core.models as models
import lisette.cogs.helpers as helpers
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

@pytest.fixture
async def get_lsts(db_session) -> tuple[models.TaskList, models.TaskList]:
    lsts = models.TaskList('test 0', 7, msg_id=8), models.TaskList('test 1', 7, msg_id=9)
    tsks0 = (models.Task('do a'),
                models.Task('do b'),
                models.Task('do c'),
                models.Task('do d'),)
    tsks1 = (models.Task('do a'), models.Task('do b'))
    lsts[0].insert_all(*tsks0)
    lsts[1].insert_all(*tsks1)
    db_session.add_all(lsts)
    await db_session.commit()
    await db_session.refresh(lsts[0])
    await db_session.refresh(lsts[1])
    yield lsts


class TestNumbering:
    async def test_base(self, get_lsts) -> None:
        tsks0 = await get_lsts[0].awaitable_attrs.tasks
        tsks1 = await get_lsts[1].awaitable_attrs.tasks

        assert tsks0[0].local_id == 0
        assert tsks0[1].local_id == 1
        assert tsks0[2].local_id == 2

        assert tsks1[0].local_id == 0
        assert tsks1[1].local_id == 1

    async def test_edit(self, get_lsts) -> None:
        edit = "do a\n" "do b\n" "do e\n"
        await helpers.put_edit(7, 'test 0', edit)

        tsks0 = await get_lsts[0].awaitable_attrs.tasks
        tsks1 = await get_lsts[1].awaitable_attrs.tasks

        assert tsks0[0].local_id == 0
        assert tsks0[1].local_id == 1
        assert tsks0[2].local_id == 2

        assert tsks1[0].local_id == 0
        assert tsks1[1].local_id == 1


        