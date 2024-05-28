import bpy
import numpy as np
from .c3d.c3d import Writer
from . perfmon import PerfMon

def export_c3d(filepath):

    perfmon = PerfMon()
    perfmon.level_up(f'Exporting: {filepath}', True)

    # Get the scene data from Blender
    scene = bpy.context.scene
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    frame_rate = scene.render.fps

    # point_count = sum(len(obj.pose.bones) for obj in scene.objects if obj.type == 'ARMATURE')

    writer = Writer(frame_rate,0)

    perfmon.level_up(f'Collecting labels', True)
    #Initialize a list of bone names to keep track of the order of bones
    bone_names = []
    bone_count = 0
    for obj in scene.objects:
        if obj.type == 'ARMATURE':
            for bone in obj.pose.bones:
                bone_names.append(bone.name)
                bone_count += 1
    perfmon.level_down(f'Collecting labels finished')
    
    perfmon.level_up(f'Collecting frame data', True)
    # Iterate over frames and collect positions
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bone_index = 0
        points = np.zeros((bone_count,5), np.float32)
        analog = np.zeros((0, 0), dtype=np.float32)
        for obj in scene.objects:
            if obj.type == 'ARMATURE':
                for bone in obj.pose.bones:
                    bone_world_matrix = obj.matrix_world @ bone.matrix
                    bone_head = bone_world_matrix.to_translation()
                    points[bone_index, :3] = bone_head.xyz
                    points[bone_index, 3] = 0
                    points[bone_index, 4] = 0
                    bone_index += 1
        frame = np.array([(points, analog)], dtype=object)
        writer.add_frames(frame)
    perfmon.level_down(f'Collecting frame data finished')

    writer.set_point_labels(bone_names)
    # writer.set_analog_labels([])

    # Save the C3D file
    with open(filepath, 'wb') as f:
        writer.write(f)

    perfmon.level_down("Export finished.")
