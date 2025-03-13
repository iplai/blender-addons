import os

import bpy


class MyAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # https://docs.blender.org/api/current/bpy.props.html

    filepath: bpy.props.StringProperty(
        default=os.path.join(os.path.expanduser("~"), "Documents", __package__),
        subtype='DIR_PATH',
    )
    addon_pref1: bpy.props.IntProperty(
        default=2,
    )
    addon_pref2: bpy.props.FloatProperty(
        default=0.5,
    )
    addon_pref3: bpy.props.BoolProperty(
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Add-on Preferences View")
        layout.prop(self, "filepath", text="")
        row = layout.row()
        row.prop(self, "addon_pref1")
        row.prop(self, "addon_pref2")
        row.prop(self, "addon_pref3")
