#!/usr/bin/env python
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Entrypoint module for Lisette bot."""
import asyncio
import os

import sqlalchemy.ext.asyncio as sqlaio

from lisette.cogs import lists, tasks
from lisette.core import bot, database, options
from lisette.lib import config, logging


class App:
    """App main class"""

    def __init__(self) -> None:
        self.bot: bot.Bot | None = None
        self.engine: sqlaio.AsyncEngine | None = None

    async def start(self) -> None:
        """Start bot loop and connect to database"""
        log.info("Starting!")
        log.info("Getting database %s", cfg.db_path)
        self.engine = await database.initalize(cfg.db_path, DEBUG)
        token = cfg.token
        self.bot = bot.Bot()

        self.bot.add_cog(lists.ListsCog(self.bot))
        self.bot.add_cog(tasks.TasksCog(self.bot))

        await self.bot.start(token)

    async def close(self) -> None:
        """Stop app loop"""
        if not self.bot or not self.engine:
            raise TypeError
        log.info("Shutting down.")
        await self.engine.dispose()
        await self.bot.close()


if __name__ == "__main__":
    DEBUG: bool = False
    if (
        os.getenv("LISETTE_DEBUG") == "1" or os.getenv("LISETTE_LOG_LEVEL") == "DEBUG"
    ) and __debug__:
        DEBUG = True
        log = logging.fallback_logger("lisette")
        log.warning("DEBUG MODE")

    app = App()
    cfg = config.get_cfg(options.lis_options, env_prefix="LISETTE")
    log = logging.initalize(cfg, "lisette", DEBUG)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(app.start())
    except KeyboardInterrupt:
        loop.run_until_complete(app.close())
    finally:
        log.info("All done. Bye!")
