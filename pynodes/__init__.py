bl_info = {
    "name": "pynodes",
    "blender": (4, 2, 0),
    "description": "Python nodes for Blender",
    "category": "Node",
    "version": (1, 0, 0),
}

from . import auto_load

auto_load.init()


def register():
    auto_load.register()


def unregister():
    auto_load.unregister()
