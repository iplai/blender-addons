import json
from itertools import chain
import os

import bpy
from mathutils import Vector
from bl_ui.generic_ui_list import draw_ui_list

from .default_presets import default_curvedefs
from .fractals import Generator, get_initiator_matrices
from .subdivide import subdivideCurve


class CurveDefItem(bpy.types.PropertyGroup):
    complex_integer: bpy.props.IntVectorProperty(
        name="Complex Integer",
        size=2,
        default=(0, 1),
        description="Complex integer coordinates used to define how the curve is generated."
    )
    transform_flags: bpy.props.BoolVectorProperty(
        name="Transform Flags",
        size=2,
        default=(False, False),
        description="Reverse flag, Mirror flag"
    )


class CurveDefItemList(bpy.types.UIList):
    bl_idname = "FRACTALFAMILY_UL_CurveDefItemList"

    def draw_item(self, context, layout, data, item: CurveDefItem, icon, active_data, active_property, index, flt_flag=0):
        integer = item.complex_integer
        reverse_flag, mirror_flag = item.transform_flags
        col = layout.column()
        row = col.row(align=True)
        total = len(data.curvedef_items)
        row.label(text=f"{index + 1:2d}/{total:2d}: ({integer[0]}, {integer[1]})")
        icon = 'UV_SYNC_SELECT' if reverse_flag else 'PROP_OFF'
        row.prop(item, "transform_flags", index=0, text="", icon=icon, emboss=False)
        icon = 'MOD_MIRROR' if mirror_flag else 'PROP_OFF'
        row.prop(item, "transform_flags", index=1, text="", icon=icon, emboss=False)


class CurvePresetItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    gene: bpy.props.StringProperty(name="Gene")
    family: bpy.props.StringProperty(name="Family")


class CurvePresetItemList(bpy.types.UIList):
    bl_idname = "FRACTALFAMILY_UL_CurvePresetItemList"

    def draw_item(self, context, layout, data, item: CurvePresetItem, icon, active_data, active_property, index, flt_flag):
        col = layout.column()
        row = col.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text=f'{item.family:10s}')
        row.prop(item, "name", text="", emboss=False)


class InitiatorSplineProp(bpy.types.PropertyGroup):
    curve: bpy.props.PointerProperty(
        type=bpy.types.Curve,
        name="Initiator Spline",
        description="Keep empty to use the segment from origin to the last accumulated cooridnate."
    )
    reverse: bpy.props.BoolProperty(
        name="Reverse",
        default=False,
        description="Use the reversed sequence of the initiator spline points."
    )


def on_preset_active_index_changed(self, context):
    fractalfamily_props: FractalFamilyProps = context.window_manager.fractalfamily_props
    preset_items = fractalfamily_props.preset_items
    active_index = fractalfamily_props.preset_active_index
    preset_item: CurvePresetItem = preset_items[active_index]
    curvedef_items = fractalfamily_props.curvedef_items
    if not preset_item.gene:
        curvedef_items.clear()
        return
    fractalfamily_props.domain = preset_item.family[0]
    fractalfamily_props.curvedef_active_index = 0
    curvedef_items.clear()
    generator = Generator(preset_item.gene)
    for element in generator.elements:
        integer, transform = element.integer, element.transform
        item = curvedef_items.add()
        item.complex_integer = (integer.a, integer.b)
        item.transform_flags = (bool(transform[0]), bool(transform[1]))


class FractalFamilyProps(bpy.types.PropertyGroup):
    preset_items: bpy.props.CollectionProperty(type=CurvePresetItem)
    preset_active_index: bpy.props.IntProperty(default=0, update=on_preset_active_index_changed)

    curvedef_items: bpy.props.CollectionProperty(type=CurveDefItem)
    curvedef_active_index: bpy.props.IntProperty(default=0)

    domain: bpy.props.EnumProperty(
        name="Domain",
        description="The domain of the Complex Integer, Gaussian domain or Eisenstein domain",
        items=[("G", "Gaussian", ""), ("E", "Eisenstein", "")],
        default="G",
    )

    spline_type: bpy.props.EnumProperty(
        name="Spline Type",
        description="Spline type of the generated fractal curves",
        items=[("POLY", "Poly", ""), ("SMOOTH", "Smooth", "")],
        default="POLY",
    )

    level: bpy.props.IntProperty(
        name="Level of fractal curves",
        description="The level of fractal curves, from 1 to 20",
        default=4,
        min=1,
        max=20,
    )

    initiator_spline: bpy.props.PointerProperty(type=InitiatorSplineProp)


class FractalFamilyPanel(bpy.types.Panel):
    bl_idname = "FRACTALFAMILY_PT_main"
    bl_label = "Fractal Family"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"

    def draw(self, context):
        layout = self.layout
        fractalfamily_props: FractalFamilyProps = context.window_manager.fractalfamily_props

        row = layout.row()
        row.label(text='Fractal Curve Presets:')
        row = layout.row()
        row.template_list(
            "FRACTALFAMILY_UL_CurvePresetItemList",
            "",
            fractalfamily_props,
            "preset_items",
            fractalfamily_props,
            "preset_active_index",
            rows=5,
            type='DEFAULT',
            columns=3,
        )
        row = layout.row(align=True)
        row.prop_enum(fractalfamily_props, 'domain', 'G', text='Square Lattice')
        row.prop_enum(fractalfamily_props, 'domain', 'E', text='Hexagonal Lattice')
        row = layout.row()

        draw_ui_list(
            layout, context,
            class_name='FRACTALFAMILY_UL_CurveDefItemList',
            list_path="window_manager.fractalfamily_props.curvedef_items",
            active_index_path="window_manager.fractalfamily_props.curvedef_active_index",
            unique_id="FRACTALFAMILY_CURVE_DEF_LIST",
        )

        generator_items = fractalfamily_props.curvedef_items
        active_index = fractalfamily_props.curvedef_active_index

        if generator_items:
            item = generator_items[active_index]
            row = layout.row()
            box = row.box()
            row1 = box.row(align=True)
            row1.prop(item, "complex_integer", index=0, text="")
            row1.prop(item, "complex_integer", index=1, text="")
            row1.label(text="", icon='BLANK1')
            icon = 'UV_SYNC_SELECT' if item.transform_flags[0] else 'PROP_OFF'
            row1.prop(item, "transform_flags", index=0, text="", icon=icon, emboss=False)
            icon = 'MOD_MIRROR' if item.transform_flags[1] else 'PROP_OFF'
            row1.prop(item, "transform_flags", index=1, text="", icon=icon, emboss=False)
            row.label(text="", icon='BLANK1')
            row = layout.row()
            row.prop(fractalfamily_props, 'level', text='')
            split = row.split(factor=0.5, align=True)
            split.prop_enum(fractalfamily_props, 'spline_type', 'POLY')
            split.prop_enum(fractalfamily_props, 'spline_type', 'SMOOTH')
            row = layout.row()
            row.prop(fractalfamily_props.initiator_spline, 'curve', text='', placeholder="Initiator Spline")
            row.prop(fractalfamily_props.initiator_spline, 'reverse', text='', icon='ARROW_LEFTRIGHT')
            row = layout.row()
            row.operator('object.fractalfamily_create_teragon_curves', text='Create Teragon Curves', icon='CURVE_BEZCURVE')


def load_default_presets():
    items = bpy.context.window_manager.fractalfamily_props.preset_items
    items.clear()
    for info in default_curvedefs:
        item = items.add()
        for key, value in info.items():
            setattr(item, key, value)
    on_preset_active_index_changed(None, bpy.context)


def create_curve_poly(points, name='Curve', noSegs=1, is_closed=False):
    pts: list[Vector] = []
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        for j in range(noSegs):
            t = j / noSegs
            pts.append(p1 + (p2 - p1) * t)
    pts.append(points[-1])
    curve = bpy.data.curves.new(name=name, type="CURVE")
    spline = curve.splines.new("BEZIER")
    bpts = spline.bezier_points
    bpts.add(len(pts) - 1)
    points_unpacked = list(chain.from_iterable(co.to_tuple() for co in pts))
    bpts.foreach_set("co", points_unpacked)
    for i in range(len(bpts)):
        bpts[i].handle_left_type = 'VECTOR'
        bpts[i].handle_right_type = 'VECTOR'
    spline.use_cyclic_u = is_closed
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return obj


def create_curve_smooth(points, name='Curve', noSegs=1, is_closed=False):
    curve = bpy.data.curves.new(name=name, type="CURVE")
    spline = curve.splines.new("BEZIER")
    spline.use_cyclic_u = is_closed
    bpts = spline.bezier_points
    bpts.add(len(points) - 1)
    for i, point in enumerate(points):
        bpts[i].co = point
        bpts[i].handle_left_type = 'AUTO'
        bpts[i].handle_right_type = 'AUTO'
    subdivideCurve(curve, noSegs)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return obj


class FRACTALFAMILY_OT_create_teragon_curves(bpy.types.Operator):
    bl_idname = "object.fractalfamily_create_teragon_curves"
    bl_label = "Create Teragon Curves"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        fractalfamily_props: FractalFamilyProps = context.window_manager.fractalfamily_props
        generator_items = fractalfamily_props.curvedef_items
        chars = [fractalfamily_props.domain,]
        for item in generator_items:
            a, b = item.complex_integer
            r = 1 if item.transform_flags[0] else 0
            m = 1 if item.transform_flags[1] else 0
            chars.extend([str(a), str(b), str(r), str(m)])
        gene = ' '.join(chars)
        generator = Generator(gene)
        if generator.integer.norm == 0:
            self.report({'WARNING'}, f"Curve Family is {generator.integer} with norm 0, which is not a valid fractal curve definition.")
            return {'CANCELLED'}
        subdivision = len(generator.elements)
        is_closed = False
        level = fractalfamily_props.level
        generator.update_level_points(level)
        spline_type = fractalfamily_props.spline_type
        initiator_spline: bpy.types.Curve = fractalfamily_props.initiator_spline.curve
        initiator_points = [Vector(), generator.integer.coord]
        if initiator_spline:
            spline = initiator_spline.splines.active
            if spline.use_cyclic_u:
                is_closed = True
            if spline.type == 'BEZIER' and len(spline.bezier_points) > 1:
                initiator_points = [p.co for p in spline.bezier_points]
            elif len(spline.points) > 1:
                initiator_points = [p.co.to_3d() for p in spline.points]
            if fractalfamily_props.initiator_spline.reverse:
                initiator_points.reverse()
        initiator_matrices = get_initiator_matrices(initiator_points, generator, is_closed)
        for i, points in enumerate(generator.level_points):
            teragon_points = [initiator_points[0]]
            for matrix in initiator_matrices:
                teragon_points.extend(matrix @ point for point in points)
            if is_closed:
                teragon_points.pop()
            # subdivide count is proportional to the level difference
            if spline_type == 'POLY':
                obj = create_curve_poly(teragon_points, f"Teragon {i}", subdivision ** (level - i), is_closed)
            else:
                obj = create_curve_smooth(teragon_points, f"Teragon {i}", subdivision ** (level - i), is_closed)
            obj.select_set(True)
            if i == 0:
                obj.name = "Teragon"
                obj.data.name = "Teragon"
                context.view_layer.objects.active = obj
        return {'FINISHED'}


def register():
    bpy.types.WindowManager.fractalfamily_props = bpy.props.PointerProperty(type=FractalFamilyProps)
    load_default_presets()


def unregister():
    del bpy.types.WindowManager.fractalfamily_props
