"""Helper functions for cogs"""
import logging
from typing import Sequence

import discord as dis
import sqlalchemy.exc as sqlexc
import sqlalchemy.ext.asyncio as sqlaio

from lisette.core import models
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
        lsts: Sequence[models.TaskList] = await models.TaskList.lookup(
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
        if await is_name_in_guild(session, guild_id, name):
            raise ValueError("Name is already used for a list in this guild.")
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
        tasks: Sequence[models.Task] = lst.tasks
        for task in tasks:
            msgs.append(f"{task.local_id}: '{task.content}', checked={task.checked}")

    return util.split_len("\n".join(msgs))


async def mk_task(guild_id: int, list_name: str, content: str) -> str:
    """Make new task, returning list msg id and new list txt"""
    async with SESSION() as sess:
        lst: models.TaskList = await models.TaskList.lookup(sess, guild_id, list_name)
        tsk: models.Task = models.Task(content=content)
        lst.insert(tsk)
        out = lst.pretty_print()
        await sess.commit()
    return out


async def del_tasks(
    guild_id: int, list_name: str, *positions: int
) -> tuple[list[int], list[int], str]:
    """Delete a task."""
    if min(positions) < 0:
        raise ValueError(f"Invalid minimum position {min(positions)}. Must be > 0.")
    async with SESSION() as sess:
        lst: models.TaskList = await models.TaskList.lookup(sess, guild_id, list_name)
        deleted: list[int] = []
        ignored: list[int] = []
        # Delete each task[pos] for pos is positions
        # convert to set to avoid duplicates
        for pos in sorted(set(positions), reverse=True):
            log.debug("del task pos: %s", pos)
            try:
                del lst.tasks[pos]
            except IndexError:
                ignored.append(pos)
                continue
            deleted.append(pos)
            lst.renumber()

        await sess.commit()
        await sess.refresh(lst)
        update = lst.pretty_print()
        out = (deleted, ignored, update)
        await sess.commit()
    return out


async def check_tasks(guild_id: int, list_name: str, *positions: int) -> str:
    """Set tasks as checked."""
    log.debug("got positions: %r", positions)
    if min(positions) < 0:
        raise ValueError(f"Invalid minimum position {min(positions)}. Must be > 0.")
    async with SESSION() as session:
        lst: models.TaskList = await models.TaskList.lookup(
            session, guild_id, list_name
        )
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

        out = lst.pretty_print()
        log.debug("sess changes %s", session.dirty)
        await session.commit()
    return out


async def get_edit_txt(guild_id: int, list_name: str) -> str:
    async with SESSION() as session:
        lst = await models.TaskList.lookup(session, guild_id, list_name)
        full_txt = lst.encode_tasks()
        return full_txt


async def put_edit(guild_id: int, list_name: str, full_txt: str) -> str:
    async with SESSION() as session:
        tasks = models.Task.decode_many(full_txt)
        lst = await models.TaskList.lookup(session, guild_id, list_name)
        lst.tasks = tasks
        update_msg = lst.pretty_print()
        await session.commit()
    return update_msg


async def put_list_edit(guild_id: int, name: str, new_name: str) -> str:
    """Edit a list name, returning new list text."""
    async with SESSION() as session:
        names: Sequence[str] = await models.TaskList.lookup(
            session, guild_id, attr="name"
        )
        if new_name in names:
            raise ValueError("New name is already used.")
        lst = await models.TaskList.lookup(session, guild_id, name)
        lst.name = new_name
        await session.commit()
        update_msg = lst.pretty_print()
    return update_msg


async def is_name_in_guild(
    session: sqlaio.AsyncSession, guild_id: int, name: str
) -> bool:
    names: Sequence[str] = await models.TaskList.lookup(session, guild_id, attr="name")
    return name in names


async def get_list_names(ctx: dis.AutocompleteContext) -> list[str]:
    assert ctx.interaction.guild is not None
    guild_id = ctx.interaction.guild.id
    async with SESSION() as session:
        names: list[str] = list(
            await models.TaskList.lookup(session, guild_id, attr="name")
        )
        return names


async def del_checked(guild_id: int, name: str) -> str:
    async with SESSION() as session:
        lst = await models.TaskList.lookup(session, guild_id, name)
        lst.tasks = [t for t in lst.tasks if not t.checked]

        lst.renumber()
        await session.commit()
        update = lst.pretty_print()
        return update


async def get_list_msg(ctx: dis.ApplicationContext, name: str) -> dis.Message:
    async with SESSION() as session:
        id: int = await models.TaskList.lookup(
            session, ctx.guild_id, name, attr="msg_id"
        )
    return await ctx.fetch_message(id)


autocomplete_list = autocomplete = dis.utils.basic_autocomplete(get_list_names)
