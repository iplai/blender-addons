import json
import os

import bpy


def load_rules():
    """Load rules from JSON file"""
    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rules_path = os.path.join(addon_dir, "data", "rules.json")
    try:
        with open(rules_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading rules from {rules_path}: {e}")
        return {}


rules = load_rules()


def execute_rules(node_group: bpy.types.NodeTree):
    """Apply rules to nodes"""
    for node in node_group.nodes:
        node.hide = False
        rule = rules.setdefault(node.bl_idname, {})
        if rule.get("hide_unlinked_input_sockets"):
            for socket in node.inputs:
                if socket.enabled and not socket.is_linked:
                    socket.hide = True
        if rule.get("hide_unlinked_output_sockets"):
            for socket in node.outputs:
                if socket.enabled and not socket.is_linked:
                    socket.hide = True
        if rule.get("hide_options"):
            node.show_options = False
        if rule.get("hide_default_vectors"):
            for socket in node.inputs:
                if socket.enabled and not socket.is_linked and socket.type in ['VECTOR', 'ROTATION']:
                    names_zero = ['Vector', 'Location', 'Translation', 'Rotation']
                    if socket.name in names_zero and tuple(socket.default_value) == (0, 0, 0):
                        socket.hide = True
                    if socket.name in ['Scale',] and tuple(socket.default_value) == (1, 1, 1):
                        socket.hide = True


def dispatch_group_input_node(node_group: bpy.types.NodeTree):
    for node in node_group.nodes:
        nodei: bpy.types.Node | None = None
        for socketi in node.inputs:
            if not socketi.is_linked:
                continue
            link: bpy.types.NodeLink
            for link in socketi.links:
                if link.from_node.bl_idname == 'NodeGroupInput':
                    if len(set(l.to_node for o in link.from_node.outputs for l in o.links)) == 1:
                        continue
                    if nodei is None:
                        nodei = node_group.nodes.new('NodeGroupInput')
                        nodei.select = False
                    for socketo in nodei.outputs:
                        if socketo.identifier == link.from_socket.identifier:
                            node_group.links.remove(link)
                            node_group.links.new(socketo, socketi)
                            break

    for node in node_group.nodes:
        if node.bl_idname == 'NodeGroupInput':
            flag = False
            for output_socket in node.outputs:
                if not output_socket.is_linked:
                    output_socket.hide = True
                else:
                    flag = True
            if not flag:
                node_group.nodes.remove(node)


def dispatch_feed_input_node(node_group: bpy.types.NodeTree):
    bl_idnames = ['GeometryNodeInputIndex', 'GeometryNodeInputPosition',
                  'GeometryNodeInputMeshFaceArea', 'ShaderNodeNewGeometry']
    for node in node_group.nodes:
        for socketi in node.inputs:
            if not socketi.is_linked:
                continue
            link: bpy.types.NodeLink = socketi.links[0]
            from_node = link.from_node
            if from_node.bl_idname in bl_idnames:
                feed_node = node_group.nodes.new(from_node.bl_idname)
                feed_node.select = False
                feed_node.location = from_node.location
                for socketo in feed_node.outputs:
                    if socketo.identifier == link.from_socket.identifier:
                        node_group.links.new(socketo, socketi)
                        break


def remove_nodes_without_links(node_group: bpy.types.NodeTree):
    linked_nodes = set()
    for link in node_group.links:
        linked_nodes.add(link.from_node)
        linked_nodes.add(link.to_node)

    unlinked_nodes = set(node_group.nodes) - linked_nodes
    for node in unlinked_nodes:
        node_group.nodes.remove(node)


def reset_node_width(node_group: bpy.types.NodeTree):
    for node in node_group.nodes:
        node.select = False
        if node.bl_idname in ['ShaderNodeMapping', 'ShaderNodeGroup', 'NodeGroupInput']:
            node.width = 140
        if node.type == 'CUSTOM' and node.width != node.bl_width_default:
            node.width = node.bl_width_default


def remove_reroute_nodes(node_group: bpy.types.NodeTree):
    """Remove all reroute nodes and keep the links"""
    for node in node_group.nodes:
        if node.type != 'REROUTE':
            continue

        socketi, socketo = node.inputs[0], node.outputs[0]

        if len(socketi.links) > 0:
            linki = socketi.links[0]

            for linko in socketo.links:
                node_group.links.new(linki.from_socket, linko.to_socket)

        node_group.nodes.remove(node)


def replace_deprecated_nodes(node_group: bpy.types.NodeTree):
    """Replace deprecated nodes with new nodes"""
    for node in node_group.nodes:
        if node.bl_idname == 'FunctionNodeAlignEulerToVector':
            new_node = node_group.nodes.new('FunctionNodeAlignRotationToVector')
            new_node.select = node.select
            new_node.location = node.location
            options = ['axis', 'pivot_axis']
            for option in options:
                setattr(new_node, option, getattr(node, option))
            for i, socketi in enumerate(node.inputs):
                new_node.inputs[i].default_value = socketi.default_value
                if socketi.is_linked:
                    link = socketi.links[0]
                    node_group.links.new(link.from_socket, new_node.inputs[i])
            for i, socketo in enumerate(node.outputs):
                for link in socketo.links:
                    node_group.links.new(new_node.outputs[i], link.to_socket)
            node_group.nodes.remove(node)


def remove_frame_nodes(node_group: bpy.types.NodeTree):
    """Remove all frame nodes"""
    for node in node_group.nodes:
        if node.type == 'FRAME':
            node_group.nodes.remove(node)


class OptimizeNodeTree(bpy.types.Operator):
    """Optimize node tree"""
    bl_idname = "node.b3d_optimize_node_tree"
    bl_label = "Optimize Node Tree"
    bl_options = {'REGISTER', 'UNDO'}

    to_remove_frame_nodes: bpy.props.BoolProperty(default=False)
    to_remove_orphan_nodes: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        space_data: bpy.types.SpaceNodeEditor = bpy.context.space_data
        node_group = space_data.edit_tree
        if self.to_remove_frame_nodes:
            remove_frame_nodes(node_group)
        remove_reroute_nodes(node_group)
        replace_deprecated_nodes(node_group)
        dispatch_group_input_node(node_group)
        dispatch_feed_input_node(node_group)
        execute_rules(node_group)
        reset_node_width(node_group)
        if self.to_remove_orphan_nodes:
            remove_nodes_without_links(node_group)
        return {'FINISHED'}


from ..addonutils import registerKeymaps, unregisterKeymaps

addon_keymaps = [
    {
        'idname': OptimizeNodeTree.bl_idname,
        'space_types': ['NODE_EDITOR'],
        'type': 'Q',
        'alt': True,
        'shift': True,
    },
]

registered_keymaps = []


def register():
    registerKeymaps(addon_keymaps, registered_keymaps)


def unregister():
    unregisterKeymaps(registered_keymaps)
