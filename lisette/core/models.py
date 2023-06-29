# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""ORM models for Lisette"""
import logging
from typing import Any, List, Optional, Self, Sequence, Type, TypeVar, overload

import sqlalchemy as sql
import sqlalchemy.ext.asyncio as sqlaio
import sqlalchemy.orm as sqlorm

from lisette.core import exceptions

T = TypeVar("T")

DISCORD_MAX_CHARS = 2000
LIST_NAME_MAX = 38  # To fit in modal title

CHECKED_CHAR = '!'
META_END_CHAR = '\\'
META_CHARS = (CHECKED_CHAR)

log = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class Base(sqlorm.DeclarativeBase, sqlorm.MappedAsDataclass, sqlaio.AsyncAttrs):
    """Internal base class for model objects"""

    def __post_init__(self) -> None:
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
        cascade="save-update, merge, expunge, delete",
        order_by="Task.local_id",
        lazy="selectin",
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

    def _len_tasks(self) -> int:
        return sum(map(len, self.tasks))

    def insert(self, task: "Task") -> None:
        """Insert a new task into this list."""
        # Get next free short id
        task.local_id = len(self.tasks)
        self.tasks.append(task)
        log.debug("inserted %r into %r", task, self)

    def insert_all(self, *tasks: "Task") -> None:
        """Insert serveral new tasks into this list."""
        # Get next free short id
        for task in tasks:
            task.local_id = len(self.tasks)
            self.tasks.append(task)
            log.debug("inserted %r into %r", task, self)

    def clear(self) -> None:
        """Clear all tasks from self"""
        del self.tasks[:]

    def renumber(self) -> None:
        """Sync task local ids with list position"""
        for i, task in enumerate(self.tasks):
            task.local_id = i

    @sqlorm.validates("name")
    def _valid_name_length(self, cb_key: str, name: str) -> str:
        """Ensure new list name doesn't make message/ edit modal title too long"""
        if len(name) > LIST_NAME_MAX:
            raise ValueError("Max list name length is 38 characters")
        new_length = len(name) + self._len_tasks()
        if new_length > DISCORD_MAX_CHARS:
            raise ValueError("List name would make message too long.")
        return name

    @sqlorm.validates("tasks")
    def _valid_list_length(self, cb_key: str, task: "Task") -> "Task":
        """Ensure list will not be too long when adding task."""
        new_length = len(self) + len(task)
        if new_length > DISCORD_MAX_CHARS:
            raise ValueError("Task would make message too long")
        return task
    
    def encode_tasks(self) -> str:
        lines = []

        # add tasks
        for task in self.tasks:
            lines.append(task.encode())
        return '\n'.join(lines)
    
    @overload
    @classmethod
    async def lookup(
        cls, session: sqlaio.AsyncSession, guild_id: int, name: str
    ) -> Self:
        ...

    @overload
    @classmethod
    async def lookup(
        cls, session: sqlaio.AsyncSession, guild_id: int
    ) -> Sequence[Self]:
        ...

    @overload
    @classmethod
    async def lookup(
        cls, session: sqlaio.AsyncSession, guild_id: int, name: str, attr: str
    ) -> T:
        ...

    @overload
    @classmethod
    async def lookup(
        cls, session: sqlaio.AsyncSession, guild_id: int, *, attr: str
    ) -> Sequence[T]:
        ...

    @classmethod
    async def lookup(
        cls,
        session: sqlaio.AsyncSession,
        guild_id: int,
        name: Optional[str] = None,
        attr: Optional[str] = None,
    ) -> Self | Sequence[Self] | Any | Sequence[Any]:
        """Lookup TaskList objects

        Arguments:
            session: SQL session to use.
            guild_id: Of list to lookup
            name: Of list to lookup (required if not all)
            load_tasks: Whether to load list's task objects
            all: Whether to return a sequence of all in guild.

        Raises:
            sql.orm.exc.MultipleResultsFound
            sql.orm.exc.NoResultFound
            ValueError
        """
        if attr:
            entity = getattr(cls, attr)
        else:
            entity = cls

        stmt = sql.select(entity).where(cls.guild_id == guild_id)
        if name:
            stmt = stmt.where(cls.name == name)
            return (await session.scalars(stmt)).one()
        else:
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
    def _format_content(cls, content: str, checked: bool) -> str:
        """Returns content formatted for display based on bool checked"""
        if checked:
            return cls.CHECKED_FRMT.format(content)
        return cls.UNCHECKED_FRMT.format(content)

    def pretty_txt(self) -> str:
        """Returns content formatted for display"""
        return Task._format_content(self.content, self.checked)

    # async def delete(self, session: sqlaio.AsyncSession, commit: bool = False) -> None:
    #     """Deletes a Task from its parent and renumbers Tasks w/ higher local_id

    #     If commit = True, the changes are committed to database. If false, the session passed
    #     must be commited later or changes will be lost.
    #     """

    #     # Get list of parent list tasks in order
    #     log.debug("Trying to get tasks in same list")
    #     parent = await session.get(TaskList, self.parent_list_id)
    #     del_task_id = self.id
    #     if parent is None:
    #         raise TypeError("Task has no parent.")

    #     await session.delete(self)
    #     log.debug("DB del done.")

    #     # Renumber tasks with local_ids above this one's
    #     tasks: list["Task"] = await parent.awaitable_attrs.tasks
    #     tasks.sort(key=lambda x: x.local_id)  # type: ignore
    #     for task in tasks[del_task_id:]:
    #         if task.local_id is None:
    #             raise TypeError
    #         task.local_id -= 1

    #     if commit:
    #         await session.commit()

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

    def encode(self) -> str:
        """Return representation of this task as markup text."""
        chars: list[str] = []
        # Handle special chars
        if self.checked:
            chars.append(CHECKED_CHAR)
    
        # Handle putting in escape if necessary.
        if self.content[0] in META_CHARS:
            chars.append(META_END_CHAR)
            
        # Add content
        chars.extend(self.content)
        return ''.join(chars)
    
    @classmethod
    def decode(cls, txt: str) -> Self:
        """Returns a Task from encoded text."""
        chars = list(txt)
        meta_end = 0
        checked = False
        i = 0
        for c in chars:
            # Special case, next char is start of content, don't continue.
            if c == META_END_CHAR:
                meta_end += 1
                break
            elif c == CHECKED_CHAR:
                checked = True
            # If not special, this is the first char of content
            else:
                break
            meta_end += 1

        content = ''.join(chars[meta_end:])            
        return Task(content, checked=checked)

    @classmethod
    def decode_many(cls, txt) -> list[Self]:
        lines = txt.splitlines()
        tasks: list[Self] = []

        for line in lines:
            tasks.append(Task.decode(line))

        return  tasks
        
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
