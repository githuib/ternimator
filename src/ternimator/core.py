from contextlib import suppress
from dataclasses import dataclass
from functools import reduce
from itertools import count
from os import get_terminal_size
from typing import TYPE_CHECKING, cast

from .utils import Lines, consume, refresh_lines, write_lines

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

type Animation = Callable[[Lines, int], Lines]


@dataclass(frozen=True)
class AnimParams[T]:
    format_item: Callable[[T], Lines] | None = None
    fps: int | None = None
    keep_last: bool = True
    only_every_nth: int = 1
    crop_to_terminal: bool = False


def animate_iter[T](items: Iterator[T], params: AnimParams = None) -> Iterator[T]:
    if params is None:
        params = AnimParams[T]()
    crop = params.crop_to_terminal

    with suppress(KeyboardInterrupt):
        lines: Lines = []
        for i, item in enumerate(items):
            yield item
            if i % params.only_every_nth == 0:
                # The cast here is somewhat sketchy, but I can't think of a better way
                # to "do nothing" by default (and that mypy would be ok with).
                fmt = params.format_item
                lines = list(fmt(item) if fmt else cast("Lines", item))
                refresh_lines(lines, fps=params.fps, crop_to_terminal=crop)
        if params.keep_last:
            write_lines(lines, crop_to_terminal=crop)


def animate[T](items: Iterator[T], params: AnimParams[T] = None) -> None:
    consume(animate_iter(items, params=params))


def animated_lines(
    lines: Lines, *animations: Animation, fill_char: str = " "
) -> Iterator[Lines]:
    max_width, max_height = get_terminal_size()
    block = list(lines)
    block = block[-min(len(block), max_height - 1) :]
    w = max(len(line) for line in block)

    frame_0 = [line.ljust(w, fill_char).center(max_width, fill_char) for line in block]

    def frame(n: int) -> Callable[[Lines, Animation], Lines]:
        def apply(f: Lines, anim: Animation) -> Lines:
            return anim(f, n)

        return apply

    for n in count():
        yield reduce(frame(n), animations, frame_0)
