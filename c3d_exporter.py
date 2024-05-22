import bpy
import numpy as np
from .c3d.c3d import Writer

def export_c3d(filepath):
    # Create a new C3D writer object
    writer = Writer()

    # Get the scene data from Blender
    scene = bpy.context.scene
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    frame_rate = scene.render.fps

    # Determine the number of points (bones)
    point_count = sum(len(obj.pose.bones) for obj in scene.objects if obj.type == 'ARMATURE')

    # Access the header once and set attributes
    header = writer.header
    header.point_count = point_count
    header.first_frame = frame_start
    header.last_frame = frame_end
    header.scale_factor = -1
    header.frame_rate = frame_rate

    # Collect bone position data over the frames
    frames = frame_end - frame_start + 1
    points = np.zeros((frames, point_count, 3))
    
    # Initialize a list of bone names to keep track of the order of bones
    bone_names = []
    bone_index = 0
    for obj in scene.objects:
        if obj.type == 'ARMATURE':
            for bone in obj.pose.bones:
                bone_names.append((obj.name, bone.name))
                bone_index += 1
    
    # Iterate over frames and collect positions
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bone_index = 0
        for obj in scene.objects:
            if obj.type == 'ARMATURE':
                for bone in obj.pose.bones:
                    bone_world_matrix = obj.matrix_world @ bone.matrix
                    bone_head = bone_world_matrix.to_translation()
                    points[frame - frame_start, bone_index, :] = bone_head
                    bone_index += 1

    # Prepare the frames for the C3D writer
    frame_data = []
    for frame in range(frames):
        point_data = points[frame]
        analog_data = np.zeros((0,))  # Empty analog data as we don't have analog measurements
        frame_data.append((point_data, analog_data))

    # Write the frames to the C3D file
    writer.add_frames(frame_data)

    # Save the C3D file
    with open(filepath, 'wb') as f:
        writer.write(f)
