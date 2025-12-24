from collections.abc import Iterable
from functools import cache, reduce
from itertools import count
from os import get_terminal_size, terminal_size
from typing import TYPE_CHECKING, NamedTuple

from based_utils.class_utils import Check
from based_utils.cli import Lines, refresh_lines, write_lines
from based_utils.data import consume
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


type Animation = Callable[[Lines, int], Lines]


class AnimParams[T](NamedTuple):
    format_item: Callable[[T], Lines] | None = None
    fps: int | None = None
    keep_last: bool = True
    loop: bool = False
    only_every_nth: int = 1
    crop_to_terminal: bool = False


class InvalidAnimationItemError(Exception):
    def __init__(self, item: object) -> None:
        super().__init__(f"Cannot animate item (when no formatter is given): {item}")


STOP_ANIMATION = object()


def animate_iter[T](items: Iterator[T], params: AnimParams[T] = None) -> Iterator[T]:
    fmt_item, fps, keep_last, loop, only_every_nth, crop = params or AnimParams()

    lines: list[object] = []
    interrupted = Check()

    def on_release(key: Key | KeyCode | None) -> None:
        if key == Key.esc:
            interrupted.check()

    keyboard.Listener(on_release=on_release, suppress=True).start()

    for i, item in enumerate(items):
        yield item
        if interrupted:
            if loop:
                break
            continue
        if i % only_every_nth > 0:
            continue

        if fmt_item:
            formatted = fmt_item(item)
        elif isinstance(item, Iterable):
            formatted = item
        else:
            raise InvalidAnimationItemError(item)

        lines = list(formatted)
        refresh_lines(lines, fps=fps, crop_to_terminal=crop)

    if keep_last:
        write_lines(lines, crop_to_terminal=crop)


def animate[T](items: Iterator[T], params: AnimParams[T] = None) -> None:
    consume(animate_iter(items, params))


@cache
def term_size() -> terminal_size:
    return get_terminal_size()


def animated_lines(
    lines: Lines | str, *animations: Animation, fill_char: str = " "
) -> Iterator[Lines]:
    if isinstance(lines, str):
        lines = lines.splitlines()

    max_width, max_height = term_size()
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
