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
#   flake8 .\c3d_parse_dictionary.py

import sys
import numpy as np
from .c3d.c3d import Reader

###############
# Standalone module to interface with the parser for the .c3d format
###############


def filter_names(group):
    ''' Iteration filter for dictionary keys, filtering all string keys
    '''
    for key, value in group.items():
        if isinstance(key, str):
            yield key


def islist(N):
    ''' Check if 'N' object is any type of array
    '''
    return hasattr(N, '__len__') and (not isinstance(N, str))


def dim(X):
    ''' Get the number of dimensions of the python array X
    '''
    if not isinstance(X, np.ndarray) and isinstance(X[0], np.ndarray):
        return len(X[0].shape) + 1
    return len(np.shape(X))


def isvector(param):
    ''' Check if the parameter is composed of single dimensional data.

    Params:
    ------
    param:	c3d.Param object
    '''
    return len(param.dimensions) < 2


def issingle(param):
    ''' Check if the parameter is composed of single element.

    Params:
    ------
    param:	c3d.Param object
    '''
    return len(param.dimensions) == 0


def parseC3DArray(param, dtype=np.int8):
    ''' Parse C3D parameter data array, returns either a single or
        multiple dimensional array depending on the parameter data shape.
    ------
    param:	c3d.Param object
    '''
    return param._as_any(dtype)


def parseC3DString(param):
    ''' Parse data as an array of, or single string.

    Params:
    ------
    param:	 c3d.Param object
    Returns: String or array (np.ndarray) of strings
    '''
    strarr = param.string_array
    if len(np.shape(strarr)) == 1 and len(strarr) == 1:
        return strarr[0].strip()
    # Strip
    for i, v in np.ndenumerate(strarr):
        strarr[i] = v.strip()
    return strarr


class C3DParseDictionary:
    ''' C3D parser dictionary, facilitates association between parameter identifiers and parsing functions.
    '''
    def __init__(self, file_path, parse_dict='basic'):
        ''' Construct a parser for a .c3d file
        '''
        self.file_path = file_path
        # Set parse dictionary
        if parse_dict == 'basic':
            self.parse_dict = C3DParseDictionary.define_basic_dictionary()
        elif isinstance(parse_dict, dict):
            self.parse_dict = parse_dict
        else:
            self.parse_dict = []

    def __del__(self):
        # Destructor
        self.close()

    def __enter__(self):
        # Open file handle and create a .c3d reader
        self.file_handle = open(self.file_path, 'rb')
        self.reader = Reader(self.file_handle)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def close(self):
        ''' Close an open .c3d file
        '''
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.close()

    def get_group(self, group_id):
        ''' Get a group from a group name id
        '''
        return self.reader.get(group_id, None)

    def get_param(self, group_id, param_id):
        ''' Fetch a parameter struct from group and param id:s
        '''
        group = self.get_group(group_id) 	# Fetch group
        if group is None:					# Verify fetch
            return None                     # Return None if group does not exist
        return group.get(param_id, None)    # Fetch param or return None if not found

    def get_paramNames(self, group_id):
        ''' Get an iterable over parameter group names.
        '''
        group = self.get_group(group_id) 		 # Fetch group
        if group is None:						 # Verify fetch
            return None
        return list(filter_names(group.params))  # Fetch param or return None if not found

    """
    --------------------------------------------------------
                        Parameter parsing functions
    --------------------------------------------------------
    """

    def try_parse_param(self, group_id, param_id):
        ''' Try parse a specified parameter, if parsing is not specified through the
            parse dictionary it will attempt to guess the appropriate format.
        '''
        value = self.parse_known_param(group_id, param_id)
        if value is None:					# Verify fetch
            return self.parse_param_any(group_id, param_id)
        return value

    def parse_known_param(self, group_id, param_id):
        ''' Parse attributes defined in the parsing dictionary
        '''
        func = self.parse_dict.get(param_id, None)
        if func is None:
            return None
        return func(self, group_id, param_id)

    def parse_param_any(self, group_id, param_id):
        '''
        Parse param as either a 32 bit floating point value or an integer unsigned integer representation
        (including string representations).

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    Value(s) of interpreted type either as a single element of the type or array.
        '''
        param = self.get_param(group_id, param_id)
        if param is None:
            return None
        if param.bytes_per_element == 4:
            return self.parse_param_float(group_id, param_id)
        else:
            return self.parse_param_uint(group_id, param_id)

    def parse_param_string(self, group_id, param_id):
        ''' Get a string or list of strings from the specified parameter.

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    String or array of strings.
        '''
        param = self.get_param(group_id, param_id)
        if param is None:
            return None
        return parseC3DString(param)

    def parse_param_float(self, group_id, param_id):
        ''' Get a ndarray of integers from a group parameter.

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    Float value or an array of float values.
        '''
        param = self.get_param(group_id, param_id)
        if(param is None):
            return None
        if(param.bytes_per_element == 4):
            return parseC3DArray(param, dtype=np.float32)
        elif(param.bytes_per_element == 8):
            return parseC3DArray(param, dtype=np.float64)
        else:
            return None

    def parse_param_int(self, group_id, param_id):
        ''' Get a ndarray of integers from a group parameter.

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    Integer value or an array of int values.
        '''
        param = self.get_param(group_id, param_id)
        if(param is None):
            return None
        if(param.bytes_per_element == -1):  # String data
            return self.parse_param_string(group_id, param_id)
        elif(param.bytes_per_element == 1):
            return parseC3DArray(param, dtype=np.int8)
        elif(param.bytes_per_element == 2):
            return parseC3DArray(param, dtype=np.int16)
        elif(param.bytes_per_element == 4):
            return parseC3DArray(param, dtype=np.int32)
        elif(param.bytes_per_element == 8):
            return parseC3DArray(param, dtype=np.int64)
        else:
            return None

    def parse_param_uint(self, group_id, param_id):
        ''' Get a ndarray of integers from a group parameter.

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    Unsigned integer value or an array of uint values.
        '''
        param = self.get_param(group_id, param_id)
        if(param is None):
            return None
        if(param.bytes_per_element == -1):  # Byte representation indicate string data
            return self.parse_param_string(group_id, param_id)
        elif(param.bytes_per_element == 1):
            return parseC3DArray(param, dtype=np.uint8)
        elif(param.bytes_per_element == 2):
            return parseC3DArray(param, dtype=np.uint16)
        elif(param.bytes_per_element == 4):
            return parseC3DArray(param, dtype=np.uint32)
        elif(param.bytes_per_element == 8):
            return parseC3DArray(param, dtype=np.uint64)
        else:
            return None

    def parse_param_any_integer(self, group_id, param_id):
        ''' Evaluate any reasonable conversion of the parameter to a 32 bit unsigned integer representation.

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    Integer or float value (representing an integer).
        '''
        param = self.get_param(group_id, param_id)
        if(param is None):
            return None
        return param._as_integer_value

    def parse_param_uint_32(self, group_id, param_id):
        ''' Get a single 32 bit unsigned integers from a parameter group.

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    First 32 bits interpreted as an unsigned integer value.
        '''
        param = self.get_param(group_id, param_id)
        if(param is None):
            return None
        return param.uint32_value

    def parse_param_float_32(self, group_id, param_id):
        ''' Get a single 32 bit floating point from a parameter group.

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    First 32 bits interpreted as an floating point value.
        '''
        param = self.get_param(group_id, param_id)
        if(param is None):
            return None
        return param.float_value

    """
    --------------------------------------------------------
                           Properties
    --------------------------------------------------------
    """

    @property
    def first_frame(self):
        ''' Get index of the first recorded frame. '''
        return self.reader.first_frame

    @property
    def last_frame(self):
        ''' Get index of the last recorded frame. '''
        return self.reader.last_frame

    @property
    def frame_rate(self):
        ''' Get the frame rate for the data sequence. '''
        return max(1.0, self.reader.header.frame_rate)

    """
    --------------------------------------------------------
                        Interpret .c3d Data
    --------------------------------------------------------
    """

    def header_events(self):
        ''' Get an iterable over header events. Each item is on the form (frame_timing, label) and type (float, string).
        '''
        header = self.reader.header
        # Convert event timing to a frame index (in floating point)
        timings = header.event_timings[header.event_disp_flags] * self.reader.point_rate - self.reader.first_frame
        return zip(timings, header.event_labels[header.event_disp_flags])

    def events(self):
        ''' Get an iterable over EVENTS defined in the file.
        '''
        if self.get_param('EVENT', 'LABELS') is None:
            return self.header_events()
        else:
            ecount = int(self.parse_param_any('EVENT', 'USED'))
            labels = self.parse_labels('EVENT', 'LABELS')
            context = self.parse_labels('EVENT', 'CONTEXTS')
            timings = self.parse_multi_parameter('EVENT', 'TIMES', C3DParseDictionary.parse_param_float)

            tshape = np.shape(timings)
            if ecount > len(labels):
                raise ValueError('C3D events could not be parsed. Expected %i labels found %i.' % (ecount, len(labels)))
            elif ecount > tshape[0]:
                raise ValueError('C3D events could not be parsed. Expected %i timings found %i.' % (ecount, tshape[0]))

            # Parse timing parameter, the parameter can contain two columns tracking
            # minutes and seconds separately. If only one column is present it's assumed
            # to be recorded in seconds.
            if len(tshape) == 2 and tshape[1] == 2:
                frame_timings = timings[:, 0] * 60.0 * self.reader.point_rate
                frame_timings += timings[:, 1] * self.reader.point_rate - self.reader.first_frame
            elif len(tshape) == 1:
                frame_timings = timings * self.reader.point_rate - self.reader.first_frame
            else:
                raise ValueError(
                    'C3D events could not be parsed. Shape %s for the EVENT.TIMES parameter is not supported.' %
                    str(np.shape(timings)))

            # Combine label array with label context and return
            if context is not None:
                labels = labels + '_' + context
            return zip(frame_timings, labels)

    def axis_interpretation(self, sys_axis_up=[0, 0, 1], sys_axis_forw=[0, 1, 0]):
        ''' Interpret X_SCREEN and Y_SCREEN parameters as the axis orientation for the system.

        Params:
        ----
        sys_axis_up:   Up axis vector defining convention used for the system (normal to the horizontal ground plane).
        sys_axis_forw: Forward axis vector defining the full system convention (forward orientation on ground plane).
        Returns:       (3x3 orientation matrix for converting 3D data points, True if POINT.?_SCREEN param was parsed).
        '''
        # Axis conversion dictionary
        AXIS_DICT = {
            'X': [1.0, 0, 0],
            '+X': [1.0, 0, 0],
            '-X': [-1.0, 0, 0],
            'Y': [0, 1.0, 0],
            '+Y': [0, 1.0, 0],
            '-Y': [0, -1.0, 0],
            'Z': [0, 0, 1.0],
            '+Z': [0, 0, 1.0],
            '-Z': [0, 0, -1.0],
        }
        O_data = np.identity(3)
        parsed_screen_param = True

        axis_x = self.parse_param_string('POINT', 'X_SCREEN')
        axis_y = self.parse_param_string('POINT', 'Y_SCREEN')
        # If both X/Y_SCREEN axis can't be parsed, default case:
        if axis_x not in AXIS_DICT or axis_y not in AXIS_DICT:
            axis_x = 'X'
            axis_y = 'Z'
            parsed_screen_param = False

        # Interpret if both X/Y_SCREEN
        axis_x = AXIS_DICT[axis_x]
        axis_y = AXIS_DICT[axis_y]
        O_data[:, 0] = axis_x
        O_data[:, 1] = axis_y
        O_data[:, 2] = np.cross(axis_x, axis_y)

        # Define the system third axis as the cross product:
        O_sys = np.empty((3, 3))
        O_sys[:, 1] = sys_axis_forw / np.linalg.norm(sys_axis_forw)
        O_sys[:, 2] = sys_axis_up / np.linalg.norm(sys_axis_up)
        O_sys[:, 0] = np.cross(O_sys[:, 1], O_sys[:, 2])
        # Orient from data basis -> system basis
        return np.matmul(O_sys, O_data.T), parsed_screen_param

    def unit_conversion(self, group_id, param_id='UNITS', sys_unit=None):
        ''' Interpret unit conversion available for a parameter.

        Params:
        ----
        group_id:   Parameter group ID (e.g. 'POINTS').
        param_id:   ID for the parameter itself, default is set to 'UNITS' as it's the standard parameter for recording
                    measurement units used.
        sys_unit:   The unit used within the system to which the units should be converted to. Leave as None if it
                    should be converted to default SI unit.

        Warning! Currently only supports units of length.
        '''
        # Unit conversion dictionary
        unit_dict = {
            # Metric
            'm': 1.0,
            'meter': 1.0,
            'cm': 1e-2,
            'centimeter': 1e-2,
            'mm': 1e-3,
            'millimeter': 1e-3,
            # Imperial
            'in': 254e-4,
            'inch': 254e-4,
            'ft': 0.3048,
            'foot': 0.3048,
            'yd': 0.9144,
            'yard': 0.9144,
            # Default
            None: 1.0
        }
        # Conversion factor (scale)
        conv_fac = 1.0
        # Convert data from unit defined in 'GROUP.UNITS'
        data_unit = self.parse_param_string(group_id, param_id)
        if data_unit is not None:
            if islist(data_unit):
                # Convert a list of units
                conv_fac = np.ones(len(data_unit))
                for i, u in enumerate(data_unit):
                    u = u.lower()
                    if u in unit_dict:
                        conv_fac = unit_dict[u]
            else:
                # Convert a single unit string
                data_unit = data_unit.lower()
                if data_unit in unit_dict:
                    conv_fac = unit_dict[data_unit]
        else:
            print("No unit of length found for %s data." % group_id)

        # Convert data to a specific unit (does not support conversion of different SI units)
        if type(sys_unit) is str:
            conv2unit = unit_dict[sys_unit.lower()]
            conv_fac = conv_fac / conv2unit

        # Return the conversion factor
        return conv_fac

    def parse_multi_parameter(self, group_id, param_ids, pfunction='C3DParseDictionary.parse_param_any'):
        ''' Get concatenated list of values for a group parameter stored in multiple entries.

        Parameters with multiple entries are parameters such as label entries which can't be stored in a single
        parameter. Instead the parameter is stored as: POINT.LABELS, POINT.LABELS2, ..., POINT.LABELSN.

        Params:
        ----
        group_id:   Group from which the labels should be parsed.
        param_ids:  List of parameter identifiers for which label information is stored, e.g. ['LABELS'].
        pfunction:  Function used to parse the group parameter, default is parse_param_any(...).
        Returns:    Numpy array containing parsed values.
        '''
        if not islist(param_ids):
            param_ids = [param_ids]

        def parseParam(pid):
            pitems = pfunction(self, group_id, pid)
            if islist(pitems):
                return pitems
            elif pitems is not None:
                return [pitems]
            return None

        items = []
        for pid in param_ids:
            # Base case, first label parameter.
            pitems = parseParam(pid)
            # Repeat checking for extended label parameters until none is found.
            i = 2
            while pitems is not None:
                # If any values were parsed, append.
                items.append(pitems)
                pitems = parseParam("%s%i" % (pid, i))
                i += 1

        if len(items) > 0:
            return np.concatenate(items)
        else:
            return np.array([])

    def parse_labels(self, group_id, param_ids=['LABELS']):
        ''' Get a list of labels from a group.

        Params:
        ----
        group_id:   Group from which the labels should be parsed.
        param_ids:  List of parameter identifiers for which label information is stored, default is: ['LABELS'].
                    Note that all label parameters will be checked for extended formats such as
        Returns:    Numpy array of label strings.
        '''
        return self.parse_multi_parameter(group_id, param_ids, C3DParseDictionary.parse_param_string)

    def point_labels(self, empty_label_prefix='EMPTY', missing_label_prefix='UNKNOWN'):
        ''' Determine a set of unique labels for POINT data.
        '''
        labels = self.parse_labels('POINT')

        used_label_count = self.reader.point_used
        if used_label_count == 0:
            return []

        if len(labels) >= used_label_count:
            # Return only labels associated with POINT data.
            return labels[:used_label_count]
        else:
            # Generate labels if the number of parsed count is less then POINT samples.
            unknown = ['%s_%00i' % (missing_label_prefix, i) for i in range(used_label_count - len(labels))]
            return np.concatenate((labels, unknown))

    @staticmethod
    def make_labels_unique(labels, empty_label_prefix='EMPTY'):
        ''' Convert a list of string labels to an unique set of label strings on form 'LABEL_XX'.

        Params:
        ----
        labels:               List of label strings.
        empty_label_prefix:   Empty label strings will be replaced with the prefix.
        Returns:              Numpy list of label strings.
        '''

        # Count duplicate labels
        unique_labels, indices, count = np.unique(labels, return_inverse=True, return_counts=True)
        out_list = [None] * len(labels)
        counter = np.zeros(len(indices), np.int32)
        for i in range(len(indices)):
            index = indices[i]
            label = labels[i] if labels[i] != '' else empty_label_prefix
            # If duplicate labels exist
            if count[index] > 1:
                counter[index] += 1
                # Generate unique label for repeated labels (if empty use prefix)
                label = '%s_%02i' % (label, counter[index])
            out_list[i] = label
        return np.array(out_list)

    def generate_label_mask(self, labels, group='POINT'):
        ''' Generate a mask for specified labels in accordance with common/software specific rules.

            Parameters:
            -----
            labels: Labels for which the mask should be generated.
            group:  Group labels are associated with, should be 'POINT' or 'ANALOG'.
            Return: Mask defined using a numpy bool array of equal shape to label argument.
        '''
        soft_dict = self.software_dictionary()
        if soft_dict is not None:
            return self.generate_software_label_mask(soft_dict, labels, group)
        return np.ones(np.shape(labels), dtype=np.bool)

    def generate_software_label_mask(self, soft_dict, labels, group='POINT'):
        ''' Generate a label mask in regard to the software used to generate the file.
            Parameters are defined by software_dictionary().

            Parameters:
            -----
            soft_dict:   Python dict as fetched using software_dictionary().
            labels:     Labels for which the mask should be generated.
            group:      Group labels are associated with, should be 'POINT' or 'ANALOG'.
            Return:     Mask defined using a numpy bool array of equal shape to label argument.
        '''
        mask = np.ones(np.shape(labels), dtype=np.bool)
        equal, contain, param = soft_dict['%s_EXCLUDE' % group]

        def contains_seq(item, words):
            ''' Checks if any word in words matches a sequence in the item. '''
            for word in words:
                if word in item:
                    return True
            return False

        # Remove labels equivalent to parameter defined words and words defined in the dict.
        equal = np.concatenate((equal, self.parse_labels(group, param)))
        if len(equal) > 0:
            for i, l in enumerate(labels):
                if l in equal:
                    mask[i] = False
        # Remove labels with matching sub-sequences
        if len(contain) > 0:
            for i, l in enumerate(labels):
                if contains_seq(l, contain):
                    mask[i] = False

        return mask

    def software_dictionary(self):
        ''' Fetch software specific dictionaries defining parameters used to
            manage specific software implementations.
        '''
        #   Comment MF:
        #   Concept of a software specific dictionary may not be an optimal solution.
        #   The approach do however provide modularity when there is a necessity to
        #   vary the approach used when parsing files generated from specific exporters.
        #
        software = self.parse_param_string('MANUFACTURER', 'SOFTWARE')

        if software is not None:
            if 'vicon' in software.lower():
                return C3DParseDictionary.vicon_dictionary()
        # No specific software matched
        return None

    @staticmethod
    def vicon_dictionary():
        return {
            'POINT_EXCLUDE': [[], [], ['ANGLES', 'FORCES', 'POWERS', 'MOMENTS']]  # Equal, contain, parameter
        }

    """
    --------------------------------------------------------
                        Parse Dictionaries
    --------------------------------------------------------
    """

    def define_parse_function(self, param_id, function):
        ''' Append a parsing method to the dictionary
        '''
        self.parse_dict[param_id] = function

    @staticmethod
    def define_basic_dictionary():
        ''' Basic dictionary
        '''
        return {
            'USED': C3DParseDictionary.parse_param_int,
            'FRAMES': C3DParseDictionary.parse_param_any_integer,  # Try to convert to integer in any way
            'DATA_START': C3DParseDictionary.parse_param_int,
            'SCALE': C3DParseDictionary.parse_param_float,
            'RATE': C3DParseDictionary.parse_param_float,
            # 'MOVIE_DELAY':C3DParseDictionary.parse_param_int,
            'MOVIE_ID': C3DParseDictionary.parse_param_string,
            'X_SCREEN': C3DParseDictionary.parse_param_string,
            'Y_SCREEN': C3DParseDictionary.parse_param_string,
            'UNITS': C3DParseDictionary.parse_param_string,
            'LABELS': C3DParseDictionary.parse_param_string,
            'DESCRIPTIONS': C3DParseDictionary.parse_param_string,
            # Test cases stored START/END fields as as uint32 but in 2 16 bit words..
            'ACTUAL_START_FIELD': C3DParseDictionary.parse_param_uint_32,
            'ACTUAL_END_FIELD': C3DParseDictionary.parse_param_uint_32,
            # or the same parameter as both a 32 bit floating point and 32 bit unsigned integer (in different files)!
            'LONG_FRAMES': C3DParseDictionary.parse_param_any_integer,
        }

    """
    --------------------------------------------------------
                        Print functions
    --------------------------------------------------------
    """

    def print_header_info(self):
        ''' Print header info (partial) for the loaded file
        '''
        print("Frames (start,end):\t", self.reader.header.first_frame, self.reader.header.last_frame)
        print("POINT Channels:\t\t", self.reader.header.point_count)
        print("ANALOG Channels:\t", self.reader.header.analog_count)
        print("Frame rate:\t\t", self.reader.header.frame_rate)
        print("Analog rate:\t\t", self.reader.header.frame_rate * self.reader.header.analog_per_frame)
        print("Data Scalar:\t\t", self.reader.header.scale_factor, "  [negative if float representation is used]")
        print("Data format:\t\t", self.reader.proc_type)

    def print_param_header(self, group_id, param_id):
        ''' Print parameter header information. Prints name, dimension, and byte
            information for the parameter struct.
        '''
        param = self.get_param(group_id, param_id)
        print("Parameter Name: ", param.name)
        print("Dimensions: ", dim(param))
        print("Bytes per elem: ", param.bytes_per_element)  # , " |-1 indicates string data|")
        print("Total Bytes: ", sys.getsizeof(param.bytes))

    def print_data(self, group_id, param_id):
        ''' Print the binary data struct for the specified parameter
        '''
        param = self.get_param(group_id, param_id)
        if(param is None):
            raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
        print(param.bytes)

    def print_parameters(self, group_id):
        ''' Try parse all parameters in a group and print the result.
        '''
        group = self.get_group(group_id)
        if group is None:					# Verify fetch
            return
        for pid in group.params:
            print('\'' + pid + '\': ', self.try_parse_param(group_id, pid))

    def print_file(self):
        ''' Combination of print_header_info() and print_parameters() over all groups
        '''
        print(''), print(''), print("------------------------------")
        print("Header:")
        print("------------------------------"), print('')
        # Header
        self.print_header_info()
        print(''), print(''), print("------------------------------")
        print("Paramaters:")
        print("------------------------------")
        # All group parameters
        for group in filter_names(self.reader.groups):
            print('')
            print('')
            print("'" + group + "':")
            print("------------------------------")
            self.print_parameters(group)
        print("------------------------------")
# end
