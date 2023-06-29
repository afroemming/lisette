# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
import pytest
import sqlalchemy as sql
import sqlalchemy.exc as sqlexc
from sqlalchemy.ext.asyncio import AsyncSession

import lisette.core.database as database
import lisette.core.models as models
# import lisette.cogs.helpers as helpers
from lisette.core.database import SESSION
from lisette.core import exceptions
from tests.fixtures import db_session, task_list, task_lists


async def test_lookup_task_list(
    db_session: AsyncSession, task_list: models.TaskList
) -> None:
    db_session.add(task_list)
    await db_session.commit()
    await db_session.close()

    lst = await models.TaskList.lookup(db_session, 0, "list 1")
    assert lst.name == "list 1"


async def test_lookup_task(db_session: AsyncSession, task_list) -> None:
    db_session.add(task_list)
    await db_session.commit()
    await db_session.close()

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
    await db_session.close()

    lst = await models.TaskList.lookup(db_session, 0, "list 1")
    tsk = models.Task("hi" * 3000)
    try:
        with pytest.raises(ValueError):
            await lst.insert(tsk)
    except:
        await db_session.rollback()


async def test_guild_all(
    db_session: AsyncSession, task_lists: tuple[models.TaskList]
) -> None:
    db_session.add_all(task_lists)
    await db_session.commit()
    await db_session.close()

    lsts = await models.TaskList.lookup(db_session, 0)
    names = [lst.name for lst in lsts]
    assert "list 1" in names
    assert "list 2" in names
    assert not "list 3" in names


async def test_guild_all_names(
    db_session: AsyncSession, task_lists: tuple[models.TaskList]
) -> None:
    db_session.add_all(task_lists)
    await db_session.commit()
    await db_session.close()

    names = await models.TaskList.lookup(db_session, 0, attr="name")
    assert "list 1" in names
    assert "list 2" in names
    assert not "list 3" in names


@pytest.fixture
async def get_lsts(db_session) -> tuple[models.TaskList, models.TaskList]:
    lsts = models.TaskList("test 0", 7, msg_id=8), models.TaskList(
        "test 1", 7, msg_id=9
    )
    tsks0 = (
        models.Task("do a"),
        models.Task("do b"),
        models.Task("do c"),
        models.Task("do d"),
    )
    tsks1 = (models.Task("do a"), models.Task("do b"))
    lsts[0].insert_all(*tsks0)
    lsts[1].insert_all(*tsks1)
    db_session.add_all(lsts)
    await db_session.commit()
    await db_session.refresh(lsts[0])
    await db_session.refresh(lsts[1])
    yield lsts

class TestEncoding:
    def test_task_reversible(self):
        txt = '! do a'
        tsk = models.Task.decode(txt)
        ans = tsk.encode()
        assert ans == txt

    def test_no_meta(self):
        content = 'do a'
        tsk = models.Task.decode(content)
        assert not tsk.checked
        assert tsk.content == content

    def test_many_inverts(self):
        txt = ('do a\n'
               'do b\n'
               '!do c')
        tasks = models.Task.decode_many(txt)
        lst = models.TaskList('list', 0, tasks, 0)
        ans = lst.encode_tasks()
        assert ans == txt

    def test_escape_inverts(self):
        txt = r'\!do a'
        tsk = models.Task.decode(txt)
        ans = tsk.encode()
        assert txt == ans