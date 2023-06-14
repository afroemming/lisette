# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
# pylint: skip-file
import asyncio
import logging
from pprint import pprint

import pytest
import sqlalchemy as sql
import sqlalchemy.exc as sqlexc
import sqlalchemy.ext.asyncio as sqlaio

from lisette.cogs import helpers
from lisette.core import models
from lisette.core.collections import MsgUpdate
from tests.fixtures import db_session, dbglog, task_list, task_lists


async def test_mk_list(db_session: sqlaio.AsyncSession) -> None:
    txt: str = await helpers.mk_list(0, "test", 55)
    lst: models.TaskList = await models.TaskList.lookup(db_session, 0, "test")
    assert lst.name == "test"
    assert lst.guild_id == 0
    assert lst.msg_id == 55
    assert txt == "**test**\n"


async def test_del_list(db_session: sqlaio.AsyncSession, task_lists) -> None:
    db_session.add_all(task_lists)
    await db_session.commit()
    await helpers.del_list(0, "list 1")
    with pytest.raises(sqlexc.NoResultFound):
        await models.TaskList.lookup(db_session, 0, "list 1")
    await models.TaskList.lookup(db_session, 0, "list 2")
    await models.TaskList.lookup(db_session, 1, "list 3")


async def test_mk_task(db_session: sqlaio.AsyncSession) -> None:
    lst = models.TaskList("list 1", 0, msg_id=99)
    db_session.add(lst)
    await db_session.commit()

    await helpers.mk_task(0, "list 1", "do a")
    await helpers.mk_task(0, "list 1", "do b")
    up = await helpers.mk_task(0, "list 1", "do c")

    tsks: list[models.Task] = [
        await models.Task.lookup(db_session, 0, "list 1", 0),
        await models.Task.lookup(db_session, 0, "list 1", 1),
        await models.Task.lookup(db_session, 0, "list 1", 2),
    ]
    assert tsks[0].content == "do a"
    assert tsks[1].content == "do b"
    assert tsks[2].content == "do c"

    correct = "".join(
        (
            "**list 1**\n",
            models.Task.UNCHECKED_FRMT.format("do a"),
            models.Task.UNCHECKED_FRMT.format("do b"),
            models.Task.UNCHECKED_FRMT.format("do c"),
        )
    )

    assert up.id == 99
    assert up.content == correct


async def test_chk_task_one(
    db_session: sqlaio.AsyncSession, task_list: models.TaskList
) -> None:
    db_session.add(task_list)
    await db_session.commit()
    # must close to avoid using in memory objects that do not reflect db state
    # when checking
    await db_session.close()
    lst_name = "list 1"
    up: MsgUpdate = await helpers.check_tasks(0, lst_name, 1)

    tsks: list[models.Task] = [
        await models.Task.lookup(db_session, 0, lst_name, 0),
        await models.Task.lookup(db_session, 0, lst_name, 1),
        await models.Task.lookup(db_session, 0, lst_name, 2),
    ]
    pprint(tsks)

    assert tsks[0].checked == False
    assert tsks[1].checked == True
    assert tsks[2].checked == False

    correct = "".join(
        (
            "**list 1**\n",
            models.Task.UNCHECKED_FRMT.format("do something"),
            models.Task.CHECKED_FRMT.format("do something else"),
            models.Task.UNCHECKED_FRMT.format("do a third thing"),
        )
    )

    assert up.id == 0
    assert up.content == correct


async def test_del_task_one(db_session, task_list, dbglog) -> None:
    db_session.add(task_list)
    await db_session.commit()
    await db_session.close()

    list_name = "list 1"

    status = await helpers.del_tasks(0, "list 1", 1)
    up = status[2]

    lst: models.TaskList = await models.TaskList.lookup(db_session, 0, "list 1")
    tasks: list[models.Task] = await lst.awaitable_attrs.tasks

    assert tasks[0].local_id == 0
    assert tasks[0].content == "do something"
    assert tasks[1].local_id == 1
    assert tasks[1].content == "do a third thing"
    with pytest.raises(IndexError):
        tasks[2]

    correct = "".join(
        [
            "**list 1**\n",
            models.Task.UNCHECKED_FRMT.format("do something"),
            models.Task.UNCHECKED_FRMT.format("do a third thing"),
        ]
    )
    assert up.id == 0
    assert up.content == correct


async def test_chk_task_many(db_session, task_list) -> None:
    db_session.add(task_list)
    await db_session.commit()
    await db_session.close()

    update: MsgUpdate = await helpers.check_tasks(0, "list 1", 0, 1, 2)

    lst: models.TaskList = await models.TaskList.lookup(db_session, 0, "list 1")
    tasks: list[models.Task] = await lst.awaitable_attrs.tasks

    assert tasks[0].checked
    assert tasks[1].checked
    assert tasks[2].checked

    correct = "".join(
        (
            "**list 1**\n",
            models.Task.CHECKED_FRMT.format("do something"),
            models.Task.CHECKED_FRMT.format("do something else"),
            models.Task.CHECKED_FRMT.format("do a third thing"),
        )
    )

    assert update.id == 0
    assert update.content == correct


async def test_del_task_many(db_session, task_list, dbglog) -> None:
    db_session.add(task_list)
    await db_session.commit()
    await db_session.close()

    status: MsgUpdate = await helpers.del_tasks(0, "list 1", 0, 1, 2)
    update = status[2]
    lst: models.TaskList = await models.TaskList.lookup(db_session, 0, "list 1")
    tasks: list[models.Task] = await lst.awaitable_attrs.tasks

    assert len(tasks) == 0

    correct = "".join(("**list 1**\n",))

    assert update.id == 0
    assert update.content == correct


async def test_get_edit_txt(db_session, task_list):
    task_list.tasks[0].checked = True
    db_session.add(task_list)
    pprint(task_list)
    await db_session.commit()
    await db_session.close()

    answer = await helpers.get_edit_txt(0, "list 1")
    print(answer)
    correct = "!do something\n" "do something else\n" "do a third thing"

    assert answer == correct


async def test_put_line(db_session, dbglog):
    full_txt = "!do a\n" "do b\n" "do c"
    tasks = []
    for line in full_txt.splitlines():
        task = helpers.put_line(line)
        tasks.append(task)

    assert tasks[0].content == "do a"
    assert tasks[1].content == "do b"
    assert tasks[2].content == "do c"

    assert tasks[0].checked
    assert not tasks[1].checked
    assert not tasks[2].checked


async def test_put_edit(db_session, task_list, dbglog):
    db_session.add(task_list)
    await db_session.commit()
    await db_session.close()

    full_text = "!do a\n" "do b\n" "do c"
    update = await helpers.put_edit(0, "list 1", full_text)

    assert update.id == 0
    assert update.content == "".join(
        [
            "**list 1**\n",
            models.Task.CHECKED_FRMT.format("do a"),
            models.Task.UNCHECKED_FRMT.format("do b"),
            models.Task.UNCHECKED_FRMT.format("do c"),
        ]
    )

    lst = await models.TaskList.lookup(db_session, 0, "list 1")
    tasks = await lst.awaitable_attrs.tasks
    assert tasks[0].checked
    assert not tasks[1].checked
    assert not tasks[2].checked
    assert tasks[0].content == "do a"
    assert tasks[1].content == "do b"
    assert tasks[2].content == "do c"

async def is_name_in_guild(db_session, task_lists):
    db_session.add_all(task_lists)
    await db_session.commit()
    await db_session.close()

    assert (await helpers.is_name_in_guild(db_session, 0, 'list 1'))
    assert (await helpers.is_name_in_guild(db_session, 0, 'list 2'))
    assert not (await helpers.is_name_in_guild(db_session, 0, 'aaaaa'))

async def test_put_list_edit(db_session, task_lists):
    db_session.add_all(task_lists)
    await db_session.commit()
    await db_session.close()

    await helpers.put_list_edit(0, 'list 1', 'list a')
    lsts = await models.TaskList.guild_all(db_session, 0)
    names = [x.name for x in lsts]

    assert 'list a' in names
    assert 'list 2' in names
    assert not 'list 1' in names
