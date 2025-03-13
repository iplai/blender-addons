import bpy


def get_displayname_node(node):
    if node.type == 'GROUP':
        if node.node_tree is not None:
            return node.node_tree.name
    if node.type in ['MATH', 'VECT_MATH', 'COMPARE']:
        return node.bl_label + " → " + node.operation.replace("_", " ").title()
    if node.name and node.label and node.name != node.label:
        return f"{node.name} ({node.label})"
    return node.name or node.label or "Unknown"


def get_displayname_socket(socket):
    name = socket.name
    if socket.identifier != socket.name:
        name = f"{socket.name} ({socket.identifier})"
    return name


def show_node_info(self, context):
    node_active = context.active_node
    node_selected = context.selected_nodes

    if len(node_selected) != 1 or node_active is None or not node_active.select:
        return

    layout: bpy.types.UILayout = self.layout.box()
    node_tree = context.space_data.node_tree

    row = layout.row()
    row.label(text=get_displayname_node(node_active), icon=node_tree.bl_icon)
    if node_active.bl_idname == "ShaderNodeValToRGB":
        row.operator("node.copy_color_ramp", icon="COPYDOWN", text='')
        row.operator("node.paste_color_ramp", icon="PASTEDOWN", text='')
    row = layout.row(align=True)
    row.prop(node_active, 'location', text='X', index=0)
    row.prop(node_active, 'location', text='Y', index=1)
    row = layout.row(align=True)
    row.prop(node_active, 'width', text="W")
    row.prop(node_active, 'dimensions', text="H", index=1)

    row = layout.row(align=True)
    icon = "HIDE_OFF" if node_active.show_options else "HIDE_ON"
    row.operator('node.options_toggle', text="Options", icon=icon)
    icon = "HIDE_OFF"
    if any(input.enabled and input.hide for input in node_active.inputs):
        icon = "HIDE_ON"
    row.operator('node.hide_socket_toggle', text="Sockets", icon=icon)
    icon = "MUTE_IPO_OFF" if node_active.mute else "MUTE_IPO_ON"
    row.operator('node.mute_toggle', text="Mute", icon=icon)

    if node_active.inputs:
        socket_count = len(node_active.inputs)
        index_length = len(str(socket_count))
        col = layout.column(align=True)
        box = col.box()
        box.scale_y = 0.75
        box.label(text="Input Sockets:")
        for i, input in enumerate(node_active.inputs):
            row = col.row(align=True)
            box = row.box()
            box.scale_y = 0.5
            row = box.row(align=True)
            row.label(text=f"{i:>0{index_length}}│ {get_displayname_socket(input)}")
            icon = 'HIDE_ON' if not input.enabled or input.hide else 'HIDE_OFF'
            row.prop(input, 'hide', icon_only=True, icon=icon, emboss=False)
            icon = "RADIOBUT_ON" if input.enabled else "RADIOBUT_OFF"
            row.prop(input, "enabled", icon_only=True, icon=icon, emboss=False)

    if node_active.outputs:
        socket_count = max(len(node_active.inputs), len(node_active.outputs))
        index_length = len(str(socket_count))
        col = layout.column(align=True)
        box = col.box()
        box.scale_y = 0.75
        box.label(text="Output Sockets:")
        for i, output in enumerate(node_active.outputs):
            row = col.row(align=True)
            box = row.box()
            box.scale_y = 0.5
            row = box.row(align=True)
            row.label(text=f"{i:>0{index_length}}│ {get_displayname_socket(output)}")
            icon = 'HIDE_ON' if not output.enabled or output.hide else 'HIDE_OFF'
            row.prop(output, 'hide', icon_only=True, icon=icon, emboss=False)
            icon = "RADIOBUT_ON" if output.enabled else "RADIOBUT_OFF"
            row.prop(output, "enabled", icon_only=True, icon=icon, emboss=False)


def register():
    bpy.types.NODE_PT_active_node_generic.prepend(show_node_info)


def unregister():
    bpy.types.NODE_PT_active_node_generic.remove(show_node_info)
