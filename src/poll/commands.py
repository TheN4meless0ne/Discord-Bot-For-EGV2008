from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import discord
from discord import app_commands

MAX_ANSWERS = 10
MAX_QUESTION = 300  # Discord limit
MAX_ANSWER = 55     # Discord limit

MAX_HOURS = 768     # Discord limit (32 days)

# Helpers
@dataclass
class PollDraft:
    question: str
    answers: list[str]
    hours: int
    multiple: bool = False

def format_hours(hours: int) -> str:
    days, rest = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if rest:
        parts.append(f"{rest} hour{'s' if rest != 1 else ''}")
    return " ".join(parts)

def build_poll(draft: PollDraft) -> discord.Poll:
    poll = discord.Poll(
        question=draft.question,
        duration=dt.timedelta(hours=draft.hours),
        multiple=draft.multiple,
    )
    for answer in draft.answers:
        poll.add_answer(text=answer)
    return poll

def preview_embed(draft: PollDraft) -> discord.Embed:
    lines = [f"`{i}.` {a}" for i, a in enumerate(draft.answers, start=1)]
    if len(draft.answers) < MAX_ANSWERS:
        # The "next slot" – only ever one visible at a time
        lines.append(f"`{len(draft.answers) + 1}.` *…add another*")

    embed = discord.Embed(title=draft.question, description="\n".join(lines), colour=discord.Colour.blurple())
    embed.add_field(name="Duration", value=format_hours(draft.hours))
    embed.add_field(name="Multiple answers", value="Yes" if draft.multiple else "No")
    embed.set_footer(text=f"{len(draft.answers)}/{MAX_ANSWERS} answers")
    return embed

# Builder UI
class AnswerModal(discord.ui.Modal):
    def __init__(self, builder: PollBuilder) -> None:
        n = len(builder.draft.answers) + 1
        super().__init__(title=f"Answer {n}")
        self.builder = builder
        self.answer = discord.ui.TextInput(
            label=f"Answer {n}",
            max_length=MAX_ANSWER,
            required=True,
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        text = self.answer.value.strip()
        draft = self.builder.draft

        if not text:
            await interaction.response.send_message("The answer can't be empty.", ephemeral=True)
            return
        if len(draft.answers) >= MAX_ANSWERS:
            await interaction.response.send_message(f"You already have {MAX_ANSWERS} answers.", ephemeral=True)
            return

        draft.answers.append(text)
        await self.builder.refresh(interaction)

class RemoveAnswerSelect(discord.ui.Select):
    def __init__(self, answers: list[str]) -> None:
        options = [
            discord.SelectOption(label=f"{i}. {a}"[:100], value=str(i - 1))
            for i, a in enumerate(answers, start=1)
        ]
        super().__init__(placeholder="Remove an answer…", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: PollBuilder = self.view  # type: ignore[assignment]
        # Removing from the list re-numbers everything after it automatically
        del view.draft.answers[int(self.values[0])]
        await view.refresh(interaction)

class PollBuilder(discord.ui.View):
    def __init__(self, draft: PollDraft) -> None:
        super().__init__(timeout=600)
        self.draft = draft
        self._remove_select: RemoveAnswerSelect | None = None
        self._sync()

    def _sync(self) -> None:
        """Rebuild the dynamic parts of the view to match the draft."""
        self.add_answer.disabled = len(self.draft.answers) >= MAX_ANSWERS

        if self._remove_select:
            self.remove_item(self._remove_select)
            self._remove_select = None
        # Only offer removal while it keeps at least 2 answers
        if len(self.draft.answers) > 2:
            self._remove_select = RemoveAnswerSelect(self.draft.answers)
            self.add_item(self._remove_select)

    async def refresh(self, interaction: discord.Interaction) -> None:
        self._sync()
        await interaction.response.edit_message(embed=preview_embed(self.draft), view=self)

    @discord.ui.button(label="Add answer", emoji="➕", style=discord.ButtonStyle.primary, row=0)
    async def add_answer(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(AnswerModal(self))

    @discord.ui.button(label="Post poll", style=discord.ButtonStyle.success, row=0)
    async def post(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.stop()
        await publish(interaction, self.draft, from_builder=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.edit_message(content="Poll cancelled.", embed=None, view=None)

# /poll
@app_commands.command(name="poll", description="Create a poll.")
@app_commands.describe(
    question="What are you asking?",
    answer_1="First answer.",
    answer_2="Second answer.",
    duration="How many hours the poll stays open (up to 768 / 32 days). Defaults to 1 hour.",
    more_answers="Add up to 8 more answers before posting.",
    multiple_answers="Let people pick more than one answer."
)
@app_commands.guild_only()
async def poll(
    interaction: discord.Interaction,
    question: app_commands.Range[str, 1, MAX_QUESTION],
    answer_1: app_commands.Range[str, 1, MAX_ANSWER],
    answer_2: app_commands.Range[str, 1, MAX_ANSWER],
    duration: app_commands.Range[int, None, MAX_HOURS] = 1,
    more_answers: bool = False,
    multiple_answers: bool = False
):
    question, answer_1, answer_2 = question.strip(), answer_1.strip(), answer_2.strip()
    if not (question and answer_1 and answer_2):
        await interaction.response.send_message("Question and answers can't be blank.", ephemeral=True)
        return

    draft = PollDraft(
        question=question,
        answers=[answer_1, answer_2],
        hours=max(1, duration),  # anything below 1 falls back to 1 hour
        multiple=multiple_answers,
    )

    if more_answers:
        await interaction.response.send_message(
            embed=preview_embed(draft), view=PollBuilder(draft), ephemeral=True
        )
    else:
        await publish(interaction, draft, from_builder=False)

async def publish(interaction: discord.Interaction, draft: PollDraft, *, from_builder: bool) -> None:
    poll = build_poll(draft)
    if from_builder:
        await interaction.response.edit_message(content="Poll posted.", embed=None, view=None)
        await interaction.followup.send(poll=poll)
    else:
        await interaction.response.send_message(poll=poll)

COMMANDS = [poll]
