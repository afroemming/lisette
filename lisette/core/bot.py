#!/usr/bin/env python3
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Module contains subclass definition for pycord Bot"""
import asyncio
import logging
from typing import Any

import discord

log = logging.getLogger(__name__)


class Bot(discord.Bot):
    """pycord.Bot subclass for lisette"""

    def __init__(self, *args: Any, **options: Any) -> None:
        discord.Bot.__init__(self, *args, **options)  # type: ignore

    async def begin(self, token: str) -> None:
        try:
            await self.start(token)
        except asyncio.CancelledError:
            log.info("Closing bot task.")
            await self.close()
            raise

    async def on_ready(self) -> None:
        """Override the on_ready event to echo to log"""
        if self.user is None:
            raise TypeError
        log.info("Ready!")
        log.info("Logged in as")
        log.info(self.user.name)
        log.info(self.user.id)
        log.info("------")
