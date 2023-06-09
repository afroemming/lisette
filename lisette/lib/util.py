# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Various utility functions"""


def split_len(txt: str, length: int = 2000) -> list[str]:
    """Splits a long string into a list of strings of a certain length or less"""
    out = []
    while len(txt) > 0:
        out.append(txt[:length])
        txt = txt[length:]
    return out


def split_int(txt: str) -> list[int]:
    """Split a whitespace seperated str of integers to a list of integers

    Raises:
        ValueError
    """
    strings = txt.split()
    ints = [int(x) for x in strings]
    return ints
