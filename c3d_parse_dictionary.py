import numpy as np


def filter_names(group):
	"""
	Iteration filter for dictionary keys, filtering all string keys
	"""
	for key, value in group.items():
		if isinstance(key, str):
			yield key
def islist(N):
	"""
	Check if 'N' object is any type of array
	"""
	return hasattr(N, '__len__') and (not isinstance(N, str))
def isvector(param):
	"""
	Check if the parameter is composed of single dimensional data.
	------
	param:	c3d.Param object
	"""
	return len(param.dimensions) < 2
def issingle(param):
	"""
	Check if the parameter is composed of single element.
	------
	param:	c3d.Param object
	"""
	return len(param.dimensions) == 0
def parseC3DArray(param, dtype=np.int8):
	"""
	Parse C3D parameter data array, returns either a single or
	multiple dimensional array depending on the parameter data shape.
	------
	param:	c3d.Param object
	"""
	return param._as_any(dtype)
	if 0 in param.dimensions[:]: 	# Check if any dimension is 0 (empty buffer)
		return [] 					# Buffer is empty
	#parseCount = int(nbytes(param) / param.bytes_per_element)
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
	"""
	Parse data as an array of, or single string.
	------
	param:	c3d.Param object
	"""
	data = parseC3DArray(param, dtype)
	if isvector(param): # Attribute is a single string vector
		return data.tostring().decode("ascii").strip()
	else: # Attribute is composed of an array of strings (or ndim?)
		list = []
		for word in data:
			list.append(word.tostring().decode("ascii").strip())
		return np.array(list)
#end parseC3DString()

class C3DParseDictionary:
    """
    C3D parser dictionary, facilitates association between parameter identifiers and parsing functions.
    """
    def __init__(self, filePath = None, parse_dict='basic'):

        # Set parse dictionary
        if parse_dict == 'basic':           self.parse_dict = C3DParseDictionary.defineBasicDictionary()
        elif isinstance(parse_dict, dict):  self.parse_dict = parse_dict
        else:                               self.parse_dict = []
        # Set c3d reader
        if filePath == None:                self.reader = None
        else:                               self.readFile(filePath)
    # end init()
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
    # end readFile()
    def close(self):
        self.file_handle.close()
    def getGroup(self, group_id):
        """
        Get a group from a group name id
        """
        return self.reader.get(group_id, None)
    # end getGroup()
    def getParam(self, group_id, param_id):
        """
        Fetch a parameter struct from group and param id:s
        """
        group = self.getGroup(group_id) 	# Fetch group
        if group is None:					# Verify fetch
            return None
        return group.get(param_id, None)	# Fetch param or return None if not found

    def getParamNames(self, group_id):
        group = self.getGroup(group_id) 		# Fetch group
        if group is None:						# Verify fetch
            return None
        return list(filter_names(group.params))	# Fetch param or return None if not found
    # end getParamNames()


    """
    --------------------------------------------------------
                        Byte Parsing functions
    --------------------------------------------------------
    """

    def tryParseParam(self, group_id, param_id):
        """
        Try parse a specified parameter, if parsing is not specified through the
        parse dictionary it will attempt to guess the appropriate format.
        """
        value = self.parseKnownParam(group_id, param_id)
        if value is None:					# Verify fetch
            param = self.getParam(group_id, param_id)
            if param == None:
                raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
            if param.bytes_per_element == 4:
                return self.parseParamFloat(group_id, param_id)
            else:
                return self.parseParamUInt(group_id, param_id)
        return value
    # end tryParseParam()
    def parseKnownParam(self, group_id, param_id):
        """
        Parse attributes defined in the parsing dictionary
        """
        func = self.parse_dict.get(param_id, None)
        if func == None:
            return None
        return func(self, group_id, param_id)
    # end parseKnownParam()
    def parseParamString(self, group_id, param_id):
        """
        Get a string or list of strings from the specified parameter
        """
        param = self.getParam(group_id, param_id)
        if param == None:
            raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
        return parseC3DString(param)
    # end parseParamString()
    def parseParamFloat(self, group_id, param_id):
        """
        Get a ndarray of integers from a group parameter
        """
        param = self.getParam(group_id, param_id)
        if(param == None):
            raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
        if(param.bytes_per_element == 4):
            return parseC3DArray(param, dtype=np.float32)
        elif(param.bytes_per_element == 8):
            return parseC3DArray(param, dtype=np.float64)
        else:
            return None
    # end parseParamFloat()
    def parseParamInt(self, group_id, param_id):
        """
        Get a ndarray of integers from a group parameter
        """
        param = self.getParam(group_id, param_id)
        if(param == None):
            raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
        if(param.bytes_per_element == -1): # String data
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
    # end parseParamInt()
    def parseParamUInt(self, group_id, param_id):
        """
        Get a ndarray of integers from a group parameter
        """
        param = self.getParam(group_id, param_id)
        if(param == None):
            raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
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
    # end parseParamUInt()

    """
    --------------------------------------------------------
                           Properties
    --------------------------------------------------------
    """

    @property
    def frame_rate(self):
        return max(1.0, self.reader.header.frame_rate)

    """
    --------------------------------------------------------
                        Interpret .c3d Data
    --------------------------------------------------------
    """

    def axis_interpretation(self, sys_axis_up=[0,0,1], sys_axis_forw=[0,1,0]):
        ''' Interpret X_SCREEN and Y_SCREEN parameters as the axis orientation for the system.

        Params:
        ----
        sys_axis_up:   Up axis vector defining convention used for the system (normal to the horizontal ground plane).
        sys_axis_forw: Forward axis vector defining the full system convention (forward orientation on ground plane).
        Returns:       3x3 orientation matrix for converting 3D data points.
        '''
        # Axis conversion dictionary
        axis_dict = {
        'X':[1.0,0,0],
        '+X':[1.0,0,0],
        '-X':[-1.0,0,0],
        'Y':[0,1.0,0],
        '+Y':[0,1.0,0],
        '-Y':[0,-1.0,0],
        'Z':[0,0,1.0],
        '+Z':[0,0,1.0],
        '-Z':[0,0,-1.0],
        }
        O_data = np.identity(3)

        try:
            axis_x = self.parseParamString('POINT', 'X_SCREEN')
            axis_y = self.parseParamString('POINT', 'Y_SCREEN')
            # Convert
            if axis_x in axis_dict and axis_y in axis_dict:
                axis_x = axis_dict[axis_x]
                axis_y = axis_dict[axis_y]
            O_data[:, 0] = axis_x
            O_data[:, 1] = axis_y
            O_data[:, 2] = np.cross(axis_x, axis_y)
        except:
            print('Unable to parse X/Y_SCREEN information for POINT data')

        # Define the system third axis as the cross product:
        O_sys = np.empty((3,3))
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
        'm': 1.0,
        'meter': 1.0,
        'cm': 1e-2,
        'centimeter': 1e-3,
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
        None:1.0
        }
        # Conversion factor (scale)
        conv_fac = 1.0
        # Convert data from unit defined in 'GROUP.UNITS'
        try:
            data_unit = self.parseParamString(group_id, param_id).lower()
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
        except:
            print("No unit of length found for %s data." % group_id)

        # Convert data to a specific unit (does not support conversion of different SI units)
        if type(sys_unit) is str:
            conv2unit = unit_dict[sys_unit.lower()]
            conv_fac = conv_fac / conv2unit

        # Return the conversion factor
        return conv_fac

    def parseLabels(self, group_id, param_id='LABELS'):
        """
        Get a list of labels from a group
        """
        return self.parseParamString(group_id, param_id)
    # end parseLabels()

    """
    --------------------------------------------------------
                        Parse Dictionaries
    --------------------------------------------------------
    """

    def defineParseFunction(self, param_id, function):
        """
        Append a parsing method to the dictionary
        """
        self.parse_dict[param_id] = function
    def defineBasicDictionary():
        """
        Basic dictionary
        """
        return {
            'USED':C3DParseDictionary.parseParamInt,
            'FRAMES':C3DParseDictionary.parseParamInt,
            'DATA_START':C3DParseDictionary.parseParamInt,
            'SCALE':C3DParseDictionary.parseParamFloat,
            'RATE':C3DParseDictionary.parseParamFloat,
            #'MOVIE_DELAY':C3DParseDictionary.parseParamInt,
            'MOVIE_ID':C3DParseDictionary.parseParamString,
            'X_SCREEN':C3DParseDictionary.parseParamString,
            'Y_SCREEN':C3DParseDictionary.parseParamString,
            'UNITS':C3DParseDictionary.parseParamString,
            'LABELS':C3DParseDictionary.parseParamString,
            'DESCRIPTIONS':C3DParseDictionary.parseParamString
        }
    # end defineBasicDictionary()

    """
    --------------------------------------------------------
                        Print functions
    --------------------------------------------------------
    """

    def printHeaderInfo(self):
        """
        Print header info (partial) for the loaded file
        """
        print("Frames (start,end):\t", self.reader.header.first_frame, self.reader.header.last_frame)
        print("Channels:\t\t", self.reader.header.point_count)
        print("Frame rate:\t\t", self.reader.header.frame_rate)
        print("Data Scalar:\t\t", self.reader.header.scale_factor, "  [negative if float representation is used]")
        print("Data format:\t\t", self.reader.proc_type)
    # end readFile()
    def printGroups(self):
        """
        Print a list over names of each group in the loaded file
        """
        print(self.groups)
    # end printGroups()
    def printParamHeader(self, group_id, param_id):
        """
        Print parameter header information. Prints name, dimension, and byte
        information for the parameter struct.
        """
        param = self.getParam(group_id, param_id)
        print("Parameter Name: ", param.name)
        print("Dimensions: ", dim(param))
        print("Bytes per elem: ", param.bytes_per_element)#, " (-1 indicate string data)")
        print("Total Bytes: ", sys.getsizeof(param.bytes))
    # end printParamHeader()
    def printData(self, group_id, param_id):
        """
        Print the binary data struct for the specified parameter
        """
        param = self.getParam(group_id, param_id)
        if(param == None):
            raise RuntimeError("Param ", param_id, " not Found in group ", group_id)
        print(param.bytes)
    # end printData()
    def printParameters(self, group_id):
        """
        Try parse all parameters in a group and print the result.
        """
        group = self.getGroup(group_id)
        if group is None:					# Verify fetch
            return
        for pid in group.params:
            print('\'' + pid + '\': ' , self.tryParseParam(group_id, pid))
    # end printParameters()
    def printGroupInfo(self, group_id):
        """
        Print header information for all parameters in a group followed by a
        list of all attempts to parse parameter data in the group.
        ----
        group_id: String identifier for the group to print info from.
        """
        print(), print()
        # Print parameter headers for the group:
        for id in self.getParamNames(group_id):
            self.printParamHeader(group_id, id)
        print(), print()
        # Try parse all parameters and print each
        self.printParameters(group_id)
    #end printGroupInfo()
    def printIndividualParam(self, group_id, param_id):
        """
        Print binary and each type of parsed data (Float, Signed Int, Unsigned Int)
        for a specified parameter. Useful for quickly debugging the data storage
        type for a parameter.
        ----
        group_id: String identifier for the group containing the parameter.
        param_id: String identifier for the parameter to print info from, in the group.
        """
        self.printData(group_id, param_id)							# Print binary data
        print("TRY: ", self.tryParseParam(group_id, param_id))		# print(try parse call)
        print("FLT: ", self.parseParamFloat(group_id, param_id))	# print(custom parse call)
        print("INT: ", self.parseParamInt(group_id, param_id))		# print(custom parse call)
        print("UINT: ", self.parseParamUInt(group_id, param_id))	# print(custom parse call)
    #end printIndividualParam()

    def printFile(self):
        """
        Combination of printHeaderInfo() and printParameters() over all groups
        """
        print(''),print(''), print("------------------------------")
        print("Header:")
        print("------------------------------"), print('')
        # Header
        self.printHeaderInfo()
        print(''),print(''), print("------------------------------")
        print("Paramaters:")
        print("------------------------------")
        # All group parameters
        for group in self.groups:
            print('')
            print('')
            print("'"+group+"':")
            print("------------------------------")
            self.printParameters(group)
        #end
        print("------------------------------")
    # end printFile()
#end
