import math
from typing import TYPE_CHECKING, Literal

import bpy

if TYPE_CHECKING:
    from .preference import MyAddonPreferences


def prefs() -> 'MyAddonPreferences':
    return bpy.context.preferences.addons[__package__].preferences


def get_or_create_keymap(space_type: str):
    key = space_type.replace("_", " ").title()
    if space_type == 'PROPERTIES':
        key = 'Property Editor'
    if space_type == 'VIEW_3D':
        key = '3D View'
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get(key)
    if not km:
        km = wm.keyconfigs.addon.keymaps.new(name=key, space_type=space_type)
    return km


def registerKeymaps(addon_keymaps: list[dict], registered_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]]):
    addon_keymaps = [item for item in addon_keymaps if 'idname' in item]
    keymaps_dict: dict[str, bpy.types.KeyMap] = {}
    for akm in addon_keymaps:
        for space_type in akm['space_types']:
            if space_type not in keymaps_dict:
                keymaps_dict[space_type] = get_or_create_keymap(space_type)
    for akm in addon_keymaps:
        for space_type in akm['space_types']:
            km = keymaps_dict[space_type]
            kmi = km.keymap_items.new(akm['idname'], akm['type'], 'PRESS', alt=akm.get('alt', False), shift=akm.get('shift', False), ctrl=akm.get('ctrl', False))
            if 'props' in akm and isinstance(akm['props'], dict):
                for prop_name, prop_value in akm['props'].items():
                    setattr(kmi.properties, prop_name, prop_value)
            registered_keymaps.append((km, kmi))


def unregisterKeymaps(registered_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]]):
    for km, kmi in registered_keymaps:
        km.keymap_items.remove(kmi)
    registered_keymaps.clear()


def show_message_box(message="", title="Message Box", icon: Literal['NONE', 'QUESTION', 'ERROR', 'WARNING', 'INFO'] = 'INFO'):
    """A hack that uses a popup menu as a message box"""

    def draw(self: bpy.types.UIPopupMenu, context):
        for line in message.split('\n'):
            self.layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
