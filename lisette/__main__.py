#!/usr/bin/env python
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Entrypoint module for Lisette bot."""
import logging
import asyncio

import dotenv

import discord
import sqlalchemy.ext.asyncio as sqlaio
import lisette.logging
import lisette.core.database
import lisette.lib.classes as classes
from lisette.core.bot import Lisette
from lisette.lib import config

options = [
    config.Option(
        "log_level",
        "Level message to log",
        choices=["DEBUG", "INFO", "WARNING", "CRITICAL"],
        default="WARNING",
        warning=True,
        post_load=lisette.logging.get_numeric,
    ),
    config.Option("token", "Discord bot token to use.", required=True),
    config.Option(
        "db_url",
        "Url/ path to database to use for bot. For a local database, ie. 'sqlite:///",
        required=True,
    ),
    config.Option("env_file", "Path to env file to load enviroment variables from."),
]


class App:
    def __init__(self):
        self.cfg: None | classes.Namespace = None
        self.database: None | sqlaio.AsyncEngine = None
        self.bot: None | Lisette = None
        print(__name__)

    async def start(self):
        """Lisette entrypoint function"""
        logging.basicConfig()
        core_filt = logging.Filter("lisette")
        logging.root.addFilter(core_filt)

        log = logging.getLogger(__name__)
        cli_args = config.load_cli_args(options)
        if cli_args.get("env_file") is not None:
            log.info("Using env_file: %s", cli_args.env_file)
            dotenv.load_dotenv(cli_args.env_file)
        env_vars = config.load_env_vars(options, "LISETTE")
        self.cfg = config.finalize(options, cli_args, env_vars)
        log.root.setLevel(self.cfg.log_level)

        logging.info("Starting...")
        logging.info("Will get database %s", self.cfg.db_url)
        database = await lisette.core.database.initalize(self.cfg.db_url)

        self.bot = Lisette()
        await self.bot.start(self.cfg.token)

    async def close(self):
        """Stop all tasks"""
        if self.bot is None:
            raise TypeError
        await self.bot.close()


if __name__ == "__main__":
    app = App()
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logging.info("Lisette is going down now.")
