from typing import TYPE_CHECKING

from kleur import Color, Colored

from .utils import randf

if TYPE_CHECKING:
    from collections.abc import Callable

    from .utils import Animation, Lines


def moving_forward(frame_0: Lines, n: int, n_frames: int) -> Lines:
    n %= n_frames
    for line in frame_0:
        yield line[-n:] + line[:-n]


def fuck_me_sideways(frame_0: Lines, n: int, n_frames: int) -> Lines:
    n %= n_frames
    lines = list(frame_0)
    height = len(lines) - 1
    half_height = height // 2
    for y, line in enumerate(lines):
        x = n * (half_height - ((half_height + y) % height))
        yield line[x:] + line[:x]


def _colorful(
    colors: Callable[[float, float], tuple[Color, Color]], *, amount_of_hues: int = 360
) -> Animation:
    def anim(frame_0: Lines, n: int, _n_frames: int) -> Lines:
        hue = n / amount_of_hues
        fg, bg = colors(n, hue)
        for line in frame_0:
            yield str(Colored(line, fg, bg))

    return anim


def changing_colors(*, amount_of_hues: int = 360) -> Animation:
    def colors(_n: float, hue: float) -> tuple[Color, Color]:
        fg = Color(hue, lightness=0.75)
        bg = fg.contrasting_hue.contrasting_shade
        return fg, bg

    return _colorful(colors, amount_of_hues=amount_of_hues)


def flashing(
    *,
    amount_of_hues: int = 360,
    intensity: float = 0.03,
    fg: Color = None,
    bg: Color = None,
) -> Animation:
    def colors(n: float, hue: float) -> tuple[Color, Color]:
        flash_ratio = 3
        flash = n % flash_ratio == 0 and randf() < intensity * flash_ratio
        c = Color(hue)
        c_fg, c_bg = fg or c.shade(0.5), bg or c.shade(0.2)
        if flash:
            c_flash = Color(hue + 0.5 if fg else randf())
            c_fg, c_bg = c_flash.shade(0.3), c_flash.shade(0.8)
        return c_fg, c_bg

    return _colorful(colors, amount_of_hues=amount_of_hues)
