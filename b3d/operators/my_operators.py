import bpy

from ..addonutils import prefs, registerKeymaps, unregisterKeymaps
from ..preference import MyAddonPreferences


class MyAddonProperties(bpy.types.PropertyGroup):
    color_ramp_copied: bpy.props.BoolProperty(default=False)

# This Example Operator will scale up the selected object


class ExampleOperator(bpy.types.Operator):
    '''测试 Operator'''
    bl_idname = "object.example_ops"
    bl_label = "Example Operator"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        addon_prefs = prefs()
        assert isinstance(addon_prefs, MyAddonPreferences)
        # use operator
        # bpy.ops.transform.resize(value=(2, 2, 2))
        # manipulate the scale directly
        context.active_object.scale *= addon_prefs.addon_pref1
        return {'FINISHED'}


class SwitchComfyUIEditor(bpy.types.Operator):
    bl_idname = "node.switch_to_comfyui_editor"
    bl_label = "Switch to ComfyUI Editor"

    def execute(self, context):
        bpy.context.area.ui_type = "CFNodeTree"
        return {"FINISHED"}


class EvaluateExpression(bpy.types.Operator):
    """简单表达式测试"""
    bl_idname = "dev.expr_test"
    bl_label = "Expression Test"
    bl_options = {'REGISTER', 'UNDO'}

    expression: bpy.props.StringProperty(
        name="Expression",
        description="Python expression to evaluate",
        default="context.area.ui_type",
    )

    local_vars = {"bpy": bpy, "C": bpy.context, 'D': bpy.data}

    def execute(self, context):
        self.local_vars.update({"context": context})
        try:
            result = eval(self.expression, globals(), self.local_vars)
            self.report({'INFO'}, f"Result: {result}")
        except Exception as e:
            self.report({'ERROR'}, f"Error: {e}")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class SwitchLanguage(bpy.types.Operator):
    """切换中英文"""
    bl_idname = "ui.switch_language"
    bl_label = "Switch Language"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        current_language = context.preferences.view.language
        if current_language == "zh_HANS":
            context.preferences.view.language = "en_US"
        else:
            context.preferences.view.language = "zh_HANS"
        return {'FINISHED'}


class SetSceneFrameEnd(bpy.types.Operator):
    """Set Scene Frame End"""
    bl_idname = "scene.set_frame_end"
    bl_label = "Set Scene Frame End"

    def execute(self, context):
        if context.scene.frame_end != 3000:
            context.scene.frame_end = 3000
        else:
            context.scene.frame_end = 250

        def draw(self: bpy.types.UIPopupMenu, context):
            self.layout.prop(context.scene, "frame_end")
        bpy.context.window_manager.popup_menu(draw, title="Set frame end", icon='BLENDER')

        return {'FINISHED'}


class DuplicateOrFullscreenWindow(bpy.types.Operator):
    """Duplicate or Fullscreen the current window"""
    bl_idname = 'window.duplicate_or_fullscreen'
    bl_label = 'Duplicate or Fullscreen'

    def execute(self, context):
        area_count = len(context.screen.areas)
        if area_count == 1:
            if context.window.height < 1080:
                bpy.ops.wm.window_fullscreen_toggle()
            else:
                bpy.ops.wm.window_close()
        else:
            bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        return {'FINISHED'}


class CopyNodeBlIdname(bpy.types.Operator):
    """Copy Node bl_idname"""
    bl_idname = "node.copy_bl_idname"
    bl_label = "Copy Node bl_idname"

    def execute(self, context):
        node = context.active_node
        if node is not None:
            context.window_manager.clipboard = node.bl_idname
        return {'FINISHED'}


class CopyColorRamp(bpy.types.Operator):
    """Copy color ramp to clipboard as python list"""
    bl_idname = 'node.copy_color_ramp'
    bl_label = 'Copy Color Ramp'

    def execute(self, context):
        addon_props = context.window_manager.myaddon_props
        node: bpy.types.ShaderNodeValToRGB = context.active_node
        color_ramp = node.color_ramp
        colors = []
        for element in color_ramp.elements:
            colors.append((round(element.position, 3), tuple(element.color)))
        context.window_manager.clipboard = repr(colors)
        addon_props.color_ramp_copied = True
        return {'FINISHED'}


class PasteColorRamp(bpy.types.Operator):
    """Paste color ramp from clipboard as python list"""
    bl_idname = 'node.paste_color_ramp'
    bl_label = 'Paste Color Ramp'

    @classmethod
    def poll(cls, context):
        addon_props = context.window_manager.myaddon_props
        return addon_props.color_ramp_copied

    def execute(self, context):
        node: bpy.types.ShaderNodeValToRGB = context.active_node
        color_ramp = node.color_ramp
        try:
            colors = eval(context.window_manager.clipboard)
            assert isinstance(colors, list), "Input must be a list"
            if not colors:
                raise ValueError("Color list cannot be empty")
            for pos, color in colors:
                assert isinstance(pos, (int, float)), \
                    f"Position must be a number, got {type(pos)}"
                assert isinstance(color, tuple), \
                    f"Color must be a tuple, got {type(color)}"
                assert len(color) >= 3, \
                    f"Color must have at least 3 elements, got {len(color)}"
        except (SyntaxError, AssertionError, ValueError) as e:
            self.report({'ERROR'}, f"Error: {e}")
            return {'CANCELLED'}
        for _ in range(len(colors) - len(color_ramp.elements)):
            color_ramp.elements.new(0)
        for i, (position, color) in enumerate(colors):
            element = color_ramp.elements[i]
            element.position = position
            element.color = color
        return {'FINISHED'}


class ShowWireframeToggle(bpy.types.Operator):
    """Show Wireframe Toggle"""
    bl_idname = "view3d.show_wireframe_toggle"
    bl_label = "Show Wireframe Toggle"

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active is not None

    def execute(self, context):
        context.view_layer.objects.active.show_wire = not context.view_layer.objects.active.show_wire
        return {'FINISHED'}


class SwitchRenderingEngine(bpy.types.Operator):
    """Switch Rendering Engine between Cycles and Eevee"""
    bl_idname = "b3d.switch_rendering_engine"
    bl_label = "Switch Rendering Engine"
    bl_options = {'REGISTER', 'UNDO'}

    frame_rate: bpy.props.IntProperty(
        name="Frame Rate",
        description="Frame rate for rendering",
        default=30,
    )

    def execute(self, context):
        context.scene.render.fps = self.frame_rate
        if context.scene.render.engine == "CYCLES":
            context.scene.render.engine = "BLENDER_EEVEE_NEXT"
            context.scene.eevee.use_raytracing = True
        else:
            context.scene.render.engine = "CYCLES"
            context.scene.cycles.device = "GPU"
        return {'FINISHED'}


class CopyObjectNameToData(bpy.types.Operator):
    """Rename the object data of each selected object to match the object name"""

    bl_idname = "object.copy_object_name_to_data"
    bl_label = "Copy Object Name to Data"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Get the valid object IDs from the Outliner selection.
        objects: list[bpy.types.Object] = [obj for obj in context.selected_ids if obj.id_type == "OBJECT"]

        self.copy_object_name_to_data(objects)
        return {"FINISHED"}

    def copy_object_name_to_data(self, objects: list[bpy.types.Object]) -> None:
        for object in objects:
            data = getattr(object, "data", None)
            if data:
                data.name = object.name


def draw_node_header_menu(self: bpy.types.Menu, context):
    self.layout.operator("outliner.orphans_purge", icon='TRASH', text="", emboss=False).do_recursive = True


def draw_node_context_menu(self: bpy.types.Menu, context: bpy.types.Context):
    """Add menu item to context menu of node editor"""
    node = context.active_node
    if node and node.bl_idname == 'ShaderNodeValToRGB':
        self.layout.operator('node.copy_color_ramp', text='Copy Color Ramp', icon='COPYDOWN')
        self.layout.operator('node.paste_color_ramp', text='Paste Color Ramp', icon='PASTEDOWN')


addon_keymaps = [
    {
        'idname': 'node.switch_to_comfyui_editor',
        'space_types': ['NODE_EDITOR'],
        'type': 'FIVE',
        'props': {},
    },
    {
        'idname': 'dev.expr_test',
        'space_types': ['NODE_EDITOR'],
        'type': 'T',
        'alt': True,
        'shift': True,
    },
    {
        'idname': 'scene.set_frame_end',
        'space_types': ['VIEW_3D'],
        'type': 'E',
        'alt': True,
        'shift': True,
    },
    {
        'idname': 'window.duplicate_or_fullscreen',
        'space_types': ['NODE_EDITOR', 'VIEW_3D', 'CONSOLE'],
        'type': 'D',
        'alt': True,
        'shift': True,
    },
    {
        # 'idname': 'ui.switch_language',
        'space_types': ['VIEW_3D', 'NODE_EDITOR', 'OUTLINER', 'PROPERTIES'],
        'type': 'R',
        'alt': True,
        'shift': True,
    },
    {
        'idname': 'view3d.show_wireframe_toggle',
        'space_types': ['VIEW_3D'],
        'type': 'W',
        'alt': True,
        'shift': True,
    },
    {
        # 'idname': 'b3d.switch_rendering_engine',
        'space_types': ['VIEW_3D'],
        'type': 'Q',
        'alt': True,
        'shift': True,
    }
]

registered_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def register():
    bpy.types.WindowManager.myaddon_props = bpy.props.PointerProperty(type=MyAddonProperties)
    bpy.types.NODE_HT_header.append(draw_node_header_menu)
    bpy.types.NODE_MT_context_menu.prepend(draw_node_context_menu)
    registerKeymaps(addon_keymaps, registered_keymaps)


def unregister():
    del bpy.types.WindowManager.myaddon_props
    bpy.types.NODE_HT_header.remove(draw_node_header_menu)
    bpy.types.NODE_MT_context_menu.remove(draw_node_context_menu)
    unregisterKeymaps(registered_keymaps)
