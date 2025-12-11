import sys
import time
from collections import deque
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from functools import reduce
from itertools import count
from math import ceil, log10
from os import get_terminal_size
from secrets import randbelow
from typing import TYPE_CHECKING, cast

from kleur.formatting import LINE_CLEAR, LINE_UP

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

type Lines = Iterable[str]
type Animation = Callable[[Lines, int, int], Lines]


@dataclass(frozen=True)
class AnimParams:
    fps: int | None = None
    keep_last: bool = True
    only_every_nth: int = 1
    crop_to_terminal: bool = False


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


def write_lines(lines: Lines, *, crop_to_terminal: bool = False) -> int:
    block = list(lines)
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
    lines: Lines, *, fps: float = None, crop_to_terminal: bool = False
) -> None:
    lines_written = write_lines(lines, crop_to_terminal=crop_to_terminal)
    if fps:
        time.sleep(1 / fps)
    clear_lines(lines_written)


def animate_iter[T](
    items: Iterator[T],
    format_item: Callable[[T], Lines] | None = None,
    *,
    params: AnimParams = None,
) -> Iterator[T]:
    if params is None:
        params = AnimParams()
    crop = params.crop_to_terminal

    def to_lines(item_: T) -> Lines:
        if format_item is None:
            # Somewhat sketchy but I can't think of a better way to
            # "do nothing" by default, that mypy would be ok with.
            return cast("Lines", item_)
        return format_item(item_)

    with suppress(KeyboardInterrupt):
        lines: Lines = []
        for i, item in enumerate(items):
            yield item
            if i % params.only_every_nth == 0:
                lines = list(to_lines(item))
                refresh_lines(lines, fps=params.fps, crop_to_terminal=crop)
        if params.keep_last:
            write_lines(lines, crop_to_terminal=crop)


def animate[T](
    items: Iterator[T],
    format_item: Callable[[T], Lines] | None = None,
    *,
    params: AnimParams = None,
) -> None:
    consume(animate_iter(items, format_item, params=params))


def animated_lines(
    lines: Lines, *animations: Animation, num_frames: int = None, fill_char: str = " "
) -> Iterator[Lines]:
    max_width, max_height = get_terminal_size()
    n_frames = max_width if num_frames is None else num_frames

    block = list(lines)
    height = min(len(block), max_height - 1)
    block = block[-height:]
    block_width = max(len(line) for line in block)

    def frame_0() -> Lines:
        for line in block:
            yield line.ljust(block_width, fill_char).center(max_width, fill_char)

    def frame_(n: int) -> Callable[[Lines, Animation], Lines]:
        def anim(frame: Lines, a: Animation) -> Lines:
            return a(frame, n, n_frames)

        return anim

    for f in count():
        yield reduce(frame_(f), animations, frame_0())
