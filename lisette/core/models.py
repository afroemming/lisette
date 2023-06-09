# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""ORM models for Lisette"""
import logging
from typing import List, Self, Sequence

import sqlalchemy as sql
import sqlalchemy.ext.asyncio as sqlaio
import sqlalchemy.orm as sqlorm

from lisette.lib.logging import logfn

DISCORD_MAX_CHARS = 2000

log = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class Base(sqlorm.DeclarativeBase, sqlorm.MappedAsDataclass, sqlaio.AsyncAttrs):
    """Internal base class for model objects"""

    id: int | None

    def __post_init__(self):
        log.debug("new %r", self)


class TaskList(Base):
    """Model class for a task list

    Attributes:
        id: Database primary key, automatically generated.
        name: Name of this list.
        guild_id: Discord id of the guild this list is associated with.
        tasks: List of associated tasks, automatically populated.
        msg_id: Discord id of the message this list is output to.

    Args:
        name: As above.
        guild_id: As above.
    """

    __tablename__ = "task_list"
    NAME_FRMT = "**{0}**\n"

    id: sqlorm.Mapped[int] = sqlorm.mapped_column(init=False, primary_key=True)
    name: sqlorm.Mapped[str]
    guild_id: sqlorm.Mapped[int]
    tasks: sqlorm.Mapped[List["Task"]] = sqlorm.relationship(
        default_factory=list,
        back_populates="parent_list",
        cascade="all, delete-orphan",
    )
    msg_id: sqlorm.Mapped[int] = sqlorm.mapped_column(default=None)

    __table_args__ = (sql.UniqueConstraint("name", "guild_id"),)

    def pretty_name(self) -> str:
        """Returns list name formatted for display"""
        return self.NAME_FRMT.format(self.name)

    def pretty_print(self) -> str:
        """Returns entire list formatted for display"""
        txt = self.pretty_name()
        for task in self.tasks:
            txt += task.pretty_txt()
        return txt

    def _len_tasks(self):
        return sum(map(len, self.tasks))

    async def delete(self, session: sqlaio.AsyncSession, commit=True) -> int:
        """Delete self from database.

        The associated discord message must be deleted seperately. If commit is
        True, commit session to database after changes.
        Returns
            int: msg_id for self.
        """
        msg_id = self.msg_id
        await session.delete(self)
        if commit:
            await session.commit()
        return msg_id

    def insert(self, task: "Task"):
        """Insert a new task into this list."""
        # Get next free short id
        task.local_id = len(self.tasks)
        self.tasks.append(task)
        log.debug("inserted %r into %r", task, self)

    @sqlorm.validates("name")
    def _valid_name_length(self, key, name) -> str:
        """Ensure new list name doesn't make message too long"""
        _ = key
        new_length = len(name) + self._len_tasks()
        if new_length > DISCORD_MAX_CHARS:
            raise ValueError("List name would make message too long.")
        return name

    @sqlorm.validates("tasks")
    def _valid_list_length(self, key, task) -> "Task":
        """Ensure list will not be too long when adding task."""
        _ = key
        new_length = len(self) + len(task)
        if new_length > DISCORD_MAX_CHARS:
            raise ValueError("Task would make message too long")
        return task

    @classmethod
    async def lookup(
        cls, session: sqlaio.AsyncSession, guild_id: int, name: str
    ) -> Self:
        """Returns TaskList matching guild_id & name if found.

        Raises:
            sql.orm.exc.MultipleResultsFound
            sql.orm.exc.NoResultFound
        """
        stmt = (
            sql.select(cls)
            .where(cls.guild_id == guild_id)
            .where(cls.name == name)
            .options(sqlorm.selectinload(cls.tasks))
        )
        return (await session.scalars(stmt)).one()

    @classmethod
    async def guild_all(
        cls, session: sqlaio.AsyncSession, guild_id: int
    ) -> Sequence[Self]:
        """Return a Sequence of all TaskLists in guild."""
        stmt = sql.select(cls).where(cls.guild_id == guild_id)
        return (await session.scalars(stmt)).all()

    @classmethod
    async def guild_all_names(
        cls, session: sqlaio.AsyncSession, guild_id: int
    ) -> Sequence[str]:
        """Returns a list of names of lists in a guild."""
        stmt = sql.select(cls.name).where(cls.guild_id == guild_id)
        return (await session.scalars(stmt)).all()

    def __len__(self) -> int:
        sum_ = 0
        sum_ += len(self.pretty_name())
        sum_ += self._len_tasks()
        return sum_


class Task(Base):
    """Model class for a task

    len(Tasks()) returns the length of the longest possible pretty text for this
        task.

    Attributes:
        id: Database primary key, automatically generated.
        content: Unformated text that is the user provided content of this task.
        parent_list_id: Database id of the task list this is in (Foreign key).
        parent_list: TaskList object this task is associated with.
        checked: Boolean that represents whether this task is checked.

    Args:
        content: As above
    """

    __tablename__ = "task"
    CHECKED_FRMT = "☑  ~~{0}~~\n"
    UNCHECKED_FRMT = "☐  {0}\n"

    content: sqlorm.Mapped[str]
    id: sqlorm.Mapped[int] = sqlorm.mapped_column(init=False, primary_key=True)
    parent_list: sqlorm.Mapped[TaskList] = sqlorm.relationship(
        back_populates="tasks", init=False
    )
    parent_list_id: sqlorm.Mapped[int | None] = sqlorm.mapped_column(
        sql.ForeignKey("task_list.id"), default=None
    )
    local_id: sqlorm.Mapped[int | None] = sqlorm.mapped_column(default=None)
    checked: sqlorm.Mapped[bool] = sqlorm.mapped_column(default=False)

    @classmethod
    def _format_content(cls, content, checked) -> str:
        """Returns content formatted for display based on bool checked"""
        if checked:
            return cls.CHECKED_FRMT.format(content)
        return cls.UNCHECKED_FRMT.format(content)

    def pretty_txt(self) -> str:
        """Returns content formatted for display"""
        return Task._format_content(self.content, self.checked)

    @logfn
    async def delete(self, session: sqlaio.AsyncSession, commit: bool = True) -> None:
        """Deletes a Task from its parent and renumbers Tasks w/ higher local_id

        If commit = True, the changes are committed to database. If false, the session passed
        must be commited later or changes will be lost.
        """

        # Get list of parent list tasks in order
        log.debug("Trying to get tasks in same list")
        parent = await session.get(TaskList, self.parent_list_id)
        if parent is None:
            raise TypeError

        await session.delete(self)
        log.debug("DB del done.")

        # Renumber tasks with local_ids above this one's
        for task in await parent.awaitable_attrs.tasks:
            if task.local_id is None:
                raise TypeError
            task.local_id -= 1

        if commit:
            await session.commit()

    # @sqlorm.validates("content")
    # def _content_edit(self, key, content) -> str:
    #     """Ensure content edits do not make parent list too long"""
    #     _ = key
    #     if not self.parent_list:
    #         return content
    #     new_length = len(Task._format_content(content, True))
    #     lst_len_other = len(self.parent_list) - len(self)
    #     if lst_len_other + new_length > DISCORD_MAX_CHARS:
    #         raise ValueError("Task edit would make list message too long")
    #     return content

    @classmethod
    async def lookup(
        cls, session: sqlaio.AsyncSession, guild_id: int, lst_name: str, local_id: int
    ) -> Self:
        """Returns task which matches arguments

        Raises:
            sqlalchemy.exc.MultipleResultsFound
            sqlalchemy.exc.NoResultsFound
        """
        stmt = (
            sql.select(cls)
            .join(TaskList)
            .where(TaskList.guild_id == guild_id)
            .where(TaskList.name == lst_name)
            .where(cls.local_id == local_id)
        )
        log.debug(stmt)
        return (await session.scalars(stmt)).one()

    def __len__(self) -> int:
        max_txt = Task._format_content(self.content, True)
        return len(max_txt)

    def __repr__(self) -> str:
        return (
            f"Task(id={self.id}, content='{self.content}', "
            f"parent_list=..., parent_list_id={self.parent_list_id}, "
            f"local_id={self.local_id}, checked={self.checked})"
        )
