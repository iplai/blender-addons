bl_info = {
    "name": "b3d",
    "author": "any",
    "description": "Personal Blender addon",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "category": "Generic"
}


from . import auto_load

auto_load.init()


def register():
    auto_load.register()


def unregister():
    auto_load.unregister()
