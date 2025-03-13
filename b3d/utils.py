import typing

import mathutils
from rich import print


class ColorTuple(typing.NamedTuple):
    r: float
    g: float
    b: float
    a: float


def setattrs(obj, **kwargs):
    for name, value in kwargs.items():
        try:
            setattr(obj, name, value)
        except (AttributeError, TypeError) as e:
            print(f"[red]Error setting attribute [bold]{name}[/bold] to [bold]{value}[/bold] on {obj}:[/red][bold cyan] {e}[/bold cyan]")


def hexStr2ColorTuple(hex_color: str):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    a = int(hex_color[6:8], 16) / 255.0 if len(hex_color) > 6 else 1.0
    color = mathutils.Color((r, g, b)).from_srgb_to_scene_linear()
    return ColorTuple(color.r, color.g, color.b, a)


def colorTuple2HexStr(color: ColorTuple):
    r, g, b, a = color
    color = mathutils.Color((r, g, b)).from_scene_linear_to_srgb()
    r, g, b = color.r, color.g, color.b
    items = (round(c * 255) for c in (r, g, b, a))
    hex_color = ''.join(f'{i:02X}' for i in items)
    return '#' + hex_color


def rgb(r: int, g: int, b: int, a: int = 255):
    color = mathutils.Color((r / 255.0, g / 255.0, b / 255.0)).from_srgb_to_scene_linear()
    return ColorTuple(color.r, color.g, color.b, a / 255.0)


def rgba(r: int, g: int, b: int, a: int = 255):
    return rgb(r, g, b, a)
