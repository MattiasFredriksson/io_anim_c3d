# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Script copyright (C) Mattias Fredriksson

# pep8 compliancy:
#   flake8 --ignore E402,F821,F722 .\__init__.py

bl_info = {
    "name": "C3D format",
    "author": "Mattias Fredriksson",
    "version": (0, 1, 0),
    "blender": (2, 83, 0),
    "location": "File > Import",
    "description": "C3D Optical Motion Capture, Point Cloud",
    "warning": "",
    "doc_url": "",
    "tracker_url": "https://github.com/MattiasFredriksson/io_anim_c3d/issues",
    "category": "Import-Export",
}

#######################
# Import & Reload Package
#######################
if "bpy" in locals():
    import importlib
    # Ensure dependency order is correct, to ensure a dependency is updated it must be reloaded first.
    # If imports are done in functions the modules seem to be linked correctly however.
    # ---
    # Reload subdirectory package?
    if "c3d" in locals():
        importlib.reload(c3d)
    # Reload the sub-pacakge modules
    from .c3d import reload as reload_sub
    reload_sub()
    # ---
    # Reload directory modules
    if "pyfuncs" in locals():
        importlib.reload(pyfuncs)
    if "perfmon" in locals():
        importlib.reload(perfmon)
    if "c3d_parse_dictionary" in locals():
        importlib.reload(c3d_parse_dictionary)
    if "c3d_importer" in locals():
        importlib.reload(c3d_importer)

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    # ExportHelper,
    orientation_helper,
)

#######################
# Operator definition
#######################


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportC3D(bpy.types.Operator, ImportHelper):
    """Load a C3D file"""
    bl_idname = "import_anim.c3d"
    bl_label = "Import C3D"
    bl_options = {'UNDO', 'PRESET'}

    directory: StringProperty()

    # File extesion specification and filter
    filename_ext = ".c3d"
    filter_glob: StringProperty(default='*' + filename_ext, options={'HIDDEN'})

    # Properties
    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    use_manual_orientation: BoolProperty(
        name="Manual Orientation",
        description="Specify orientation manually rather then use interpretations from embedded data",
        default=False,
    )

    global_scale: FloatProperty(
        name="Scale",
        description="Scaling factor applied to geometric (spatial) data, multiplied with other (embedded) factors",
        min=0.001, max=1000.0,
        default=1.0,
    )

    create_armature: BoolProperty(
        name="Create Armature",
        description="Generate an armature for the data",
        default=True,
    )

    bone_size: FloatProperty(
        name="Marker Size", default=0.02,
        description="Define the width of each marker",
        min=0.001, max=10.0,
        soft_min=0.01, soft_max=1.0,
    )

    # Scale frame rate to match blender frame rate.
    # This does not reduce the number of keyframes (keyframe reduction through interpolation would be useful)
    adapt_frame_rate: BoolProperty(
        name="Convert Frame Rate",
        description="""Scale sample frame rate to the current Blender frame rate.
                        If False keyframes will be inserted at 1 frame increments""",
        default=True,
    )

    fake_user: BoolProperty(
        name="Fake User",
        description="True to set the fake user flag for generated action sequence(s)",
        default=True,
    )

    # Interpolation settings (link below), there is such thing as to many settings so ignored ones
    # seemingly redundant.
    # https://docs.blender.org/api/current/bpy.types.Keyframe.html#bpy.types.Keyframe.interpolation
    interpolation: EnumProperty(items=(
        ('CONSTANT', "Constant", "Constant, No interpolation"),
        ('LINEAR', "Linear", "Linear interpolation"),
        ('BEZIER', "Bezier", "Smooth interpolation between A and B, with some control over curve shape"),
        # ('SINE', "Sinusoidal", "Sinusoidal easing (weakest, almost linear but with a slight curvature)"),
        ('QUAD', "Quadratic", "Quadratic easing"),
        ('CUBIC', "Cubic", "Cubic easing"),
        # ('QUART', "Quartic", "Quartic easing"),
        # ('QUINT', "Quintic", "Quintic easing"),
        ('CIRC', "Circular", "Circular easing (strongest and most dynamic)"),
        # ('BOUNCE', "Bounce", "Exponentially decaying parabolic bounce, like when objects collide"),
        #  Options with specific settings
        # ('BACK', "Back", "Cubic easing with overshoot and settle"),
        # ('ELASTIC', "Elastic", "Exponentially decaying sine wave, like an elastic band"),
    ),
        name="Interpolation",
        description="Keyframe interpolation",
        default='LINEAR'
    )

    # It should be noted that the standard states two custom representations:
    # 0:  'indicates that the 3D point coordinate is the result of modeling
    #      calculations, interpolation, or filtering'
    # -1: 'is used to indicate that a point is invalid'
    max_residual: FloatProperty(
        name="Maximum Residual", default=0.0,
        description="""Ignore data samples with a residual greater then specified value. If value is equal to 0 all
                       samples will be included. Note that NOT all files record marker residuals""",
        min=0., max=1000000.0,
        soft_min=0., soft_max=100.0,
    )

    min_camera_count: IntProperty(
        name="Min. camera count",
        description="""Minimum number of cameras recording a marker for it to be considered a valid recording
                       (non-occluded). Note that NOT all files record visibility counters""",
        min=0, max=10,
        default=0,
    )

    print_file: BoolProperty(
        name="Print File",
        description="Print file and parameter headers to console",
        default=False,
    )

    load_mem_efficient: BoolProperty(
        name="Memory Efficient",
        description="""Reduce memory footprint of the import process at the cost of ~40 times
                        longer processing time""",
        default=False,
    )

    def draw(self, context):
        pass

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", "directory", "ui_tab", "filepath", "files"))

        from . import c3d_importer
        import os

        if self.files:
            ret = {'CANCELLED'}
            dirname = os.path.dirname(self.filepath)
            for file in self.files:
                path = os.path.join(dirname, file.name)
                if c3d_importer.load(self, context, filepath=path, **keywords) == {'FINISHED'}:
                    ret = {'FINISHED'}
            return ret
        else:
            return c3d_importer.load(self, context, filepath=self.filepath, **keywords)


#######################
# Panels
######################

class C3D_PT_action(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Import Action"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_ANIM_OT_c3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "adapt_frame_rate")
        layout.prop(operator, "fake_user")
        layout.prop(operator, "interpolation")
        layout.prop(operator, "min_camera_count")
        layout.prop(operator, "max_residual")


class C3D_PT_marker_armature(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Create Armature"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_ANIM_OT_c3d"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "create_armature", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.create_armature

        layout.prop(operator, "bone_size")


class C3D_PT_import_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_ANIM_OT_c3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "global_scale")


class C3D_PT_import_transform_manual_orientation(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Manual Orientation"
    bl_parent_id = "C3D_PT_import_transform"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_ANIM_OT_c3d"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "use_manual_orientation", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.enabled = operator.use_manual_orientation

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


class C3D_PT_debug(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Console"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_ANIM_OT_c3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "print_file")
        layout.prop(operator, "load_mem_efficient")

#######################
# Register Menu Items
#######################


def menu_func_import(self, context):
    self.layout.operator(ImportC3D.bl_idname, text="C3D (.c3d)")

# def menu_func_export(self, context):
#    self.layout.operator(ExportC3D.bl_idname, text="C3D (.c3d)")

#######################
# Register Operator
#######################


classes = (
    ImportC3D,
    C3D_PT_action,
    C3D_PT_marker_armature,
    C3D_PT_import_transform,
    C3D_PT_import_transform_manual_orientation,
    C3D_PT_debug,
    # ExportC3D,
)


def register():
    for cl in classes:
        bpy.utils.register_class(cl)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    # bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    # bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cl in classes:
        bpy.utils.unregister_class(cl)


if __name__ == "__main__":
    register()
