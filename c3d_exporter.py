import os
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

    curve_names = set()

    for obj in context.scene.objects:
        if obj.type == 'ARMATURE' and obj.animation_data is not None and obj.animation_data.action is not None:
            for fcu in obj.animation_data.action.fcurves:
                curve_names.add(fcu.data_path)

    label_count = len(curve_names)
    curve_names = list(curve_names)

    perfmon.level_down(f'Collecting labels finished')

    perfmon.level_up(f'Collecting frame data', True)

    # Create frames data structure and fill it with default values
    frame_count = frame_end-frame_start

    points = np.zeros((label_count, 5), np.float32)
    points[:, 3] = -1  # Set residual to -1
    keyframes = np.array([points.copy() for _ in range(frame_count)])

    # Process each object in the scene
    for ob in context.scene.objects:
        if ob.type != 'ARMATURE' or ob.animation_data is None or ob.animation_data.action is None:
            continue
        for fcu in ob.animation_data.action.fcurves:
            bone_index = curve_names.index(fcu.data_path)

            for kp in fcu.keyframe_points:
                frame_index = int(kp.co[0]) - frame_start
                if 0 <= frame_index < frame_count:
                    # Fill in points with keyframe value at the appropriate position
                    keyframes[frame_index][bone_index, fcu.array_index] = kp.co[1]
                    keyframes[frame_index][bone_index, 3] = 0 # Set residual
        perfmon.step(f"Collected data from {ob.name} Armature")

    perfmon.level_down(f'Collecting frame data finished')

    perfmon.level_up(f'Applying transformation', True)

    # Scale and orientation
    unit_scale = get_unit_scale(scene) * 1000 # Convert to millimeters TODO: Add unit setting
    scale = global_scale * unit_scale

    # Orient and scale point data
    if use_manual_orientation:
        global_orient = axis_conversion(to_forward=axis_forward, to_up=axis_up)
        global_orient = global_orient @ mathutils.Matrix.Scale(scale, 3)
        # Convert orientation to a numpy array (3x3 rotation matrix).
        global_orient = np.array(global_orient)

        keyframes[..., :3] = keyframes[..., :3] @ global_orient.T
    else:
        keyframes[..., :3] *= scale

    analog = np.zeros((0, 0), dtype=np.float32)
    frames = [(keyframes[i], analog) for i in range(frame_count)]

    perfmon.level_down(f'Transformations applied')

    writer.add_frames(frames)

    labels = [name.split('"')[1] for name in curve_names]
    writer.set_point_labels(labels)
    # writer.set_analog_labels([])

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Save the C3D file
    with open(filepath, 'w+b') as f:
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