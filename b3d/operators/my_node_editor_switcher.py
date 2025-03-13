import bpy


class NodeEditorSwitcherBase(bpy.types.Operator):
    bl_idname = "node.switch_base"  # Will be overridden
    bl_label = "Switch Node Editor"  # Will be overridden

    ui_type: str = "ShaderNodeTree"
    shader_type: str = None

    def execute(self, context):
        context.area.ui_type = self.ui_type
        if self.shader_type:
            context.space_data.shader_type = self.shader_type
        return {"FINISHED"}


class SwitchShaderEditor(NodeEditorSwitcherBase):
    bl_idname = "node.switch_to_shader_editor"
    bl_label = "Switch to Shader Editor"
    shader_type = "OBJECT"


class SwitchWorldEditor(NodeEditorSwitcherBase):
    bl_idname = "node.switch_to_world_editor"
    bl_label = "Switch to World Editor"
    shader_type = "WORLD"


class SwitchCompositorEditor(NodeEditorSwitcherBase):
    bl_idname = "node.switch_to_compositor_editor"
    bl_label = "Switch to Compositor Editor"
    ui_type = "CompositorNodeTree"


class SwitchGeometryEditor(NodeEditorSwitcherBase):
    bl_idname = "node.switch_to_geometry_editor"
    bl_label = "Switch to Geometry Editor"
    ui_type = "GeometryNodeTree"


def draw_switch_buttons(self: bpy.types.Header, context: bpy.types.Context):
    layout = self.layout
    current_ui = context.area.ui_type
    shader_type = getattr(context.space_data, 'shader_type', None)

    items = [
        {
            "operator": "node.switch_to_geometry_editor",
            "icon": "GEOMETRY_NODES",
            "depress": current_ui == "GeometryNodeTree"
        },
        {
            "operator": "node.switch_to_shader_editor",
            "icon": "NODE_MATERIAL",
            "depress": current_ui == "ShaderNodeTree" and shader_type == "OBJECT"
        },
        {
            "operator": "node.switch_to_world_editor",
            "icon": "WORLD_DATA",
            "depress": current_ui == "ShaderNodeTree" and shader_type == "WORLD"
        },
        {
            "operator": "node.switch_to_compositor_editor",
            "icon": "NODE_COMPOSITING",
            "depress": current_ui == "CompositorNodeTree"
        },
    ]

    row = layout.row(align=True)
    for item in items:
        row.operator(**item, text="")


def register():
    bpy.types.NODE_HT_header.append(draw_switch_buttons)


def unregister():
    bpy.types.NODE_HT_header.remove(draw_switch_buttons)
