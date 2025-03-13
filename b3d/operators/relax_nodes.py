import bpy
import mathutils

MOVE_UNIT = 1


def absolute_location(node: bpy.types.Node):
    if node.parent:
        return absolute_location(node.parent) + node.location
    else:
        return node.location


def calc_node(node: bpy.types.Node, nodes: list[bpy.types.Node], influence, slide_vec, relax_power, collide_power, collide_dist: mathutils.Vector, pull_non_siblings):
    if node.type == 'FRAME':
        return False

    loc = absolute_location(node)
    size = node.dimensions

    offset = mathutils.Vector(slide_vec)

    if relax_power > 0:
        # Relax
        tar_y = 0
        link_cnt = 0
        tar_x_in = loc.x
        has_input = False
        for socket in node.inputs:
            link: bpy.types.NodeLink
            for link in socket.links:
                other = link.from_node
                if not pull_non_siblings and node.parent != other.parent:
                    continue
                loc_other = absolute_location(other)
                size_other = other.dimensions

                x = loc_other.x + size_other.x + collide_dist.x
                if has_input:
                    tar_x_in = max(tar_x_in, x)
                else:
                    tar_x_in = x
                has_input = True

                tar_y += loc_other.y - size_other.y / 2
                link_cnt += 1

        tar_x_out = loc.x
        has_output = False
        for socket in node.outputs:
            for link in socket.links:
                other = link.to_node
                if not pull_non_siblings and node.parent != other.parent:
                    continue
                loc_other = absolute_location(other)
                size_other = other.dimensions

                x = loc_other.x - size.x - collide_dist.x
                if has_output:
                    tar_x_out = min(tar_x_out, x)
                else:
                    tar_x_out = x
                has_output = True

                tar_y += loc_other.y - size_other.y / 2
                link_cnt += 1

        if link_cnt > 0:
            tar_x = tar_x_in * int(has_input) + tar_x_out * int(has_output)
            tar_x /= int(has_input) + int(has_output)
            tar_y /= link_cnt
            tar_y += size.y / 2
            offset.x += (tar_x - loc.x) * relax_power
            offset.y += (tar_y - loc.y) * relax_power

    if collide_power > 0:
        # Collision
        for other in nodes:
            if other == node:
                continue
            if other.type == 'FRAME':
                continue
            collide(loc, absolute_location(other), size, other.dimensions, offset, collide_power, collide_dist)

    if abs(offset.x) > MOVE_UNIT or abs(offset.y) > MOVE_UNIT:
        node.location += offset * influence
        return True
    else:
        return False


def socket_pos(socket: bpy.types.NodeSocket, sockets: list[bpy.types.NodeSocket], size):
    i = 0
    sockets_has_link = [socket for socket in sockets if len(socket.links) > 0]

    for socket in sockets_has_link:
        if socket == socket:
            return (i / len(sockets_has_link)) * size
        i += 1
    return size / 2


def calc_collision_y(node: bpy.types.Node, nodes: list[bpy.types.Node], collide_power, collide_dist):
    if node.type == 'FRAME':
        return False

    loc = absolute_location(node)
    size = node.dimensions

    offset = mathutils.Vector((0, 0))

    # Collision
    for other in nodes:
        if other == node:
            continue
        if other.type == 'FRAME':
            continue
        collide(loc, absolute_location(other), size, other.dimensions, offset, 1, collide_dist, True)

    if abs(offset.y) > MOVE_UNIT:
        node.location += offset * collide_power
        return True
    else:
        return False


def arrange_relax(node: bpy.types.Node, influence, relax_power, distance, clamped_pull):
    if node.type == 'FRAME':
        return False

    loc = absolute_location(node)
    size = node.dimensions

    offset = mathutils.Vector((0, 0))

    # Relax
    tar_y = 0
    tar_x_in = loc.x if clamped_pull else 0
    link_cnt = 0
    has_input = False
    for socket in node.inputs:
        link: bpy.types.NodeLink
        for link in socket.links:
            other = link.from_node
            loc_other = absolute_location(other)
            size_other = other.dimensions

            x = loc_other.x + size_other.x + distance
            if clamped_pull:
                if has_input:
                    tar_x_in = max(tar_x_in, x)
                else:
                    tar_x_in = x
            else:
                tar_x_in += x
            has_input = True

            tar_y += loc_other.y + socket_pos(socket, node.inputs, size.y) - socket_pos(link.from_socket, other.outputs, size_other.y)
            link_cnt += 1

    tar_x_out = loc.x if clamped_pull else 0
    has_output = False
    for socket in node.outputs:
        for link in socket.links:
            other = link.to_node
            loc_other = absolute_location(other)
            size_other = other.dimensions

            x = loc_other.x - size.x - distance
            if clamped_pull:
                if has_output:
                    tar_x_out = min(tar_x_out, x)
                else:
                    tar_x_out = x
            else:
                tar_x_out += x
            has_output = True

            tar_y += loc_other.y + socket_pos(socket, node.outputs, size.y) - socket_pos(link.to_socket, other.inputs, size_other.y)
            link_cnt += 1

    if link_cnt > 0:
        if clamped_pull:
            tar_x = tar_x_in * int(has_input) + tar_x_out * int(has_output)
            tar_x /= int(has_input) + int(has_output)
        else:
            tar_x = (tar_x_in + tar_x_out) / link_cnt
        tar_y /= link_cnt
        offset.x += (tar_x - loc.x) * relax_power
        offset.y += (tar_y - loc.y) * relax_power

    if abs(offset.x) > MOVE_UNIT or abs(offset.y) > MOVE_UNIT:
        node.location += offset * influence
        return True
    else:
        return False


def collide(loc0: mathutils.Vector, loc1: mathutils.Vector, size0: mathutils.Vector, size1: mathutils.Vector, offset: mathutils.Vector, power, dist: mathutils.Vector, only_y=False):
    pos0 = loc0 + size0 / 2
    pos1 = loc1 + size1 / 2
    pos0.y -= size0.y
    pos1.y -= size1.y

    size = (size0 + size1) / 2 + dist
    delta = pos1 - pos0
    inters = size - mathutils.Vector((abs(delta.x), abs(delta.y)))

    if inters.x > 0 and inters.y > 0:
        if inters.y < inters.x or only_y:
            if delta.y > 0:
                inters.y *= -1
            offset.y += inters.y / 2 * power
        else:
            if delta.x > 0:
                inters.x *= -1
            offset.x += inters.x / 2 * power


def step(step_num, iter_num, nodes: list[bpy.types.Node], props: "NodeRelaxProps", root_center, iter_func):
    iter_cnt = 0
    for i in range(iter_num):
        new_center = mathutils.Vector((0, 0))
        node_cnt = 0
        changed = False
        for node in nodes:
            if node.type == 'FRAME':
                continue
            t = i / iter_num
            if iter_func(node, t):
                changed = True
            new_center += absolute_location(node)
            node_cnt += 1

        if not changed:
            break

        new_center /= node_cnt
        slide = root_center - new_center  # Keep Center
        for node in nodes:
            if node.type == 'FRAME':
                continue
            node.location += slide

        iter_cnt += 1
        if iter_cnt > 2:
            iter_cnt = 0
            props.routine_state = str(i) + "/" + str(iter_num) + " " + str(step_num) + "/4"
            yield 1


class RelaxNodesOperator(bpy.types.Operator):
    """Relax Nodes"""
    bl_idname = "node.b3d_relax_nodes"
    bl_label = "Relax Nodes"

    bl_options = {"UNDO", "REGISTER"}

    _timer = None

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return space_data.type == 'NODE_EDITOR' and space_data.edit_tree

    def main_routine(self, context):
        yield 1
        nodes: list[bpy.types.Node] = []
        frame_child_nodes: dict[bpy.types.NodeFrame, list[bpy.types.Node]] = {}
        root_nodes: list[bpy.types.Node] = [node for node in self.tree.nodes if node.parent is None]
        for node in self.tree.nodes:
            if node.parent is not None:
                frame_child_nodes.setdefault(node.parent, []).append(node)
        for node in root_nodes:
            if node.select:
                if node.type == 'FRAME':
                    nodes.extend(frame_child_nodes[node])
                else:
                    nodes.append(node)
        nodes = root_nodes if all(node.type == 'FRAME' for node in nodes) else nodes
        nodes = root_nodes if len(nodes) <= 1 else nodes

        props: NodeRelaxProps = context.scene.node_relax_props
        root_center = mathutils.Vector((0, 0))

        node_cnt = 0
        for node in nodes:
            if node.type == 'FRAME':
                continue
            root_center += absolute_location(node)
            node_cnt += 1
        root_center /= node_cnt

        yield from step(1, props.iterations_s1, nodes, props, root_center, lambda curr_node, e: arrange_relax(curr_node, 1, 1, props.node_margin_x, False))

        yield from step(2, props.iterations_s2, nodes, props, root_center, lambda curr_node, e: arrange_relax(curr_node, 1, 1, props.node_margin_x, True))

        dist = mathutils.Vector((0, props.node_margin_y))
        yield from step(3, props.iterations_s3, nodes, props, root_center, lambda curr_node, e: calc_collision_y(curr_node, nodes, e, dist))

        dist = mathutils.Vector((props.node_margin_x, props.node_margin_y))
        zero_vec = mathutils.Vector((0, 0))
        # yield from step(4, props.iterations_s4, nodes, props, root_center, lambda curr_node, e: calc_node(curr_node, nodes, min(1, e * 2), zero_vec, 0.1, 0.3, dist, True))
        yield from step(4, props.iterations_s4, nodes, props, root_center, lambda curr_node, e: calc_node(curr_node, nodes, min(1, e * 2), zero_vec, 0.2, 1.5, dist, True))

        yield 0

    def finish(self, context: bpy.types.Context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        props: NodeRelaxProps = context.scene.node_relax_props
        props.routine_state = ""

    def modal(self, context, event):
        if event.type == 'TIMER':
            state = next(self.main_coroutine)
            if state == 0:
                self.finish(context)
                return {'FINISHED'}

        if event.type in {'ESC'}:
            self.finish(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        space_data: bpy.types.SpaceNodeEditor = context.space_data
        self.tree = space_data.edit_tree

        wm = context.window_manager
        self.main_coroutine = self.main_routine(context)
        self._timer = wm.event_timer_add(0.001, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class NODE_PT_relax_nodes(bpy.types.Panel):
    bl_label = "Relax Nodes"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'b3d'

    def draw(self, context):
        layout = self.layout
        props: NodeRelaxProps = context.scene.node_relax_props
        layout.operator(RelaxNodesOperator.bl_idname, icon=context.space_data.edit_tree.bl_icon)
        layout.label(text="Node Margin:")
        row = layout.row(align=True)
        row.prop(props, 'node_margin_x', text="X")
        row.prop(props, 'node_margin_y', text="Y")
        if len(props.routine_state) > 0:
            layout.label(text=props.routine_state)
        col = layout.column(align=True)
        col.prop(props, "iterations_s1", text="S1")
        col.prop(props, "iterations_s2", text="S2")
        col.prop(props, "iterations_s3", text="S3")
        col.prop(props, "iterations_s4", text="S4")


class NodeRelaxProps(bpy.types.PropertyGroup):
    node_margin_x: bpy.props.IntProperty(default=30)
    node_margin_y: bpy.props.IntProperty(default=60)
    iterations_s1: bpy.props.IntProperty(min=0, default=0)
    iterations_s2: bpy.props.IntProperty(min=0, default=0)
    iterations_s3: bpy.props.IntProperty(min=0, default=0)
    iterations_s4: bpy.props.IntProperty(min=0, default=60)
    routine_state: bpy.props.StringProperty(default="")


from ..addonutils import registerKeymaps, unregisterKeymaps

addon_keymaps = [
    {
        'idname': RelaxNodesOperator.bl_idname,
        'space_types': ['NODE_EDITOR'],
        'type': 'G',
        'alt': True,
        'shift': True,
    },
]

registered_keymaps = []


def register():
    registerKeymaps(addon_keymaps, registered_keymaps)
    bpy.types.Scene.node_relax_props = bpy.props.PointerProperty(type=NodeRelaxProps)


def unregister():
    unregisterKeymaps(registered_keymaps)
    del bpy.types.Scene.node_relax_props
