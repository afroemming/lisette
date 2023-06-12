# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Module with commands for manipulating lists."""
import logging
from typing import NoReturn

import discord as dis
import discord.ext.commands as disc
import sqlalchemy.exc as sqlexc

from lisette.cogs import helpers
from lisette.core.bot import Bot

log = logging.getLogger(__name__)


class ListsCog(disc.Cog):
    """Cog for manipulating lists"""

    lists_grp = dis.SlashCommandGroup("lists", "Commands for manipulating lists.")

    def __init__(self, bot_: Bot) -> None:
        log.info("Adding cog 'lists'.")
        self.bot = bot_

    @lists_grp.command()
    @dis.guild_only()  # type: ignore
    async def info(self, ctx: dis.ApplicationContext) -> None:
        """List all lists in this guild."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild info.")
        msgs: list[str] = await helpers.get_lists_info(ctx.guild.id, ctx.guild.name)
        await helpers.respond_all(ctx, msgs)

    @lists_grp.command()
    @dis.guild_only()  # type: ignore
    async def new(self, ctx: dis.ApplicationContext, name: str) -> None:
        """Make a new list in current channel."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild id.")
        if not ctx.channel.can_send(dis.Message):
            await ctx.respond(
                "Sorry, I can't send messages in this channel :-(", ephemeral=True
            )
            return
        msg: dis.Message = await ctx.send("Making list...")
        txt: str = await helpers.mk_list(ctx.guild.id, name, msg.id)
        await msg.edit(content=txt)
        await ctx.respond("Made list :-)", ephemeral=True)

    @lists_grp.command(name="del")
    @dis.guild_only()  # type: ignore
    async def del_(self, ctx: dis.ApplicationContext, name: str) -> None:
        """Delete the list 'name' in current guild."""
        if ctx.guild_id is None:
            raise TypeError("Couldn't get guild id.")
        try:
            msg_id = await helpers.del_list(ctx.guild_id, name)
        except sqlexc.NoResultFound:
            log.exception("Caught exception.")
            await ctx.respond(f"Couldn't find list '{name}' to delete", ephemeral=True)
            return

        msg: dis.Message = await ctx.fetch_message(msg_id)
        await msg.delete()
        await ctx.respond(f"Deleted '{name}'.", ephemeral=True)

    @lists_grp.command()
    @dis.guild_only()
    @dis.option('name', str, description="Current name of the list.") # type:ignore
    @dis.option('new_name', str, description="New name to use.") # type:ignore
    async def edit(self, ctx: dis.ApplicationContext, name: str, new_name: str) -> None:
        if ctx.guild is None:
            raise TypeError('Invalid context.')
        try:
            update = await helpers.put_list_edit(ctx.guild.id, name, new_name)
        except ValueError:
            await ctx.respond(f"There already is a list name {new_name} in this guild :-(")
            return
        msg = ctx.bot.get_message(update.id)
        if msg is None:
            log.error("Msg lookup failed. List name: '%s', got id '%s", name, update.id)
            await ctx.respond(f"Couldn't get list message to edit. Rolling back. . . :-(")
            await helpers.put_list_edit(ctx.guild.id, name, name)
            raise TypeError
        await msg.edit(content=update.content)
        await ctx.respond('Name updated :-)')
        

    async def cog_command_error(
        self, ctx: dis.ApplicationContext, exc: Exception
    ) -> NoReturn:
        log.exception("Unhandled exception:", exc_info=exc)
        await ctx.respond(
            f"There was an error while doing a command ({ctx.command}): {str(exc)}",
            ephemeral=True,
        )
        raise exc
