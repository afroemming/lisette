#!/usr/bin/env python3
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Module contains subclass definition for pycord Bot"""
import logging
import discord

log = logging.getLogger(__name__)


class Bot(discord.Bot):
    """pycord.Bot subclass for lisette"""

    def __init__(self, *args, **options):
        discord.Bot.__init__(self, *args, **options)

    async def on_ready(self):
        """Override the on_ready event to echo to log"""
        if self.user is None:
            raise TypeError
        log.info("Ready!")
        log.info("Logged in as")
        log.info(self.user.name)
        log.info(self.user.id)
        log.info("------")
