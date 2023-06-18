from typing import Any, Optional

import discord
import sqlalchemy.ext.asyncio as sqlaio
from discord.interactions import Interaction

from lisette.cogs import helpers
from lisette.core import exceptions, models
from lisette.core.database import SESSION


async def ephm_respond(ctx: discord.ApplicationContext, msg: str) -> None:
    await ctx.respond(msg, ephemeral=True, delete_after=10)


async def confirm(
    ctx: discord.ApplicationContext, msg: str, raises: bool = False
) -> Optional[bool]:
    view = Confirm()
    prompt = await ctx.send(msg, view=view)
    await view.wait()

    if view.value is None:
        await ephm_respond(ctx, "Timed out. . .")
    if view.value:
        await ephm_respond(ctx, "Confirmed.")
    elif raises:
        await ephm_respond(ctx, "Cancelled.")
        raise exceptions.CancelledError()

    await prompt.delete()
    return view.value


class Confirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.value: Optional[bool] = None

    # When the confirm button is pressed, set the inner value
    # to `True` and stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction  # type: ignore
    ) -> None:
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`.
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction  # type: ignore
    ) -> None:
        self.value = False
        self.stop()


class TasksEdit(discord.ui.Modal):
    def __init__(
        self, name: str, txt: str, msg: discord.Message, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.msg = msg
        self.name = name

        self.add_item(
            discord.ui.InputText(
                label="Tasks (one per line, ! prefix marks checked.)",
                style=discord.InputTextStyle.long,
                value=txt,
                max_length=2000,
                required=True,
            )
        )

    async def callback(self, interaction: Interaction) -> None:
        name = self.name
        input_ = self.children[0].value
        guild = interaction.guild
        channel = interaction.channel
        # Validate context
        assert guild is not None
        assert channel is not None
        assert input_ is not None
        assert isinstance(channel, discord.TextChannel)

        async with SESSION() as session:
            msg_id: int = await models.TaskList.lookup(
                session, guild.id, name, attr="msg_id"
            )
            msg = await channel.fetch_message(msg_id)

        # Make tasks
        update: str = await helpers.put_edit(guild.id, name, input_)

        await msg.edit(content=update)
        await interaction.response.send_message(
            content="Made edit :-)", ephemeral=True, delete_after=10
        )
