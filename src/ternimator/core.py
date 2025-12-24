from collections.abc import Iterable
from contextlib import suppress
from functools import reduce
from itertools import count
from os import get_terminal_size
from typing import TYPE_CHECKING, NamedTuple

from based_utils.cli import Lines, refresh_lines, write_lines
from based_utils.data import consume

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

type Animation = Callable[[Lines, int], Lines]


class AnimParams[T](NamedTuple):
    format_item: Callable[[T], Lines] | None = None
    fps: int | None = None
    keep_last: bool = True
    only_every_nth: int = 1
    crop_to_terminal: bool = False


class InvalidAnimationItemError(Exception):
    def __init__(self, item: object) -> None:
        super().__init__(f"Cannot animate item (when no formatter is given): {item}")


def animate_iter[T](items: Iterator[T], params: AnimParams[T] = None) -> Iterator[T]:
    if params is None:
        params = AnimParams()
    format_item, fps, keep_last, only_every_nth, crop_to_term = params

    with suppress(KeyboardInterrupt):
        lines = []
        for i, item in enumerate(items):
            yield item
            if i % only_every_nth > 0:
                continue

            if format_item:
                formatted = format_item(item)
            elif isinstance(item, Iterable):
                formatted = item
            else:
                raise InvalidAnimationItemError(item)
            lines = list(formatted)
            refresh_lines(lines, fps=fps, crop_to_terminal=crop_to_term)

        if keep_last:
            write_lines(lines, crop_to_terminal=crop_to_term)


def animate[T](items: Iterator[T], params: AnimParams[T] = None) -> None:
    consume(animate_iter(items, params))


def animated_lines(
    lines: Lines | str, *animations: Animation, fill_char: str = " "
) -> Iterator[Lines]:
    if isinstance(lines, str):
        lines = lines.splitlines()

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
