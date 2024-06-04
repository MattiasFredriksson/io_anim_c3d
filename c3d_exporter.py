import mathutils
import numpy as np
from .c3d.c3d import Writer
from . perfmon import PerfMon

def export_c3d(filepath, context, 
            use_manual_orientation = False,
            axis_forward='-Z',
            axis_up='Y',
            global_scale=1.0):
    
    from bpy_extras.io_utils import axis_conversion

    perfmon = PerfMon()
    perfmon.level_up(f'Exporting: {filepath}', True)

    # Get the scene data from Blender
    scene = context.scene
    frame_start = scene.frame_start
    frame_end = scene.frame_end+1
    frame_rate = scene.render.fps


    writer = Writer(frame_rate,0)

    perfmon.level_up(f'Collecting labels', True)
    #Initialize a list of bone names to keep track of the order of bones

    labels = []
    label_count = 0
    for obj in context.scene.objects:
        if obj.type == 'ARMATURE' and obj.animation_data is not None and obj.animation_data.action is not None:
            for fcu in obj.animation_data.action.fcurves:
                data_path_split = fcu.data_path.split('"')
                if len(data_path_split) <= 1:
                    continue
                bone_name = data_path_split[1]
                if bone_name not in labels:
                    labels.append(bone_name)
                    label_count += 1

    perfmon.level_down(f'Collecting labels finished')

    perfmon.level_up(f'Collecting frame data', True)

    # Create frames data structure and fill it with default values
    frame_count = frame_end-frame_start

    points = np.zeros((label_count, 5), np.float32)
    points[:, 3] = -1  # Set residual to -1

    analog = np.zeros((0, 0), dtype=np.float32)
    frames = [(points.copy(), analog.copy()) for _ in range(frame_count)]

    # Process each object in the scene
    for ob in context.scene.objects:
        if ob.type != 'ARMATURE' or ob.animation_data is None or ob.animation_data.action is None:
            continue
        for fcu in ob.animation_data.action.fcurves:
            # Extract the bone name from the data path
            # Example data path: 'pose.bones["Bone"].location'
            data_path_split = fcu.data_path.split('"')
            if len(data_path_split) <= 1:
                continue
            bone_name = data_path_split[1]
            bone_index = labels.index(bone_name)

            for kp in fcu.keyframe_points:
                frame_index = int(kp.co[0]) - frame_start
                if 0 <= frame_index < frame_count:
                    # Fill in points with keyframe value at the appropriate position
                    frames[frame_index][0][bone_index, fcu.array_index] = kp.co[1]
                    frames[frame_index][0][bone_index, 3] = 0 # Set residual
        perfmon.step(f"Collected data from {ob.name} Armature")

    perfmon.level_down(f'Collecting frame data finished')

    perfmon.level_up(f'Applying transformation', True)

    # Scale and orientation
    unit_scale = get_unit_scale(scene) * 1000 # Convert to millimeters TODO: Add unit setting
    scale = global_scale * unit_scale

    if use_manual_orientation:
        global_orient = axis_conversion(to_forward=axis_forward, to_up=axis_up)
        global_orient = global_orient @ mathutils.Matrix.Scale(scale, 3)
    else:
        global_orient = mathutils.Matrix.Scale(scale,3)
    # Convert orientation to a numpy array (3x3 rotation matrix).
    global_orient = np.array(global_orient)

    # Orient and scale point data
    for frame in frames:
        for bone in frame[0]:
            bone[:3] = np.matmul(global_orient, bone[:3])

    perfmon.level_down(f'Transformations applied')

    writer.add_frames(frames)


    writer.set_point_labels(labels)
    # writer.set_analog_labels([])

    # Save the C3D file
    with open(filepath, 'wb') as f:
        writer.write(f)

    perfmon.level_down("Export finished.")


def get_unit_scale(scene):
    # Determine the unit scale to convert to meters
    unit_scale = scene.unit_settings.scale_length
    if scene.unit_settings.system == 'METRIC':
        unit_conversion_factor = unit_scale
    elif scene.unit_settings.system == 'IMPERIAL':
        unit_conversion_factor = 25.4 * 12 * unit_scale / 1000  # Convert feet to meters
    else:
        unit_conversion_factor = unit_scale  # Default to meters if no system is set
    return unit_conversion_factor