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
    if 0 in param.dimensions[:]: 	# Check if any dimension is 0 (empty buffer)
        return [] 					# Buffer is empty
    # parseCount = int(nbytes(param) / param.bytes_per_element)
    if issingle(param):			# Check if single data item (not array)
        return param._as(dtype)
    if dtype == np.float32:
        data = param.float_array()
    else:
        data = param._as_array(dtype)
    if isvector(param):				# Check if data is contained in a single dimension
        return data.flatten()
    return data


def parseC3DString(param, dtype=np.int8):
    ''' Parse data as an array of, or single string.

    Params:
    ------
    param:	 c3d.Param object
    Returns: String or array (np.ndarray) of strings
    '''
    data = parseC3DArray(param, dtype)
    if isvector(param):  # Attribute is a single string vector
        return data.tostring().decode("ascii").strip()
    else:  # Attribute is composed of an array of strings (or ndim?)
        list = []
        for word in data:
            list.append(word.tostring().decode("ascii").strip())
        return np.array(list)


class C3DParseDictionary:
    ''' C3D parser dictionary, facilitates association between parameter identifiers and parsing functions.
    '''
    def __init__(self, filePath=None, parse_dict='basic'):

        # Set parse dictionary
        if parse_dict == 'basic':
            self.parse_dict = C3DParseDictionary.defineBasicDictionary()
        elif isinstance(parse_dict, dict):
            self.parse_dict = parse_dict
        else:
            self.parse_dict = []
        # Set c3d reader
        if filePath is None:
            self.reader = None
        else:
            self.readFile(filePath)

    def __del__(self):
        self.close()

    def readFile(self, file_path):
        # Open file handle
        self.file_handle = open(file_path, 'rb')
        # Generate
        from .c3d.c3d import Reader
        self.reader = Reader(self.file_handle)
        # Localize some params:
        self.groups = list(filter_names(self.reader.groups))

    def close(self):
        self.file_handle.close()

    def getGroup(self, group_id):
        ''' Get a group from a group name id
        '''
        return self.reader.get(group_id, None)

    def getParam(self, group_id, param_id):
        ''' Fetch a parameter struct from group and param id:s
        '''
        group = self.getGroup(group_id) 	# Fetch group
        if group is None:					# Verify fetch
            return None
        return group.get(param_id, None)    # Fetch param or return None if not found

    def getParamNames(self, group_id):
        group = self.getGroup(group_id) 		 # Fetch group
        if group is None:						 # Verify fetch
            return None
        return list(filter_names(group.params))  # Fetch param or return None if not found

    """
    --------------------------------------------------------
                        Byte Parsing functions
    --------------------------------------------------------
    """

    def tryParseParam(self, group_id, param_id):
        ''' Try parse a specified parameter, if parsing is not specified through the
            parse dictionary it will attempt to guess the appropriate format.
        '''
        value = self.parseKnownParam(group_id, param_id)
        if value is None:					# Verify fetch
            return self.parseParamAny(group_id, param_id)
        return value

    def parseKnownParam(self, group_id, param_id):
        ''' Parse attributes defined in the parsing dictionary
        '''
        func = self.parse_dict.get(param_id, None)
        if func is None:
            return None
        return func(self, group_id, param_id)

    def parseParamAny(self, group_id, param_id):
        '''
        Parse param as either a 32 bit floating point value or an integer unsigned integer representation
        (including string representations).

        Params:
        ----
        group_id:   Parameter group id.
        Param_id:   Parameter id.
        Returns:    Value(s) of interpreted type either as a single element of the type or array.
        '''
        param = self.getParam(group_id, param_id)
        if param is None:
            return None
        if param.bytes_per_element == 4:
            return self.parseParamFloat(group_id, param_id)
        else:
            return self.parseParamUInt(group_id, param_id)

    def parseParamString(self, group_id, param_id):
        ''' Get a string or list of strings from the specified parameter.
        '''
        param = self.getParam(group_id, param_id)
        if param is None:
            return None
        return parseC3DString(param)

    def parseParamFloat(self, group_id, param_id):
        ''' Get a ndarray of integers from a group parameter.
        '''
        param = self.getParam(group_id, param_id)
        if(param is None):
            return None
        if(param.bytes_per_element == 4):
            return parseC3DArray(param, dtype=np.float32)
        elif(param.bytes_per_element == 8):
            return parseC3DArray(param, dtype=np.float64)
        else:
            return None

    def parseParamInt(self, group_id, param_id):
        ''' Get a ndarray of integers from a group parameter.
        '''
        param = self.getParam(group_id, param_id)
        if(param is None):
            return None
        if(param.bytes_per_element == -1):  # String data
            return self.parseParamString(group_id, param_id)
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

    def parseParamUInt(self, group_id, param_id):
        ''' Get a ndarray of integers from a group parameter.
        '''
        param = self.getParam(group_id, param_id)
        if(param is None):
            return None
        if(param.bytes_per_element == -1):  # String data
            return self.parseParamString(group_id, param_id)
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

    def parseParamAnyInteger(self, group_id, param_id):
        ''' Evaluate any possible conversion of the parameter to a 32 bit unsigned integer representation.
        '''
        param = self.getParam(group_id, param_id)
        if(param is None):
            return None
        return param._as_integer_value

    def parseParamUInt_32(self, group_id, param_id):
        ''' Get a single 32 bit unsigned integers from a group parameter.
        '''
        param = self.getParam(group_id, param_id)
        if(param is None):
            return None
        return param.uint32_value

    def parseParamFloat_32(self, group_id, param_id):
        ''' Get a single 32 bit floating point from a group parameter.
        '''
        param = self.getParam(group_id, param_id)
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
        return self.reader.first_frame()
    @property
    def last_frame(self):
        return self.reader.last_frame()
    @property
    def frame_rate(self):
        return max(1.0, self.reader.header.frame_rate)

    """
    --------------------------------------------------------
                        Interpret .c3d Data
    --------------------------------------------------------
    """

    def axis_interpretation(self, sys_axis_up=[0, 0, 1], sys_axis_forw=[0, 1, 0]):
        ''' Interpret X_SCREEN and Y_SCREEN parameters as the axis orientation for the system.

        Params:
        ----
        sys_axis_up:   Up axis vector defining convention used for the system (normal to the horizontal ground plane).
        sys_axis_forw: Forward axis vector defining the full system convention (forward orientation on ground plane).
        Returns:       3x3 orientation matrix for converting 3D data points.
        '''
        # Axis conversion dictionary
        axis_dict = {
            'X':  [1.0, 0, 0],
            '+X': [1.0, 0, 0],
            '-X': [-1.0, 0, 0],
            'Y':  [0, 1.0, 0],
            '+Y': [0, 1.0, 0],
            '-Y': [0, -1.0, 0],
            'Z':  [0, 0, 1.0],
            '+Z': [0, 0, 1.0],
            '-Z': [0, 0, -1.0],
            }
        O_data = np.identity(3)

        axis_x = self.parseParamString('POINT', 'X_SCREEN')
        axis_y = self.parseParamString('POINT', 'Y_SCREEN')
        # Convert
        if axis_x in axis_dict and axis_y in axis_dict:
            axis_x = axis_dict[axis_x]
            axis_y = axis_dict[axis_y]
            O_data[:, 0] = axis_x
            O_data[:, 1] = axis_y
            O_data[:, 2] = np.cross(axis_x, axis_y)
        else:
            print('Unable to parse X/Y_SCREEN information for POINT data')

        # Define the system third axis as the cross product:
        O_sys = np.empty((3, 3))
        O_sys[:, 1] = sys_axis_forw / np.linalg.norm(sys_axis_forw)
        O_sys[:, 2] = sys_axis_up / np.linalg.norm(sys_axis_up)
        O_sys[:, 0] = np.cross(O_sys[:, 1], O_sys[:, 2])
        # Orient from data basis -> system basis
        return np.matmul(O_sys, O_data.T)
    # end axis_interpretation()

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
            'm':            1.0,
            'meter':        1.0,
            'cm':           1e-2,
            'centimeter':   1e-3,
            'mm':           1e-3,
            'millimeter':   1e-3,
            # Imperial
            'in':           254e-4,
            'inch':         254e-4,
            'ft':           0.3048,
            'foot':         0.3048,
            'yd':           0.9144,
            'yard':         0.9144,
            # Default
            None:           1.0
            }
        # Conversion factor (scale)
        conv_fac = 1.0
        # Convert data from unit defined in 'GROUP.UNITS'
        data_unit = self.parseParamString(group_id, param_id).lower()
        if data_unit is not None:
            if islist(data_unit):
                # Convert a list of units
                conv_fac = np.ones(len(data_unit))
                for i, u in enumerate(data_unit):
                    if u in unit_dict:
                        conv_fac = unit_dict[u]
            else:
                # Convert a single unit string
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

    def parseLabels(self, group_id, param_ids=['LABELS', 'LABELS2']):
        ''' Get a list of labels from a group.

        Params:
        ----
        group_id:   Group from which the labels should be parsed.
        param_ids:  List of parameter identifiers for which label information is stored.
        Returns:    Python list of label strings.
        '''
        if not islist(param_ids):
            param_ids = [param_ids]

        labels = []
        for pid in param_ids:
            plabels = self.parseParamString(group_id, pid)
            if islist(plabels):
                labels.append(plabels)
            elif plabels is not None:  # is string
                labels.append([plabels])
        return np.concatenate(labels)

    """
    --------------------------------------------------------
                        Parse Dictionaries
    --------------------------------------------------------
    """

    def defineParseFunction(self, param_id, function):
        ''' Append a parsing method to the dictionary
        '''
        self.parse_dict[param_id] = function

    def defineBasicDictionary():
        ''' Basic dictionary
        '''
        return {
            'USED':         C3DParseDictionary.parseParamInt,
            'FRAMES':       C3DParseDictionary.parseParamAnyInteger,  # Try to convert to integer in any way
            'DATA_START':   C3DParseDictionary.parseParamInt,
            'SCALE':        C3DParseDictionary.parseParamFloat,
            'RATE':         C3DParseDictionary.parseParamFloat,
            # 'MOVIE_DELAY':C3DParseDictionary.parseParamInt,
            'MOVIE_ID':     C3DParseDictionary.parseParamString,
            'X_SCREEN':     C3DParseDictionary.parseParamString,
            'Y_SCREEN':     C3DParseDictionary.parseParamString,
            'UNITS':        C3DParseDictionary.parseParamString,
            'LABELS':       C3DParseDictionary.parseParamString,
            'DESCRIPTIONS': C3DParseDictionary.parseParamString,
            # Test cases stored START/END fields as as uint32 but in indicated 2 16 bit words..
            'ACTUAL_START_FIELD': C3DParseDictionary.parseParamUInt_32,
            'ACTUAL_END_FIELD': C3DParseDictionary.parseParamUInt_32,
            # or the same parameter as both a 32 bit floating point and 32 bit unsigned integer (in different files)!
            'LONG_FRAMES': C3DParseDictionary.parseParamAnyInteger,
        }
    # end defineBasicDictionary()

    """
    --------------------------------------------------------
                        Print functions
    --------------------------------------------------------
    """

    def printHeaderInfo(self):
        ''' Print header info (partial) for the loaded file
        '''
        print("Frames (start,end):\t", self.reader.header.first_frame, self.reader.header.last_frame)
        print("Channels:\t\t", self.reader.header.point_count)
        print("Frame rate:\t\t", self.reader.header.frame_rate)
        print("Data Scalar:\t\t", self.reader.header.scale_factor, "  [negative if float representation is used]")
        print("Data format:\t\t", self.reader.proc_type)

    def printGroups(self):
        ''' Print a list over names of each group in the loaded file
        '''
        print(self.groups)

    def printParamHeader(self, group_id, param_id):
        ''' Print parameter header information. Prints name, dimension, and byte
            information for the parameter struct.
        '''
        param = self.getParam(group_id, param_id)
        print("Parameter Name: ", param.name)
        print("Dimensions: ", dim(param))
        print("Bytes per elem: ", param.bytes_per_element)  # , " |-1 indicates string data|")
        print("Total Bytes: ", sys.getsizeof(param.bytes))

    def printData(self, group_id, param_id):
        ''' Print the binary data struct for the specified parameter
        '''
        param = self.getParam(group_id, param_id)
        if(param is None):
            raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
        print(param.bytes)

    def printParameters(self, group_id):
        ''' Try parse all parameters in a group and print the result.
        '''
        group = self.getGroup(group_id)
        if group is None:					# Verify fetch
            return
        for pid in group.params:
            print('\'' + pid + '\': ', self.tryParseParam(group_id, pid))

    def printGroupInfo(self, group_id):
        ''' Print header information for all parameters in a group followed by a
            list of all attempts to parse parameter data in the group.

        Params:
        ----
        group_id: String identifier for the group to print info from.
        '''
        print(), print()
        # Print parameter headers for the group:
        for id in self.getParamNames(group_id):
            self.printParamHeader(group_id, id)
        print(), print()
        # Try parse all parameters and print each
        self.printParameters(group_id)

    def printIndividualParam(self, group_id, param_id):
        '''
        Print binary and each type of parsed data (Float, Signed Int, Unsigned Int)
        for a specified parameter. Useful for quickly debugging the data storage
        type for a parameter.

        Params:
        ----
        group_id: String identifier for the group containing the parameter.
        param_id: String identifier for the parameter to print info from, in the group.
        '''
        self.printData(group_id, param_id)							# Print binary data
        print("TRY: ", self.tryParseParam(group_id, param_id))		# print(try parse call)
        print("FLT: ", self.parseParamFloat(group_id, param_id))    # print(custom parse call)
        print("INT: ", self.parseParamInt(group_id, param_id))	    # print(custom parse call)
        print("UINT: ", self.parseParamUInt(group_id, param_id))    # print(custom parse call)

    def printFile(self):
        ''' Combination of printHeaderInfo() and printParameters() over all groups
        '''
        print(''), print(''), print("------------------------------")
        print("Header:")
        print("------------------------------"), print('')
        # Header
        self.printHeaderInfo()
        print(''), print(''), print("------------------------------")
        print("Paramaters:")
        print("------------------------------")
        # All group parameters
        for group in self.groups:
            print('')
            print('')
            print("'"+group+"':")
            print("------------------------------")
            self.printParameters(group)
        # end
        print("------------------------------")
# end
