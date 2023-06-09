"""Module with commands for manipulating lists."""
import logging
from typing import Sequence

import discord as dis
import discord.ext.commands as disc

import sqlalchemy.exc as sqlexc

from lisette.core.bot import Bot
from lisette.core import models
from lisette.core.database import SESSION

log = logging.getLogger(__name__)


class Lists(disc.Cog):
    """Cog for manipulating lists"""

    lists = dis.SlashCommandGroup("lists", "Commands for manipulating lists.")

    def __init__(self, bot_: Bot) -> None:
        log.info("Adding cog 'lists'.")
        self.bot = bot_

    @staticmethod
    async def info_get(guild_id: int, guild_name: str) -> str:
        "Get list of lists in a server and format to txt, returning txt."
        async with SESSION() as sess:
            lsts: Sequence[models.TaskList] = await models.TaskList.guild_all(
                sess, guild_id
            )
            msg: list[str] = [f"Lists in guild {guild_name}:\n"]
            for lst in lsts:
                line: str = f"{lst.id}: {lst.name}\n"
                msg.append(line)
        return "".join(msg)

    @staticmethod
    async def new_do(name: str, msg_id: int, guild_id: int) -> str:
        """Create a new list, saving msg its out to in database"""
        # Make sure a list with the same name is not in this guild
        async with SESSION() as sess:
            names: Sequence[str] = await models.TaskList.guild_all_names(sess, guild_id)
            if name in names:
                raise ValueError("List with name '%s' already exists in guild.")
            lst = models.TaskList(name, guild_id, msg_id=msg_id)
            sess.add(lst)
            msg = lst.pretty_print()
            await sess.commit()
        return msg

    @staticmethod
    async def del_do(name: str, guild_id: int) -> int:
        """Delete a lst from database and return it's msg id"""
        async with SESSION() as sess:
            lst = await models.TaskList.lookup(sess, guild_id, name)
            msg_id = await lst.delete(sess)
        return msg_id

    @lists.command()
    async def info(self, ctx: dis.ApplicationContext) -> None:
        """List all lists in this guild."""
        if ctx.guild is None:
            raise TypeError("Couldn't get guild info.")
        msg: str = await self.info_get(ctx.guild.id, ctx.guild.name)
        await ctx.respond(msg, ephemeral=True)

    @lists.command()
    async def new(self, ctx: dis.ApplicationContext, name: str) -> None:
        """Make a new list in current channel."""
        if ctx.guild_id is None:
            raise TypeError("Couldn't get guild id.")
        msg: dis.Message = await ctx.send("Making list...")
        txt: str = await self.new_do(
            name,
            msg.id,
            ctx.guild_id,
        )
        await msg.edit(content=txt)
        await ctx.respond("Made list :-)", ephemeral=True)

    @lists.command(name="del")
    async def del_(self, ctx: dis.ApplicationContext, name: str) -> None:
        """Delete the list 'name' in current guild."""
        if ctx.guild_id is None:
            raise TypeError("Couldn't get guild id.")
        try:
            msg_id = await self.del_do(name, ctx.guild_id)
        except sqlexc.NoResultFound:
            log.exception("Caught exception.")
            await ctx.respond(f"Couldn't find list '{name}' to delete", ephemeral=True)
            return

        msg: dis.Message = await ctx.fetch_message(msg_id)
        await msg.delete()
        await ctx.respond(f"Deleted '{name}'.", ephemeral=True)

    async def cog_command_error(
        self, ctx: dis.ApplicationContext, error: dis.ApplicationCommandError
    ):
        log.exception("Unhandled exception:", exc_info=error)
        await ctx.respond(
            f"There was an error while doing a command ({ctx.command}): {type(error)}",
            ephemeral=True,
        )
        raise error
