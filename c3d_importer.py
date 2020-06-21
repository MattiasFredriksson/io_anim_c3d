import mathutils, bpy
import os
from . pyfuncs import *


def load(operator, context, filepath="",
         use_manual_orientation=False,
         axis_forward='-Z',
         axis_up='Y',
         global_scale=1.0,
         create_armature=True,
         fake_user=True,
         interpolation='LINEAR',
         occlude_invalid = True,
         min_camera_count = 0,
         max_residual=0.0,
         print_file=False):
    import numpy as np
    from bpy_extras.io_utils import axis_conversion
    from .c3d_parse_dictionary import C3DParseDictionary
    from . perfmon import PerfMon

    # Action id
    file_id = os.path.basename(filepath)
    file_name = os.path.splitext(file_id)[0]

    # Monitor performance
    perfmon = PerfMon()
    perfmon.level_up('Importing: %s ...' % file_id, True)

    # World orientation adjustment
    if use_manual_orientation:
        global_orientation = axis_conversion(from_forward=axis_forward, from_up=axis_up).to_4x4()
    else:
        global_orientation = mathutils.Matrix.Identity(4)
    global_orientation = global_orientation @ mathutils.Matrix.Scale(global_scale, 4)



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

    # Create an armature adapted to the data (if specified)
    arm_obj = None
    if create_armature:
        arm_obj = create_armature_object(context, file_name)
        add_empty_armature_bones(context, arm_obj, labels, 0.1)


    # Create an action
    action = create_action(file_name, arm_obj, fake_user)
    # Generate location (x,y,z) F-Curves for each label
    blen_curves_arr = generate_blend_curves(action, labels, 3, 'pose.bones["%s"].location')
    # Format the curve list in sets of 3
    blen_curves = np.array(blen_curves_arr).reshape(nlabels, 3)


    perfmon.level_up('Processing POINT data..', True)

    read_sampler, key_sampler = new_sampler(True), new_sampler()

    for fc in blen_curves_arr:
        fc.keyframe_points.add(nframes)

    for i, points, analog in parser.reader.read_frames(copy=False):

        # Determine valid samples
        valid = points[:, 4] >= min_camera_count
        if max_residual > 0.0:
            valid = np.logical_and(points[:, 3] < max_residual, valid)

        end_sample(read_sampler)
        begin_sample(key_sampler)

        index = i - first_frame

        # Insert keyframes by iterating over each valid point and channel (x/y/z)
        #for value, fc in zip(points[valid, :3].flat, blen_curves[valid].flat):
        for value, fc in zip(points[valid, :3].flat, blen_curves[valid].flat):
            kf = fc.keyframe_points[index]
            kf.co = (i, value)
            kf.interpolation = interpolation
            #kf.type = 'KEFRAME' # Default

            # Inserting keyframes is veeerry slooooww:
            #fc.keyframe_points.insert(i, value, options={'FAST'}).interpolation = interpolation

        end_sample(key_sampler)
        begin_sample(read_sampler)

    end_sample(read_sampler)
    perfmon.level_down()

    # Since we inserted our keyframes in 'FAST' mode, we have to update the fcurves now.
    for fc in blen_curves_arr:
        fc.update()

    perfmon.level_down("Import finished.")

    rtot, rmean = analyze_sample(read_sampler, 0, -1)
    ktot, kmean = analyze_sample(key_sampler)
    perfmon.message('File read (tot, mean):  %0.3f \t %f (s)' % (rtot, rmean))
    perfmon.message('Key insert (tot, mean): %0.3f \t %f (s)' % (ktot, kmean))

    bpy.context.view_layer.update()
    return {'FINISHED'}


def create_action(action_name, object=None, fake_user=False):
    # Create new action.

    action = bpy.data.actions.new(action_name)
    action.use_fake_user = fake_user

    # If none yet assigned, assign this action to id_data.
    if object:
        if not object.animation_data:
            object.animation_data_create()
        if not object.animation_data.action:
            object.animation_data.action = action
    return action

def create_armature_object(context, name):
    arm_data = bpy.data.armatures.new(name=name)
    arm_obj = bpy.data.objects.new(name=name, object_data=arm_data)

    # Instance in scene.
    context.view_layer.active_layer_collection.collection.objects.link(arm_obj)

    return arm_obj

def add_empty_armature_bones(context, arm_obj, bone_names, length=0.1):
    '''
    Generate a set of named bones

    Params:
    ----
    context:    bpy.context
    arm_obj:    Armature object
    length:     Length of each bone.
    '''

    assert arm_obj.type == 'ARMATURE', "Object passed to 'add_empty_armature_bones()' must be an armature."

    # Clear any selection
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='DESELECT')
    # Enter edit mode for the armature
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    edit_bones = arm_obj.data.edit_bones

    if not islist(bone_names):
        bone_names = [bone_names]

    for name in bone_names:
        # Create a new bone
        b = edit_bones.new(name)
        b.head = (0.0, 0.0, 0.0)
        b.tail = (0.0, 0.0, length)

    bpy.ops.object.mode_set(mode='OBJECT')

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
