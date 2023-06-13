# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Module with commands for manipulating lists."""
import logging

import discord as dis
import discord.ext.commands as disc
import sqlalchemy.exc as sqlexc

from lisette.cogs import helpers
from lisette.core.bot import Bot
from lisette.core.collections import MsgUpdate
from lisette.core import modals
from lisette.lib import util

log = logging.getLogger(__name__)


class TasksCog(disc.Cog):
    """Tasks cog class"""

    tasks_grp = dis.SlashCommandGroup(
        "tasks", description="Commands for manipulating tasks."
    )

    def __init__(self, bot_: Bot):
        log.info("Adding cog 'tasks'")
        self.bot = bot_

    @tasks_grp.command(description="Edit all of a list tasks in a pop-up dialog")  # type: ignore
    @dis.guild_only()  # type: ignore
    @dis.option("name", str, help="List to edit tasks of.", autocomplete=helpers.autocomplete_list)  # type: ignore
    async def edit(self, ctx: dis.ApplicationContext, name):
        if ctx.guild is None:
            await ctx.respond("Inappropriate context")
            return
        try:
            txt = await helpers.get_edit_txt(ctx.guild.id, name)
        except sqlexc.NoResultFound as exc:
            msg = f"Can't find list '{name}' in '{ctx.guild.name}'"
            log.warning("Lookup failed, guild %s, name %s", ctx.guild.id, name)
            await ctx.respond(content=msg, ephemeral=True)
            return

        modal = modals.TasksEdit(
            title=f"Edit '{name}'", txt=txt, list_name=name
        )
        await ctx.send_modal(modal)

    @tasks_grp.command()
    @dis.guild_only()  # type: ignore
    @dis.option("name", str, description="Name of list to print task info for", autocomplete=helpers.autocomplete_list)  # type: ignore
    async def info(self, ctx: dis.ApplicationContext, name: str) -> None:
        """Print info about a list and it's tasks."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild.")
        try:
            msgs: list[str] = await helpers.get_tasks_info(ctx.guild.id, name)
        except sqlexc.NoResultFound:
            log.warning("Lookup failed, guild %s, name %s", ctx.guild.id, name)
            await ctx.respond(f"Couldn't find list {name}", ephemeral=True)
            return
        for msg in msgs:
            await ctx.respond(msg, ephemeral=True)

    @tasks_grp.command(description="Add a new task to a list")
    @dis.guild_only()  # type: ignore
    @dis.option("name", str, description="Name of list to add task to.", autocomplete=helpers.autocomplete_list)  # type: ignore
    @dis.option("content", str, description="Text to put with task.")  # type: ignore
    async def new(
        self, ctx: dis.ApplicationContext, name: str, content: str
    ) -> None:
        """Add a new task to a list"""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild.")
        try:
            msg_update: MsgUpdate = await helpers.mk_task(
                ctx.guild.id, name, content
            )
        except sqlexc.NoResultFound:
            log.warning("Lookup failed, guild %s, name %s", ctx.guild.id, name)
            await ctx.respond(f"Couldn't find list {name}", ephemeral=True)
            return
        msg = await ctx.fetch_message(msg_update.id)
        await msg.edit(content=msg_update.content)
        await ctx.respond("Task added :-)", ephemeral=True)

    @tasks_grp.command(name="del")
    @dis.guild_only()  # type: ignore
    @dis.option('name', str, description='Name of list to delete tasks from', autocomplete=helpers.autocomplete_list) # type: ignore
    @dis.option(
        "positions",
        str,
        help="A whitespace seperated list of integers. Ie.: '1 2 3'. Indexed from zero",
    )  # type: ignore
    async def del_(
        self, ctx: dis.ApplicationContext, name: str, positions: str
    ) -> None:
        """Delete a task."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild.")

        try:
            local_ids: list[int] = util.split_int(positions)
        except ValueError:
            await ctx.respond("Invalid argument :-(", ephemeral=True)
            return

        try:
            await helpers.del_tasks(ctx.guild.id, name, *local_ids)
        except sqlexc.NoResultFound:
            log.warning(
                "Lookup failed, guild %s, name %s, pos %s",
                ctx.guild.id,
                name,
                local_ids,
            )
            await ctx.respond(
                f"Couldn't find task in {name} w/ positions {local_ids}"
            )
            return
        await ctx.respond("Task deleted :-)")

    @tasks_grp.command()
    @dis.guild_only()  # type: ignore
    @dis.option(
        "positions",
        str,
        help="A whitespace seperated list of integers. Ie.: '1 2 3'. Indexed from zero",
    )  # type: ignore
    @dis.option('name', str, description='Name of list to check tasks on.', autocomplete=helpers.autocomplete_list) # type: ignore
    async def chk(
        self, ctx: dis.ApplicationContext, name: str, positions: str
    ) -> None:
        """Check or uncheck tasks with given positions"""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild.")

        try:
            local_ids: list[int] = util.split_int(positions)
        except ValueError:
            await ctx.respond("Invalid argument :-(", ephemeral=True)
            return

        try:
            msg_update: MsgUpdate = await helpers.check_tasks(
                ctx.guild.id, name, *local_ids
            )
        except ValueError as exc:
            log.warning("Caught exception", exc_info=exc)
            await ctx.respond(str(exc.args[0]), ephemeral=True)
            return

        msg: dis.Message = await ctx.fetch_message(msg_update.id)
        await msg.edit(content=msg_update.content)
        await ctx.respond("List updated :-)", ephemeral=True)
