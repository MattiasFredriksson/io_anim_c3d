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

# Script copyright (C) Mattias Fredriksson

# pep8 compliancy:
#   flake8 .\c3d_importer.py

import mathutils
import bpy
import os
import numpy as np
from .pyfuncs import islist


def load(operator, context, filepath="",
         use_manual_orientation=False,
         axis_forward='-Z',
         axis_up='Y',
         global_scale=1.0,
         create_armature=True,
         bone_size=0.02,
         adapt_frame_rate=True,
         fake_user=True,
         interpolation='LINEAR',
         min_camera_count=0,
         max_residual=0.0,
         include_empty_labels=False,
         apply_label_mask=True,
         load_mem_efficient=False,
         print_file=True):

    from bpy_extras.io_utils import axis_conversion
    from .c3d_parse_dictionary import C3DParseDictionary
    from . perfmon import PerfMon

    # Action id
    file_id = os.path.basename(filepath)
    file_name = os.path.splitext(file_id)[0]

    # Monitor performance
    perfmon = PerfMon()
    perfmon.level_up('Importing: %s ...' % file_id, True)

    # Open file and read parameter headers
    parser = C3DParseDictionary(filepath)
    if print_file:
        parser.printFile()
    if parser.reader.point_used == 0:
        operator.report({'WARNING'}, 'No POINT data in file: %s' % filepath)
        return {'CANCELLED'}

    # Frame rate conversion factor
    conv_fac_frame_rate = 1.0
    if adapt_frame_rate:
        conv_fac_frame_rate = bpy.context.scene.render.fps / parser.frame_rate

    # Conversion factor for length measurements
    blend_units = 'm'
    conv_fac_spatial_unit = parser.unit_conversion('POINT', sys_unit=blend_units)

    # World orientation adjustment
    scale = global_scale * conv_fac_spatial_unit
    if use_manual_orientation:
        global_orient = axis_conversion(from_forward=axis_forward, from_up=axis_up)
        global_orient = global_orient @ mathutils.Matrix.Scale(scale, 3)
        # Convert to a numpy array matrix
        global_orient = np.array(global_orient)
    else:
        global_orient, msg = parser.axis_interpretation([0, 0, 1], [0, 1, 0])
        global_orient *= scale  # Uniform scale axis

        if msg is not None:
            operator.report({'INFO'}, msg)

    # Read labels, remove labels matching criteria as defined
    # in regard to the software used to generate the file.
    labels = parser.getPointChannelLabels()
    if apply_label_mask:
        point_mask = parser.generateLabelMask(labels, 'POINT')
    else:
        point_mask = np.ones(np.shape(labels), np.bool)
    labels = C3DParseDictionary.generateUniqueLabels(labels[point_mask])
    # Equivalent to number of channels used in POINT data
    nlabels = len(labels)
    if nlabels == 0:
        operator.report({'WARNING'}, 'All POINT data was culled in file: %s' % filepath)
        return {'CANCELLED'}

    # Number of frames [first, last] => +1
    # first_frame is the frame index to start parsing from
    # nframes is the number of frames to parse
    first_frame = parser.first_frame
    nframes = parser.last_frame - first_frame + 1
    perfmon.message('Parsing: %i frames...' % nframes)

    # Create an action
    action = create_action(file_name, fake_user=fake_user)
    # Generate location (x,y,z) F-Curves for each label
    blen_curves_arr = generate_blend_curves(action, labels, 3, 'pose.bones["%s"].location')
    # Format the curve list in sets of 3
    blen_curves = np.array(blen_curves_arr).reshape(nlabels, 3)

    if load_mem_efficient:
        # Primarily a test function.
        read_data_mem_efficient(parser, blen_curves, labels, point_mask, global_orient,
                                first_frame, nframes, conv_fac_frame_rate,
                                interpolation, min_camera_count, max_residual,
                                perfmon)
    else:
        # Default processing func.
        read_data_processor_efficient(parser, blen_curves, labels, point_mask, global_orient,
                                      first_frame, nframes, conv_fac_frame_rate,
                                      interpolation, min_camera_count, max_residual,
                                      perfmon)

    # Remove labels with no valid keyframes
    if not include_empty_labels:
        clean_empty_fcurves(action)
    # Since we inserted our keyframes in 'FAST' mode, we have to update the fcurves now.
    for fc in action.fcurves:
        fc.update()

    if action.fcurves == 0:
        remove_action(action)
        # All samples were either invalid or was previously culled in regard to the channel label.
        operator.report({'WARNING'}, 'No valid POINT data in file: %s' % filepath)
        return {'CANCELLED'}

    # Create an armature adapted to the data (if specified)
    arm_obj = None
    bone_radius = bone_size * 0.5
    if create_armature:
        final_labels = [fc_grp.name for fc_grp in action.groups]
        arm_obj = create_armature_object(context, file_name, 'BBONE')
        add_empty_armature_bones(context, arm_obj, final_labels, bone_size)
        # Set the width of the bbones
        for bone in arm_obj.data.bones:
            bone.bbone_x = bone_radius
            bone.bbone_z = bone_radius
        # Set generated action as active
        set_action(arm_obj, action, replace=False)

    perfmon.level_down("Import finished.")

    bpy.context.view_layer.update()
    return {'FINISHED'}


def valid_points(point_block, min_camera_count, max_residual):
    ''' Generate a mask for valid points read for a frame.
    '''
    valid = point_block[:, 4] >= min_camera_count
    if max_residual > 0.0:
        valid = np.logical_and(point_block[:, 3] < max_residual, valid)
    return valid


def read_data_processor_efficient(parser, blen_curves, labels, point_mask, global_orient,
                                  first_frame, nframes, conv_fac_frame_rate,
                                  interpolation, min_camera_count, max_residual,
                                  perfmon):
    '''   Read and keyframe POINT data.
    '''
    nlabels = len(labels)

    # Generate numpy arrays to store read frame data before generating keyframes
    point_frames = np.zeros([nframes, 3, nlabels], dtype=np.float64)
    valid_samples = np.empty([nframes, nlabels], dtype=np.bool)

    ##
    # Start reading POINT blocks (and analog, but signals from force plates etc. are not supported...)
    perfmon.level_up('Reading POINT data..', True)
    for i, points, analog in parser.reader.read_frames(copy=False):
        index = i - first_frame
        # Apply masked samples
        points = points[point_mask]
        # Determine valid samples using columns 3:4
        valid_samples[index] = valid_points(points, min_camera_count, max_residual)

        # Extract position coordinates from columns 0:3
        point_frames[index] = points[:, 0:3].T

    # Re-orient and scale the data
    point_frames = np.matmul(global_orient, point_frames)

    perfmon.level_down('Reading Done.')

    ##
    # Time to generate keyframes
    perfmon.level_up('Keyframing POINT data..', True)
    # Number of valid keys for each label
    nkeys = np.sum(valid_samples, axis=0)
    frame_range = np.arange(0, nframes)
    # Iterate each group (tracker label)
    for group_ind, fc_set in enumerate(blen_curves):
        # Create keyframes
        for fc in fc_set:
            fc.keyframe_points.add(nkeys[group_ind])

        # Iterate valid frames and insert keyframes
        indices = frame_range[valid_samples[:, group_ind]]
        for key_ind, (frame, p) in enumerate(zip(indices, point_frames[indices, :, group_ind])):
            for dim, fc in enumerate(fc_set):
                kf = fc.keyframe_points[key_ind]
                kf.co = (frame * conv_fac_frame_rate, p[dim])
                kf.interpolation = interpolation

    perfmon.level_down('Keyframing Done.')


def read_data_mem_efficient(parser, blen_curves, labels, point_mask, global_orient,
                            first_frame, nframes, conv_fac_frame_rate,
                            interpolation, min_camera_count, max_residual,
                            perfmon):
    '''Read POINT data block by block, inserting keyframes for a .c3d block at a time.

    Note:
    This function reads a .c3d block (frame) at a time, and uses insert(keyframe).
    Inserting is very slow, but this might change in which case this an acceptable
    solution. Now it serves two purposes:
    1. Test and/or example case for how the code could be written.
    2. Provide memory efficient loading, currently it's useless due to the processing time but that might change.
    '''
    from . perfmon import new_sampler, begin_sample, end_sample, analyze_sample

    perfmon.level_up('Processing POINT data..', True)
    read_sampler, key_sampler = new_sampler(True), new_sampler()

    for i, points, analog in parser.reader.read_frames(copy=False):
        points = points[point_mask]
        # Determine valid samples
        valid = valid_points(points, min_camera_count, max_residual)

        # Re-orient and scale the data
        opoints = np.matmul(global_orient, points[:, 0:3].T).T

        end_sample(read_sampler)
        begin_sample(key_sampler)

        # index = i - first_frame
        frame = i * conv_fac_frame_rate

        # Insert keyframes by iterating over each valid point and channel (x/y/z)
        for value, fc in zip(opoints[valid].flat, blen_curves[valid].flat):
            # Inserting keyframes is veeerry slooooww:
            fc.keyframe_points.insert(frame, value, options={'FAST'}).interpolation = interpolation

            # Fast insert that are added first, generates empty keyframes complicated to get rid of,
            # hence the number of keyframes must be known when using this method.
            # kf = fc.keyframe_points[index]
            # kf.co = (i, value)
            # kf.interpolation = interpolation

        end_sample(key_sampler)
        begin_sample(read_sampler)

    end_sample(read_sampler)

    perfmon.level_down()
    rtot, rmean = analyze_sample(read_sampler, 0, -1)
    ktot, kmean = analyze_sample(key_sampler)
    perfmon.message('File read (tot, mean):  %0.3f \t %f (s)' % (rtot, rmean))
    perfmon.message('Key insert (tot, mean): %0.3f \t %f (s)' % (ktot, kmean))


def create_action(action_name, object=None, fake_user=False):
    ''' Create new action.

    Params:
    -----
    action_name:    Name for the action
    object:         Set the action as the active animation data for the object.
    fake_user:      Set the 'Fake User' flag for the action.
    '''

    action = bpy.data.actions.new(action_name)
    action.use_fake_user = fake_user

    # If none yet assigned, assign this action to id_data.
    if object:
        set_action(object, action, replace=False)
    return action


def remove_action(action):
    ''' Delete a specific action.
    '''
    bpy.data.actions.remove(action)


def set_action(object, action, replace=True):
    ''' Set the action associated with the object.
    -----
    object:    Object for which the animation should be set.
    action:    Action to set for the object.
    replace:   If False, existing action set for the object will not be replaced.
    '''
    if not object.animation_data:
        object.animation_data_create()
    if replace or not object.animation_data.action:
        object.animation_data.action = action


def create_armature_object(context, name, display_type='OCTAHEDRAL'):
    ''' Create an 'ARMATURE' object and add to active layer

    Params:
    -----
    context:        Blender Context
    name:           Name for the object
    display_type:   Display type for the armature bones.
    '''
    arm_data = bpy.data.armatures.new(name=name)
    arm_data.display_type = display_type

    arm_obj = bpy.data.objects.new(name=name, object_data=arm_data)

    # Instance in scene.
    context.view_layer.active_layer_collection.collection.objects.link(arm_obj)
    return arm_obj


def enter_clean_object_mode():
    ''' Enter object mode and clear any selection.
    '''
    # Try to enter object mode, polling active object is unreliable since an object can be in edit mode but not active!
    try:
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    except RuntimeError:
        pass
    # Clear any selection
    bpy.ops.object.select_all(action='DESELECT')


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

    # Enter object mode
    enter_clean_object_mode()
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

    # Convert a single label to an iterable tuple (list)
    if not islist(labels):
        labels = (labels)

    # Generate channels for each label to hold location information
    if '%s' not in fc_data_path_str:
        # No format operator found in the data_path_str used to define F-curves.
        blen_curves = [action.fcurves.new(fc_data_path_str, index=i, action_group=label)
                       for label in labels for i in range(grp_channel_count)]
    else:
        # Format operator found, replace it with label associated with the created F-Curve
        blen_curves = [action.fcurves.new(fc_data_path_str % label, index=i, action_group=label)
                       for label in labels for i in range(grp_channel_count)]
    return blen_curves


def clean_empty_fcurves(action):
    '''
    Remove any F-Curve in the action with no keyframes.

    Parameters
    ----
    action:             bpy.types.Action object to clean F-curves.

    '''
    empty_curves = []
    for curve in action.fcurves:
        if len(curve.keyframe_points) == 0:
            empty_curves.append(curve)

    for curve in empty_curves:
        action.fcurves.remove(curve)
