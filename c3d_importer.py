import mathutils, bpy
import os
import numpy as np
from . pyfuncs import *


def load(operator, context, filepath="",
         use_manual_orientation=False,
         axis_forward='-Z',
         axis_up='Y',
         global_scale=1.0,
         create_armature=True,
         bone_size=0.02,
         fake_user=True,
         interpolation='LINEAR',
         min_camera_count = 0,
         max_residual=0.0,
         load_mem_efficient=False,
         print_file=True):

    from bpy_extras.io_utils import axis_conversion
    from .c3d_parse_dictionary import C3DParseDictionary
    from . perfmon import PerfMon

    print(axis_forward, axis_up)
    # Action id
    file_id = os.path.basename(filepath)
    file_name = os.path.splitext(file_id)[0]

    # Monitor performance
    perfmon = PerfMon()
    perfmon.level_up('Importing: %s ...' % file_id, True)

    # Open file and read parameter headers
    parser = C3DParseDictionary(filepath)

    unit_conv_fac = unit_conversion(parser, 'POINT', sys_unit='m')

    # World orientation adjustment
    scale = global_scale*unit_conv_fac
    if use_manual_orientation:
        global_orient = axis_conversion(from_forward=axis_forward, from_up=axis_up)
        global_orient = global_orient @ mathutils.Matrix.Scale(scale, 3)
        # Convert to a numpy array matrix
        global_orient = np.array(global_orient)
    else:
        global_orient = parser.axis_interpretation([0,0,1], [0,1,0])
        global_orient *= scale # Uniform scale axis


    if print_file:
        parser.printFile()

    labels = parser.parseLabels('POINT')
    nlabels = len(labels)

    # Number of frames [first, last] => +1
    # first_frame is the frame index to start parsing from
    # nframes is the number of frames to parse
    first_frame = parser.reader.header.first_frame
    nframes = parser.reader.header.last_frame - first_frame + 1

    # Create an armature adapted to the data (if specified)
    arm_obj = None
    bone_radius = bone_size * 0.5
    if create_armature:
        arm_obj = create_armature_object(context, file_name, 'BBONE')
        add_empty_armature_bones(context, arm_obj, labels, bone_size)
        # Set the width of the bbones
        for bone in arm_obj.data.bones:
            bone.bbone_x = bone_radius
            bone.bbone_z = bone_radius


    # Create an action
    action = create_action(file_name, arm_obj, fake_user)
    # Generate location (x,y,z) F-Curves for each label
    blen_curves_arr = generate_blend_curves(action, labels, 3, 'pose.bones["%s"].location')
    # Format the curve list in sets of 3
    blen_curves = np.array(blen_curves_arr).reshape(nlabels, 3)

    if load_mem_efficient:
        # Primarily a test function.
        read_data_mem_efficient(parser, blen_curves, labels, global_orient, first_frame, nframes,
                                interpolation, min_camera_count, max_residual,
                                perfmon)
    else:
        # Default processing func.
        read_data_processor_efficient(parser, blen_curves, labels, global_orient, first_frame, nframes,
                                      interpolation, min_camera_count, max_residual,
                                      perfmon)

    # Since we inserted our keyframes in 'FAST' mode, we have to update the fcurves now.
    for fc in blen_curves_arr:
        fc.update()

    perfmon.level_down("Import finished.")

    bpy.context.view_layer.update()
    return {'FINISHED'}

def valid_points(point_block, min_camera_count, max_residual):
    ''' Determine valid points in a block.
    '''
    valid = point_block[:, 4] >= min_camera_count
    if max_residual > 0.0:
        valid = np.logical_and(point_block[:, 3] < max_residual, valid)
    return valid

def read_data_processor_efficient(parser, blen_curves, labels, global_orient, first_frame, nframes,
                                  interpolation,
                                  min_camera_count, max_residual,
                                  perfmon):
    '''Read and keyframe POINT data.
    '''
    nlabels = len(labels)

    point_frames = np.zeros([nframes, 3, nlabels], dtype=np.float64)
    valid = np.empty([nframes, nlabels], dtype=np.bool)

    # Start reading POINT blocks (and analog, but signals from force plates etc. are not supported...)
    perfmon.level_up('Reading POINT data..', True)
    for i, points, analog in parser.reader.read_frames(copy=False):
        index = i - first_frame

        # Determine valid samples
        valid[index] = valid_points(points, min_camera_count, max_residual)

        # Extract columns 0:3
        point_frames[index] = points[0:nlabels,0:3].T

    # Re-orient and scale the data
    point_frames = np.matmul(global_orient, point_frames)

    perfmon.level_down('Reading Done.')

    # Time to generate keyframes
    perfmon.level_up('Keyframing POINT data..', True)
    # Number of valid keys for each label
    nkeys = np.sum(valid, axis=0)
    frame_range = np.arange(0, nframes)
    # Iterate each group (tracker label)
    for group_ind, fc_set in enumerate(blen_curves):
        # Create keyframes
        for fc in fc_set:
            fc.keyframe_points.add(nkeys[group_ind])

        # Iterate valid frames and insert keyframes
        indices = frame_range[valid[:, group_ind]]
        for key_ind, (frame, p) in enumerate(zip(indices, point_frames[indices, :, group_ind])):
            for dim, fc in enumerate(fc_set):
                kf = fc.keyframe_points[key_ind]
                kf.co = (frame, p[dim])
                kf.interpolation = interpolation

    perfmon.level_down('Keyframing Done.')

def read_data_mem_efficient(parser, blen_curves, labels,
                            global_orient, first_frame, nframes,
                            interpolation,
                            min_camera_count, max_residual,
                            perfmon):
    '''Read POINT data block by block, inserting keyframes for a .c3d block at a time.

    Note:
    This function reads a .c3d block (frame) at a time, and uses insert(keyframe).
    Inserting is very slow, but this might change in which case this an acceptable
    solution. Now it serves two purposes:
    1. Test and/or example case for how the code could be written.
    2. Provide memory efficient loading, currently it's useless due to the processing time but that might change.
    '''

    perfmon.level_up('Processing POINT data..', True)


    read_sampler, key_sampler = new_sampler(True), new_sampler()

    for i, points, analog in parser.reader.read_frames(copy=False):

        # Determine valid samples
        valid = valid_points(points, min_camera_count, max_residual)

        # Re-orient and scale the data
        opoints = np.matmul(global_orient, points[:, 0:3].T).T

        end_sample(read_sampler)
        begin_sample(key_sampler)

        index = i - first_frame

        # Insert keyframes by iterating over each valid point and channel (x/y/z)
        for value, fc in zip(opoints[valid].flat, blen_curves[valid].flat):
            # Inserting keyframes is veeerry slooooww:
            fc.keyframe_points.insert(i, value, options={'FAST'}).interpolation = interpolation

            # Fast insert that are added first, generates empty keyframes complicated to get rid of,
            # hence the number of keyframes must be known when using this method.
            #kf = fc.keyframe_points[index]
            #kf.co = (i, value)
            #kf.interpolation = interpolation

        end_sample(key_sampler)
        begin_sample(read_sampler)

    end_sample(read_sampler)

    perfmon.level_down()
    rtot, rmean = analyze_sample(read_sampler, 0, -1)
    ktot, kmean = analyze_sample(key_sampler)
    perfmon.message('File read (tot, mean):  %0.3f \t %f (s)' % (rtot, rmean))
    perfmon.message('Key insert (tot, mean): %0.3f \t %f (s)' % (ktot, kmean))

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

def create_armature_object(context, name, display_type='OCTAHEDRAL'):
    arm_data = bpy.data.armatures.new(name=name)
    arm_data.display_type = display_type

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

    # Try to enter object mode, polling active object is unreliable since an object can be in edit mode but not active!
    try:
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    except:
        pass
    # Clear any selection
    bpy.ops.object.select_all(action='DESELECT')
    # Enter edit mode for the armature
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
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
