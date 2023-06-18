# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Module with commands for manipulating lists."""
import logging
from typing import Any, Coroutine, NoReturn

import discord as discord
import sqlalchemy.exc as sqlexc
from discord.commands import ApplicationContext

from lisette.cogs import helpers
from lisette.core import models, ui
from lisette.core.bot import Bot
from lisette.core.database import SESSION
from lisette.lib import util

log = logging.getLogger(__name__)


class TasksCog(discord.Cog):
    """Tasks cog class"""

    def __init__(self, bot_: Bot):
        log.info("Adding cog 'tasks'")
        self.bot = bot_

    tasks = discord.SlashCommandGroup(
        "tasks", description="Commands for managing tasks.", guild_only=True
    )
    lists = tasks.create_subgroup(
        "lists", description="Commands for managing lists.", guild_only=True
    )

    async def cog_command_error(
        self, ctx: ApplicationContext, error: Exception
    ) -> None:
        log.error("exc in cmd %s", ctx.command)
        if isinstance(error, sqlexc.NoResultFound) or isinstance(
            error, sqlexc.MultipleResultsFound
        ):
            await ctx.respond(
                "Couldn't find list in database. Did you spell its" " name correctly?",
                ephemeral=True,
            )
        elif isinstance(error, discord.NotFound):
            await ctx.respond(
                "Couldn't get message from Discord. Are you in the"
                " same channel as it? Has it been deleted?",
                ephemeral=True,
            )
        elif isinstance(error, discord.Forbidden):
            await ctx.respond(
                "Sorry, I am missing permissions I need to get this"
                " list's message. Am I allowed to see the channel its"
                " in?",
                ephemeral=True,
            )
        else:
            await ctx.respond(f"error during command {ctx.command}: {str(error)}")
            raise error

    @tasks.command()  # type: ignore
    @discord.guild_only()  # type: ignore
    @discord.option("name", str, help="List to edit tasks of.", autocomplete=helpers.autocomplete_list)  # type: ignore
    async def edit(self, ctx: discord.ApplicationContext, name):
        """Edit all of a list tasks in a pop-up dialog"""
        assert ctx.guild_id is not None

        msg = await helpers.get_list_msg(ctx, name)
        txt = await helpers.get_edit_txt(ctx.guild_id, name)

        modal = ui.TasksEdit(name, txt, msg, title=f"Edit '{name}'")
        await ctx.send_modal(modal)
        await ui.ephm_respond(ctx, "All done :-)")

    @tasks.command()
    @discord.guild_only()  # type: ignore
    @discord.option("name", str, description="Name of list to print task info for", autocomplete=helpers.autocomplete_list)  # type: ignore
    async def info(self, ctx: discord.ApplicationContext, name: str) -> None:
        """Print info about a list and it's tasks."""
        assert ctx.guild_id is not None

        msgs: list[str] = await helpers.get_tasks_info(ctx.guild.id, name)
        for msg in msgs:
            await ui.ephm_respond(ctx, msg)

    @tasks.command(description="Add a new task to a list")
    @discord.guild_only()  # type: ignore
    @discord.option("name", str, description="Name of list to add task to.", autocomplete=helpers.autocomplete_list)  # type: ignore
    @discord.option("content", str, description="Text to put with task.")  # type: ignore
    async def new(
        self, ctx: discord.ApplicationContext, name: str, content: str
    ) -> None:
        """Add a new task to a list"""
        assert ctx.guild_id is not None
        await ctx.defer(ephemeral=True)

        msg = await helpers.get_list_msg(ctx, name)
        update: str = await helpers.mk_task(ctx.guild_id, name, content)

        await msg.edit(content=update)
        await ui.ephm_respond(ctx, "Task added :-)")

    @tasks.command(name="del")
    @discord.guild_only()  # type: ignore
    @discord.option("name", str, description="Name of list to delete tasks from", autocomplete=helpers.autocomplete_list)  # type: ignore
    @discord.option(
        "positions",
        str,
        help="A whitespace seperated list of integers. Ie.: '1 2 3'. Indexed from zero",
    )  # type: ignore
    async def del_(
        self, ctx: discord.ApplicationContext, name: str, positions: str
    ) -> None:
        """Delete tasks."""
        assert ctx.guild_id is not None
        await ctx.defer(ephemeral=True)

        msg = await helpers.get_list_msg(ctx, name)
        local_ids: list[int] = util.split_int(positions)
        status = await helpers.del_tasks(ctx.guild.id, name, *local_ids)
        update: str = status[2]

        await msg.edit(content=update)
        await ui.ephm_respond(
            ctx, f"Tasks {status[0]} deleted. Positions {status[1]} ignored :-)"
        )

    @tasks.command()
    @discord.guild_only()  # type: ignore
    @discord.option(
        "positions",
        str,
        help="A whitespace seperated list of integers. Ie.: '1 2 3'. Indexed from zero",
    )  # type: ignore
    @discord.option("name", str, description="Name of list to check tasks on.", autocomplete=helpers.autocomplete_list)  # type: ignore
    async def chk(
        self, ctx: discord.ApplicationContext, name: str, positions: str
    ) -> None:
        """Check or uncheck tasks with given positions"""
        assert ctx.guild_id is not None
        await ctx.defer(ephemeral=True)

        msg = await helpers.get_list_msg(ctx, name)
        # Parse args
        try:
            local_ids: list[int] = util.split_int(positions)
        except ValueError:
            await ui.ephm_respond(ctx, "Invalid argument :-(")
            return

        # Check tasks
        msg_update: str = await helpers.check_tasks(ctx.guild.id, name, *local_ids)

        await msg.edit(content=msg_update)
        await ui.ephm_respond(ctx, "List updated :-)")

    @tasks.command(
        guild_only=True, description="Deletes all tasks in a list that are checked."
    )
    @discord.option("name", str, description="Name of list to delete tasks from.")  # type: ignore
    async def delchk(self, ctx: discord.ApplicationContext, name: str) -> None:
        assert ctx.guild_id is not None
        await ctx.defer()

        msg = await helpers.get_list_msg(ctx, name)

        update = await helpers.del_checked(ctx.guild.id, name)
        await msg.edit(content=update)
        await ui.ephm_respond(ctx, "All done :-)")

    @lists.command(name="info")
    @discord.guild_only()
    async def list_info(self, ctx: discord.ApplicationContext) -> None:
        """List all lists in this guild."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild info.")
        msgs: list[str] = await helpers.get_lists_info(ctx.guild.id, ctx.guild.name)
        await helpers.respond_all(ctx, msgs)

    @lists.command(name="new")
    @discord.option("name", str, description="Name of new list.")  # type: ignore
    @discord.guild_only()  # type: ignore
    async def list_new(self, ctx: discord.ApplicationContext, name: str) -> None:
        """Make a new list in current channel."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild id.")
        if not ctx.channel.can_send(discord.Message):
            await ctx.respond(
                "Sorry, I can't send messages in this channel :-(", ephemeral=True
            )
            return
        msg: discord.Message = await ctx.send("Making list...")
        txt: str = await helpers.mk_list(ctx.guild.id, name, msg.id)
        await msg.edit(content=txt)
        await ui.ephm_respond(ctx, "Made list :-)")

    @lists.command(name="del")
    @discord.option(
        "name",
        str,
        description="Name of list to delete",
        autocomplete=helpers.autocomplete_list,
    )  # type:ignore
    @discord.guild_only()  # type: ignore
    async def list_del_(self, ctx: discord.ApplicationContext, name: str) -> None:
        """Delete the list 'name' in current guild."""
        assert ctx.guild_id is not None
        await ctx.defer(ephemeral=True)

        conf = await ui.confirm(ctx, f"Confirm deleting: '{name}'?")
        if not conf:
            return

        try:
            msg = await helpers.get_list_msg(ctx, name)
        except discord.NotFound:
            msg = None
            cont = await ui.confirm(
                ctx, "Couldn't get message! Delete from database anyways?"
            )
            if not conf:
                return

        await helpers.del_list(ctx.guild_id, name)

        if msg:
            await msg.delete()
        await ui.ephm_respond(ctx, f"Deleted '{name}'.")

    @lists.command(name="edit")
    @discord.guild_only()
    @discord.option(
        "name",
        str,
        description="Current name of the list.",
        autocomplete=helpers.autocomplete_list,
    )  # type:ignore
    @discord.option("new_name", str, description="New name to use.")  # type:ignore
    async def list_edit(
        self, ctx: discord.ApplicationContext, name: str, new_name: str
    ) -> None:
        assert ctx.guild_id is not None
        msg = await helpers.get_list_msg(ctx, name)
        try:
            update = await helpers.put_list_edit(ctx.guild_id, name, new_name)
        except ValueError:
            await ctx.respond(
                f"There already is a list name {new_name} in this guild :-(",
                ephemeral=True,
            )
            return

        await msg.edit(content=update)
        await ctx.respond("Name updated :-)", ephemeral=True)
