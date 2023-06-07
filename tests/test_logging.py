import logging
from lisette.logging import logfn


@logfn
def example(a, b):
    return [a, b]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    example(1, 2)
