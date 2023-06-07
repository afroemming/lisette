"""Module with commands for manipulating lists."""

import discord
from discord import ApplicationContext
import discord.ext.commands as commands
import lisette.core.database
from lisette.core.database import SESSION_MKR
from lisette.core import models


def format_info(guild_id) -> str:
    msg = list()
    msg.append("Lists in current guild:")
    with SESSION_MKR() as sess:
        names = lisette.core.database.lookup_task_lists_names(guild_id, sess)
    for name in names:
        msg.append(name)
    return "\n".join(msg)


class Lists(commands.Cog):
    """Cog for manipulating lists"""

    lists = discord.SlashCommandGroup("lists", "Commands for manipulation lists")

    def __init__(self, bot_, database_):
        self.bot = bot_
        self.database = database_

    @lists.command()
    @discord.commands.guild_only()
    async def info(self, ctx: discord.ApplicationContext):
        """List all lists in current guild."""
        msg = format_info(ctx.guild_id)
        await ctx.respond(msg, ephemeral=True)

    @lists.command()
    @discord.commands.guild_only()
    async def new(self, ctx: discord.ApplicationContext, name):
        """Make a new list in current channel."""
        if name is None:
            await ctx.respond("A name is required", ephemeral=True)
        if ctx.guild_id is None:
            return

        # Try making list
        try:
            lst = new_pre(ctx.guild_id, name)
        except ValueError as err:
            await ctx.respond(err, ephemeral=True)
            return
        # Print list
        msg = await ctx.send(lst.pretty_print())
        # Save list data
        new_post(lst, msg.id)

    @lists.command()
    @discord.commands.guild_only()
    async def delete(self, ctx: discord.ApplicationContext, name):
        try:
            del_do(name, ctx)
        except ValueError as err:
            await ctx.respond(err)
            return
