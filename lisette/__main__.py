#!/usr/bin/env python
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Entrypoint module for Lisette bot."""
import asyncio
import functools
import logging
import os
import signal
import sys
from types import FrameType

import sqlalchemy.ext.asyncio as sqlaio

import lisette.cogs.tasks
import lisette.cogs.lists
from lisette.core import bot, database, options
from lisette.lib import config
import lisette.lib.logging


# class App:
#     """App main class"""

#     async def start(self) -> None:
#         """Start bot loop and connect to database"""
#         log.info("Starting!")
#         log.info("Getting database %s", cfg.db_path)
#         self.engine = await database.initalize(cfg.db_path, DEBUG)
#         token = cfg.token
#         self.bot = bot.Bot()


#         try:
#             await self.bot.start(token)
#         except asyncio.CancelledError:
#             await self.close()
#             raise

#     async def close(self) -> None:
#         """Stop app loop"""
#         if not self.bot or not self.engine:
#             raise TypeError
#         log.info("Shutting down bot. . .")
#         await self.bot.close()
#         log.info("Shutting database engine. . .")
#         await self.engine.dispose()


def exit_handler(signum: int, tasks: set[asyncio.Task]) -> None:  # type: ignore
    global log
    signame = signal.Signals(signum).name
    log.info(f"Signal handler called with signal {signame} ({signum})")
    if signal.SIGINT or signal.SIGTERM:
        log.info("Cancelling background tasks. .  .")
        for task in tasks:
            task.cancel()


async def main() -> None:
    global log
    bot_ = bot.Bot()
    cfg = config.get_cfg(options.lis_options, env_prefix="LISETTE")
    log = lisette.lib.logging.initalize(cfg, "lisette", DEBUG)

    bot_.add_cog(lisette.cogs.lists.ListsCog(bot_))
    bot_.add_cog(lisette.cogs.tasks.TasksCog(bot_))

    engine = await database.initalize(cfg.db_path)
    tasks: set[asyncio.Task] = set()  # type: ignore

    async with asyncio.TaskGroup() as tg:
        # Add signal handlers
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(
            signal.SIGINT, functools.partial(exit_handler, signal.SIGINT, tasks)
        )
        loop.add_signal_handler(
            signal.SIGTERM, functools.partial(exit_handler, signal.SIGTERM, tasks)
        )
        tasks.add(tg.create_task(bot_.begin(cfg.token)))

    log.info("Closing database engine.")
    await engine.dispose()
    log.info("Shutdown complete")


if __name__ == "__main__":
    DEBUG: bool = False
    SHUTDOWN = True
    log: logging.Logger
    if (
        os.getenv("LISETTE_DEBUG") == "1" or os.getenv("LISETTE_LOG_LEVEL") == "DEBUG"
    ) and __debug__:
        DEBUG = True
        log = lisette.lib.logging.fallback_logger("lisette")
        log.warning("DEBUG MODE")

    asyncio.run(main())
