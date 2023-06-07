# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Various useful and reusable classes"""
import types
from typing import Self


class Namespace(types.SimpleNamespace):
    """Simple object for using as an arbitrary namespace.

    Attributes may be freely added and accessed. In-built vars() returns
    a dict of only attributes added by client because this class has no regular
    attributes. Any kwargs will form the inital attributes in that object."""

    def union(self: Self, other: Self):
        """Join the namespaces of inserted Namespace into this object.

        Duplicate attrs will be overwritten"""
        out = self
        for key, val in vars(other).items():
            if val is None:
                continue
            setattr(out, key, val)
        return out

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, val):
        setattr(self, key, val)

    def get(self, key: str, default=None):
        """Get self['key'], returning None or if set 'default' if not present"""
        try:
            return self[key]
        except AttributeError:
            return default
