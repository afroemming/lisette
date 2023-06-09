# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
# pylint: skip-file
import os

import pytest

from lisette.lib.config import *


@pytest.fixture
def options():
    out = [
        Option("test1", arguments={"help": "test option"}),
        Option("test2", arguments={"help": "test option 2"}),
        Option("test_num", arguments={"help": "number"}, post_load=int),
    ]
    return out


@pytest.fixture
def options_required():
    out = [
        Option("not_req"),
        Option("test_req", required=True),
        Option("test_req2", required=True),
    ]
    return out


def test_get_env_vars(options):
    os.environ["TEST1"] = "9999"
    cfg = get_env_vars(options)
    assert cfg.test1 == "9999"


def test_cfg_get_raise_if_not_found(options):
    cfg = get_env_vars(options)
    with pytest.raises(AttributeError):
        cfg.aaaa


def test_post_load(options):
    os.environ["TEST_NUM"] = "9999"
    cfg = get_env_vars(options)
    assert cfg.test_num == 9999


def test_cfg_get_when_missing(options):
    cfg = get_env_vars(options)
    assert cfg.get("aaaa") is None


def test_cfg_contains(options):
    cfg = Cfg()
    assert "aaa" not in cfg


def test_validate_required_raises(options_required):
    cfg = get_env_vars(options_required)
    with pytest.raises(ConfigurationError):
        validate_required(options_required, cfg)


def test_get_cfg(options_required):
    with pytest.raises(ConfigurationError):
        cfg = get_cfg(options_required, exit_on_error=False)
