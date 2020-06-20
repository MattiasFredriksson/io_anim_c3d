import mathutils, bpy
import os
from . pyfuncs import *


def load(operator, context, filepath="",
         use_manual_orientation=False,
         axis_forward='-Z',
         axis_up='Y',
         global_scale=1.0,
         interpolation='LINEAR',
         occlude_invalid = True,
         min_camera_count = 0,
         max_residual=0.0,
         print_file=True):
    import numpy as np
    from bpy_extras.io_utils import axis_conversion
    from .c3d_parse_dictionary import C3DParseDictionary

    # World orientation adjustment
    if use_manual_orientation:
        global_orientation = axis_conversion(from_forward=axis_forward, from_up=axis_up).to_4x4()
    else:
        global_orientation = mathutils.Matrix.Identity(4)
    global_orientation = global_orientation @ mathutils.Matrix.Scale(global_scale, 4)



    file_name = os.path.splitext(os.path.basename(filepath))[0]

    parser = C3DParseDictionary(filepath)

    if print_file:
        parser.printFile()

    labels = parser.parseLabels('POINT')
    nlabels = len(labels)

    # Number of frames [first, last] => +1
    # first_frame is the frame index to start parsing from
    # nframes is the number of frames to parse
    first_frame = parser.reader.header.first_frame + 1
    nframes = parser.reader.header.last_frame - first_frame + 1

    # Create an action
    action = create_action(file_name)
    # Generate location (x,y,z) F-Curves for each label
    blen_curves = generate_blend_curves(action, labels, 3, 'pose.bones["%s"].location')
    # Format the curve list in sets of 3
    blen_curves = np.array(blen_curves).reshape(nlabels, 3)

    for i, points, analog in parser.reader.read_frames(copy=False):

        # Determine valid samples
        valid = points[:, 4] >= min_camera_count
        if max_residual > 0.0:
            valid = np.logical_and(points[:, 3] < max_residual, valid)

        # Insert keyframes by iterating over each valid point and channel (x/y/z)
        for value, fc in zip(points[valid, :3].flat, blen_curves[valid].flat):
            fc.keyframe_points.insert(i, value, options={'NEEDED', 'FAST'}).interpolation = interpolation

    # Since we inserted our keyframes in 'FAST' mode, we have to update the fcurves now.
    for fc in blen_curves:
        fc.update()


def create_action(action_name, id_data=None, fake_user=False):
    # Create new action.

    action = bpy.data.actions.new(action_name)
    action.use_fake_user = fake_user

    # If none yet assigned, assign this action to id_data.
    if id_data:
        if not id_data.animation_data:
            id_data.animation_data_create()
        if not id_data.animation_data.action:
            id_data.animation_data.action = action
    return action

def generate_blend_curves(action, labels, grp_channel_count, fc_data_path_str):
    '''
    Generate F-Curves for the action.

    Parameters
    ----
    action:             bpy.types.Action object to generate F-curves for.
    labels:             String label(s) for generated F-Curves, an action group is generated for each label.
    grp_channel_count:  Number of channels generated for each label (group).
    fc_data_path_str:   Unformated data path string used to define the F-Curve data path. If a string format
                        operator (%s) is contained within the string it will be replaced with the label.

                        Valid args are:
                        ----
                        Object anim:
                        'location', 'scale', 'rotation_quaternion', 'rotation_axis_angle', 'rotation_euler'
                        Bone anim:
                        'pose.bones["%s"].location'
                        'pose.bones["%s"].scale'
                        'pose.bones["%s"].rotation_quaternion'
                        'pose.bones["%s"].rotation_axis_angle'
                        'pose.bones["%s"].rotation_euler'

    '''

    # Convert label to iterable tuple
    if not islist(labels): labels = (labels)

    # Generate channels for each label to hold location information
    if '%s' not in fc_data_path_str:
        # No format operator found in the data_path_str used to define F-curves.
        blen_curves = [action.fcurves.new(fc_data_path_str, index=i, action_group=label)
                        for label in labels for i in range(grp_channel_count)]
    else:
        # Format operator found, replace it with label associated with the created F-Curve
        blen_curves = [action.fcurves.new(fc_data_path_str%label, index=i, action_group=label)
                        for label in labels for i in range(grp_channel_count)]
    return blen_curves

def something():
    print(blen_curves)

    #for fc, value in zip(blen_curves, chain(loc, rot, sca)):
    #    fc.keyframe_points.insert(frame, value, options={'NEEDED', 'FAST'}).interpolation = 'LINEAR'



    # Since we inserted our keyframes in 'FAST' mode, we have to update the fcurves now.
    for fc in blen_curves:
        fc.update()


def validate_blend_names(name):
    assert(type(name) == bytes)
    # Blender typically does not accept names over 63 bytes...
    if len(name) > 63:
        import hashlib
        h = hashlib.sha1(name).hexdigest()
        n = 55
        name_utf8 = name[:n].decode('utf-8', 'replace') + "_" + h[:7]
        while len(name_utf8.encode()) > 63:
            n -= 1
            name_utf8 = name[:n].decode('utf-8', 'replace') + "_" + h[:7]
        return name_utf8
    else:
        # We use 'replace' even though FBX 'specs' say it should always be utf8, see T53841.
        return name.decode('utf-8', 'replace')
def blen_read_animations_action_item(action, item, cnodes, fps, anim_offset):
    """
    'Bake' loc/rot/scale into the action,
    taking any pre_ and post_ matrix into account to transform from fbx into blender space.
    """
    from bpy.types import Object, PoseBone, ShapeKey, Material, Camera
    from itertools import chain


    blen_curves = []
    props = []



    for frame, values in blen_read_animations_curves_iter(fbx_curves, anim_offset, 0, fps):

        # Now we have a virtual matrix of transform from AnimCurves, we can insert keyframes!
        loc, rot, sca = mat.decompose()
        if rot_mode == 'QUATERNION':
            if rot_quat_prev.dot(rot) < 0.0:
                rot = -rot
            rot_quat_prev = rot
        elif rot_mode == 'AXIS_ANGLE':
            vec, ang = rot.to_axis_angle()
            rot = ang, vec.x, vec.y, vec.z
        else:  # Euler
            rot = rot.to_euler(rot_mode, rot_eul_prev)
            rot_eul_prev = rot
        for fc, value in zip(blen_curves, chain(loc, rot, sca)):
            fc.keyframe_points.insert(frame, value, options={'NEEDED', 'FAST'}).interpolation = 'LINEAR'

    # Since we inserted our keyframes in 'FAST' mode, we have to update the fcurves now.
    for fc in blen_curves:
        fc.update()
