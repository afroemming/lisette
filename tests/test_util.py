# pylint: skip-file
# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
import pytest
from lisette.lib import util


def test_split_len():
    s = "aabbcc"
    t = util.split_len(s, 2)
    assert t[0] == "aa"
    assert t[1] == "bb"
    assert t[2] == "cc"
    assert len(t) == 3
