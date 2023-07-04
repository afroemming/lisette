import logging
from importlib import metadata
import discord

from lisette.core.bot import Bot

PKG = "lisette"

log = logging.getLogger(__name__)


class UtilCog(discord.Cog):
    def __init__(self, bot_):
        log.info("Adding cog 'util'")
        self.bot = bot_

    @discord.slash_command()
    async def version(self, ctx: discord.ApplicationCommand):
        """Print application version."""
        await ctx.respond(
            f"lisette {metadata.version(PKG)}\n"
            f"Copyright (c) 2023 {metadata.metadata(PKG)['author']}\n"
            f"License {metadata.metadata(PKG)['license']}",
            ephemeral=True,
        )
