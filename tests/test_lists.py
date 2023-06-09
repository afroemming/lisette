# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
# pylint: skip-file
import pytest
import sqlalchemy.exc as sqlexc
from tests.fixtures import db_session, task_lists, task_list
from lisette.cogs.lists import *
from lisette.core import models


async def test_info_get(db_session, task_lists):
    task_lists[0].id = 5
    task_lists[1].id = 6
    db_session.add_all(task_lists)
    await db_session.commit()
    correct = "Lists in guild 0:\n" "5: list 1\n" "6: list 2\n"
    answer = await Lists.info_get(0, "...")
    assert answer == correct


async def test_new_do(db_session):
    await Lists.new_do("test new", 6, 7)
    lst = await models.TaskList.lookup(db_session, 7, "test new")
    assert lst.name == "test new"
    assert lst.msg_id == 6
    assert lst.guild_id == 7


async def test_del_do(db_session, task_list):
    db_session.add(task_list)
    await db_session.commit()
    msg_id = await Lists.del_do("list 1", 0)
    assert msg_id == 0
    with pytest.raises(sqlexc.NoResultFound):
        await models.TaskList.lookup(db_session, 0, "list 1")
