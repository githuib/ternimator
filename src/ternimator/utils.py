import sys
import time
from collections import deque
from collections.abc import Iterable
from math import ceil, log10
from os import get_terminal_size
from secrets import randbelow
from typing import TYPE_CHECKING

from kleur.formatting import LINE_CLEAR, LINE_UP

if TYPE_CHECKING:
    from collections.abc import Iterator

type Lines = Iterable[str]


def consume(iterator: Iterator) -> None:
    """
    Consume an iterator entirely.

    We will achieve this by feeding the entire iterator into a zero-length deque.
    """
    deque(iterator, maxlen=0)


def randf(exclusive_upper_bound: float = 1, precision: int = 8) -> float:
    """
    Return a random float in the range [0, n).

    :param exclusive_upper_bound: n
    :param precision: Number of digits to round to
    :return: randomly generated floating point number
    """
    epb = 10 ** (ceil(log10(exclusive_upper_bound)) + precision)
    return randbelow(epb) * exclusive_upper_bound / epb


def write_lines(lines: Iterable, *, crop_to_terminal: bool = False) -> int:
    block = [str(line) for line in lines]
    height = len(block)
    if crop_to_terminal:
        # Could be nice to crop to width as well, but it seems
        # to me vertical cropping is a bit quirky now anyway.
        _max_width, max_height = get_terminal_size()
        height = min(max_height - 1, height)
    for line in block[-height:]:
        sys.stdout.write(line + "\n")
    return height


def clear_lines(amount: int) -> None:
    for _ in range(amount):
        sys.stdout.write(LINE_UP + LINE_CLEAR)


def refresh_lines(
    lines: Iterable, *, fps: float = None, crop_to_terminal: bool = False
) -> None:
    lines_written = write_lines(lines, crop_to_terminal=crop_to_terminal)
    if fps:
        time.sleep(1 / fps)
    clear_lines(lines_written)
