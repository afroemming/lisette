from typing import Any
import discord as dis
from discord.interactions import Interaction

from lisette.core.collections import MsgUpdate
from lisette.cogs import helpers


class TasksEdit(dis.ui.Modal):
    def __init__(self, txt: str, list_name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.list_name = list_name

        self.add_item(
            dis.ui.InputText(
                label="Tasks (one per line, ! prefix marks checked.)",
                style=dis.InputTextStyle.long,
                value=txt,
                max_length=2000,
            )
        )

    async def callback(self, interaction: Interaction) -> None:
        name = self.list_name
        input_ = self.children[0].value
        guild = interaction.guild
        channel = interaction.channel
        # Validate context
        if guild is None or channel is None:
            raise TypeError("Invalid context.")
        if name is None or input_ is None:
            raise TypeError("Inappropiate input.")
        if not isinstance(channel, dis.TextChannel):
            raise TypeError("Inappropriate source channel")

        await interaction.response.send_message(content="Made edit :-)", ephemeral=True)
        # Make tasks
        update: MsgUpdate = await helpers.put_edit(guild.id, name, input_)

        msg = await channel.fetch_message(update.id)
        await msg.edit(content=update.content)
