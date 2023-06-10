"""Helper functions for cogs"""
import logging
from typing import Sequence

import discord as dis
import sqlalchemy.ext.asyncio as sqlaio

from lisette.core import models
from lisette.core.collections import MsgUpdate
from lisette.core.database import SESSION
from lisette.lib import util

log = logging.getLogger(__name__)

CHECKED_PREFIX = "!"


async def respond_all(ctx: dis.ApplicationContext, msgs: list[str]) -> None:
    """Respond with a list of messages"""
    for msg in msgs:
        await ctx.respond(content=msg, ephemeral=True)


async def get_lists_info(guild_id: int, guild_name: str) -> list[str]:
    """Return list of strs that are msgs describing lists in a guild"""
    msgs: list[str] = [f"Lists in guild {guild_name}:"]
    async with SESSION() as session:
        lsts: Sequence[models.TaskList] = await models.TaskList.guild_all(
            session, guild_id
        )
        if len(lsts) == 0:
            msgs.append("None")
            return ["/n".join(msgs)]
        for lst in lsts:
            msgs.append(f"{lst.id}: '{lst.name}'")
    return util.split_len("\n".join(msgs))


async def mk_list(guild_id: int, name: str, msg_id: int) -> str:
    """Make a new list"""
    async with SESSION() as session:
        lst = models.TaskList(name=name, guild_id=guild_id, msg_id=msg_id)
        session.add(lst)
        msg = lst.pretty_print()
        await session.commit()
    return msg


async def del_list(guild_id: int, name: str) -> int:
    """Delete a list"""
    async with SESSION() as session:
        lst = await models.TaskList.lookup(session, guild_id, name)
        msg_id = lst.msg_id
        await session.delete(lst)
        await session.commit()
    return msg_id


async def get_tasks_info(guild_id: int, name: str) -> list[str]:
    """Returns formatted list info."""
    msgs: list[str] = [f"Tasks in {name}:"]
    async with SESSION() as sess:
        lst = await models.TaskList.lookup(sess, guild_id, name)
        tasks: Sequence[models.Task] = await lst.awaitable_attrs.tasks
        for task in tasks:
            msgs.append(f"{task.local_id}: '{task.content}', checked={task.checked}")

    return util.split_len("\n".join(msgs))


async def mk_task(guild_id: int, list_name: str, content: str) -> MsgUpdate:
    """Make new task, returning list msg id and new list txt"""
    async with SESSION() as sess:
        lst: models.TaskList = await models.TaskList.lookup(sess, guild_id, list_name)
        tsk: models.Task = models.Task(content=content)
        lst.insert(tsk)
        out = MsgUpdate(lst.msg_id, lst.pretty_print())
        await sess.commit()
    return out


async def del_tasks(guild_id: int, list_name: str, *positions: int) -> MsgUpdate:
    """Delete a task."""
    if min(positions) < 0:
        raise ValueError(f"Invalid minimum position {min(positions)}. Must be > 0.")
    async with SESSION() as sess:
        lst: models.TaskList = await models.TaskList.lookup(sess, guild_id, list_name)
        tasks: Sequence[models.Task] = await lst.awaitable_attrs.tasks
        max_pos = len(tasks) - 1
        if max(positions) > max_pos:
            raise ValueError(
                f"Invalid max position {max(positions)}. Must be < {max_pos}"
            )

        # Delete each task[pos] for pos is positions
        # convert to set to avoid duplicates
        for pos in set(positions):
            log.debug("del task pos: %s", pos)
            await tasks[pos].delete(sess)

        await sess.commit()
        await sess.refresh(lst)
        out = MsgUpdate(lst.msg_id, lst.pretty_print())
        await sess.commit()
    return out


async def check_tasks(guild_id: int, list_name: str, *positions: int) -> MsgUpdate:
    """Set tasks as checked."""
    log.debug("got positions: %r", positions)
    if min(positions) < 0:
        raise ValueError(f"Invalid minimum position {min(positions)}. Must be > 0.")
    async with SESSION() as sess:
        lst: models.TaskList = await models.TaskList.lookup(sess, guild_id, list_name)
        tasks: Sequence[models.Task] = await lst.awaitable_attrs.tasks
        max_pos = len(tasks) - 1
        if max(positions) > max_pos:
            raise ValueError(
                f"Invalid max position {max(positions)}. Must be < {max_pos}"
            )
        # Invert checked for tasks with pos in positions
        # convert to set to avoid duplicates
        for pos in set(positions):
            log.debug("inverting %r.checked", tasks[pos])
            tasks[pos].checked = not tasks[pos].checked
            log.debug("now %r", tasks[pos])

        out = MsgUpdate(lst.msg_id, lst.pretty_print())
        log.debug("sess changes %s", sess.dirty)
        await sess.commit()
    return out


async def get_edit_txt(guild_id: int, list_name: str) -> str:
    async with SESSION() as session:
        lst = await models.TaskList.lookup(session, guild_id, list_name)
        tasks = await lst.awaitable_attrs.tasks
        full_txt = []
        for task in tasks:
            log.debug("working on: '%s', '%s'", task.content, task.checked)
            txt = f"{CHECKED_PREFIX}{task.content}" if task.checked else task.content
            log.debug("made text %s", txt)
            full_txt.append(txt)
        log.debug("made full text: %s", full_txt)
        return "\n".join(full_txt)


def put_line(line: str) -> models.Task:
    tsk = models.Task("")
    log.debug("working on '%s'", line)
    if line.startswith(CHECKED_PREFIX):
        tsk.checked = True
    tsk.content = line.removeprefix(CHECKED_PREFIX)
    log.debug("made task %r", tsk)
    return tsk


async def put_edit(guild_id: int, list_name: str, full_txt: str) -> MsgUpdate:
    async with SESSION() as session:
        lst = await models.TaskList.lookup(session, guild_id, list_name)
        await lst.clear(session)
        for line in full_txt.splitlines():
            task = put_line(line)
            lst.insert(task)
        await session.commit()
        await session.refresh(lst)
        update_msg = MsgUpdate(lst.msg_id, lst.pretty_print())
    return update_msg
