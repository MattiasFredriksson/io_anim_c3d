import bpy
import numpy as np
from .c3d.c3d import Writer

def export_c3d(filepath):

    # Get the scene data from Blender
    scene = bpy.context.scene
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    frame_rate = scene.render.fps

    # Determine the number of points (bones)
    point_count = sum(len(obj.pose.bones) for obj in scene.objects if obj.type == 'ARMATURE')

    frame_rate = 1
    point_count = 10

    # Create a new C3D writer object
    writer = Writer(frame_rate,0)

    # Access the header once and set attributes
    # header = writer.header
    # header.point_count = point_count
    # header.analog_count = point_count
    # header.first_frame = frame_start
    # header.last_frame = frame_end
    # header.scale_factor = -1
    # header.frame_rate = frame_rate

    points = np.zeros((10, 5), np.float32)
    analog = np.zeros((0, 0), dtype=np.float32)
    frame = np.array([(points, analog)], dtype=object)

    writer.set_point_labels(["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    #writer.set_analog_labels = ["aA", "aB", "aC", "aD", "aE", "aF", "aG", "aH", "aI", "aJ"]
    writer.set_analog_labels = []

    writer.add_frames(frame)

        
    # Initialize a list of bone names to keep track of the order of bones
    # bone_names = []
    # bone_index = 0
    # for obj in scene.objects:
    #     if obj.type == 'ARMATURE':
    #         for bone in obj.pose.bones:
    #             bone_names.append((obj.name, bone.name))
    #             bone_index += 1
    
    # # Iterate over frames and collect positions
    # for frame in range(frame_start, frame_end + 1):
    #     scene.frame_set(frame)
    #     bone_index = 0
    #     frame_data = np.zeros((point_count,3))
    #     for obj in scene.objects:
    #         if obj.type == 'ARMATURE':
    #             for bone in obj.pose.bones:
    #                 bone_world_matrix = obj.matrix_world @ bone.matrix
    #                 bone_head = bone_world_matrix.to_translation()
    #                 frame_data[bone_index] = bone_head.xyz
    #                 bone_index += 1
    #                 writer.add_frames(frame_data)

    # Save the C3D file
    with open(filepath, 'wb') as f:
        writer.write(f)
