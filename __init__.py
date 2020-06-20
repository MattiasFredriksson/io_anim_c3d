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

# <pep8 compliant>

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
# Import Package
#######################
import bpy

if "bpy" in locals():
    import importlib
    if "c3d_importer" in locals():
        importlib.reload(c3d_importer)
    if "c3d_parse_dictionary" in locals():
        importlib.reload(c3d_parse_dictionary)
    if "pyfuncs" in locals():
        importlib.reload(pyfuncs)
    importlib.reload(c3d.__init__)


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
        ExportHelper,
        orientation_helper,
        path_reference_mode,
        axis_conversion,
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
    filter_glob: StringProperty(default="*"+filename_ext, options={'HIDDEN'})

    # Properties
    files: CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )

    global_scale: FloatProperty(
            name="Scale",
            min=0.001, max=1000.0,
            default=1.0,
            )

    interpolation: EnumProperty(
            items=(('LINEAR', "Linear", "Linear interpolation (default)"),
            ('CUBIC', "Cubic", "Cubic interpolation")),
            name="Interpolation",
            default='LINEAR'
            )

    # It should be noted that the standard states two custom representations:
    # 0:  'indicates that the 3D point coordinate is the result of modeling
    #      calculations, interpolation, or filtering'
    # -1: 'is used to indicate that a point is invalid'
    max_residual: FloatProperty(
        name="Maximum Residual", default=0.0,
        description="Ignore data samples with a residual greater then specified value. If 0 all samples are included.",
        min=0., max=1000000.0,
        soft_min=0., soft_max=100.0,
    )


    min_camera_count: IntProperty(
        name="Minimum camera count",
        description="Minimum number of cameras recording a marker for it to be considered a valid recording (non-occluded). Not all files record visibility counters.",
        min=0, max=10,
        default=0,
        )

    # This is probably a redundant setting as an invalid point is generally not recorded by a camera
    occlude_invalid: BoolProperty(
            name="Occlude Invalid",
            description="Handle invalid points as occluded",
            default=True,
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
# Register Menu Items
#######################

def menu_func_import(self, context):
    self.layout.operator(ImportC3D.bl_idname, text="C3D (.c3d)")

#def menu_func_export(self, context):
#    self.layout.operator(ExportC3D.bl_idname, text="C3D (.c3d)")


#######################
# Register Operator
#######################

operators = (
    ImportC3D,
    #ExportC3D,
)

def register():
    for op in operators:
        bpy.utils.register_class(op)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    #bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    #bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for op in operators:
        bpy.utils.unregister_class(op)


if __name__ == "__main__":
    register()
