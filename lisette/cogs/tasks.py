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
from lisette.lib import util

log = logging.getLogger(__name__)


class TasksCog(disc.Cog):
    """Tasks cog class"""

    tasks_grp = dis.SlashCommandGroup(
        "tasks", description="Commands for manipulating tasks."
    )

    def __init__(self, bot_: Bot):
        log.info("Adding cog Tasks")
        self.bot = bot_

    @tasks_grp.command()
    async def info(self, ctx: dis.ApplicationContext, list_name):
        """Print info about a list and it's tasks."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild.")
        try:
            msgs: list[str] = await helpers.get_tasks_info(ctx.guild.id, list_name)
        except sqlexc.NoResultFound:
            log.warning("Lookup failed, guild %s, name %s", ctx.guild.id, list_name)
            await ctx.respond(f"Couldn't find list {list_name}", ephemeral=True)
            return
        for msg in msgs:
            await ctx.respond(msg, ephemeral=True)

    @tasks_grp.command()
    async def new(self, ctx: dis.ApplicationContext, list_name, content):
        """Add a new task to a list"""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild.")
        try:
            msg_update: MsgUpdate = await helpers.mk_task(
                ctx.guild.id, list_name, content
            )
        except sqlexc.NoResultFound:
            log.warning("Lookup failed, guild %s, name %s", ctx.guild.id, list_name)
            await ctx.respond(f"Couldn't find list {list_name}", ephemeral=True)
            return
        msg = await ctx.fetch_message(msg_update.id)
        await msg.edit(content=msg_update.content)
        await ctx.respond("Task added :-)", ephemeral=True)

    @tasks_grp.command(name="del")
    @dis.option(
        "positions",
        str,
        help="A whitespace seperated list of integers. Ie.: '1 2 3'. Indexed from zero",
    )
    async def del_(self, ctx: dis.ApplicationContext, list_name: str, positions: str):
        """Delete a task."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild.")

        try:
            local_ids: list[int] = util.split_int(positions)
        except ValueError:
            await ctx.respond("Invalid argument :-(", ephemeral=True)
            return

        try:
            await helpers.del_tasks(ctx.guild.id, list_name, *local_ids)
        except sqlexc.NoResultFound:
            log.warning(
                "Lookup failed, guild %s, name %s, pos %s",
                ctx.guild.id,
                list_name,
                local_ids,
            )
            await ctx.respond(
                f"Couldn't find task in {list_name} w/ positions {local_ids}"
            )
            return
        await ctx.respond("Task deleted :-)")

    @tasks_grp.command()
    @dis.option(
        "positions",
        str,
        help="A whitespace seperated list of integers. Ie.: '1 2 3'. Indexed from zero",
    )
    async def chk(self, ctx: dis.ApplicationContext, list_name: str, positions: str):
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
                ctx.guild.id, list_name, *local_ids
            )
        except ValueError as exc:
            log.warning("Caught exception", exc_info=exc)
            await ctx.respond(str(exc.args[0]), ephemeral=True)
            return

        msg: dis.Message = await ctx.fetch_message(msg_update.id)
        await msg.edit(content=msg_update.content)
        await ctx.respond("List updated :-)", ephemeral=True)
