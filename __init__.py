# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

# <pep8-80 compliant>

# This script was developed with financial support from the Foundation for
# Science and Technology of Portugal, under the grant SFRH/BD/66452/2009.


bl_info = {
    "name": "C3D Graphics Lab Motion Capture file (.c3d)",
    "author": "Daniel Monteiro Basso <daniel@basso.inf.br>",
    "version": (2015, 5, 5, 1),
    "blender": (2, 74, 1),
    "location": "File > Import",
    "description": "Imports C3D Graphics Lab Motion Capture files",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/C3D_Importer",
    "category": 'Import-Export',
}


import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
)

import os
import math
from mathutils import Vector
from . import import_c3d


class C3DAnimateCloud(bpy.types.Operator):
    """
        Animate the Marker Cloud
    """
    bl_idname = "import_anim.c3danim"
    bl_label = "Animate C3D"

    is_armature = False
    markerset = None
    uname = None
    curframe = 0
    fskip = 0
    scale = 0
    timer = None
    Y_up = False

    def update_empty(self, fno, ml, m):
        name = self.unames[self.prefix + ml]
        o = bpy.context.scene.objects[name]
        p = Vector(m.position) * self.scale
        o.location = Vector((p[0], -p[2], p[1])) if self.Y_up else p
        o.keyframe_insert('location', frame=fno)

    def update_bone(self, fno, ml, m, bones):
        name = self.prefix + ml
        if name not in bones:
            return
        b = bones[name]
        p = Vector(m.position) * self.scale
        b.matrix.translation = Vector((p[0], -p[2], p[1])) if self.Y_up else p
        b.keyframe_insert('location', -1, fno, name)

    def update_frame(self):
        fno = self.curframe
        if not self.use_frame_no:
            fno = (self.curframe - self.markerset.startFrame) / self.fskip
        for i in range(self.fskip):
            self.markerset.readNextFrameData()
        if self.is_armature:
            bones = bpy.context.active_object.pose.bones
        for ml in self.markerset.markerLabels:
            m = self.markerset.getMarker(ml, self.curframe)
            if m.confidence < self.confidence:
                continue
            if self.is_armature:
                self.update_bone(fno, ml, m, bones)
            else:
                self.update_empty(fno, ml, m)

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)
        if event.type == 'TIMER':
            if self.curframe > self.markerset.endFrame:
                return self.cancel(context)
            self.update_frame()
            self.curframe += self.fskip
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.timer = context.window_manager.\
            event_timer_add(0.001, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
        context.window_manager.event_timer_remove(self.timer)
        return {'FINISHED'}



def menu_func(self, context):
    self.layout.operator(C3DImporter.bl_idname,
                         text="Graphics Lab Motion Capture (.c3d)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
