# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
# pylint: skip-file
import logging
from lisette.lib.logging import logfn


@logfn
def example(a, b):
    return [a, b]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    example(1, 2)
