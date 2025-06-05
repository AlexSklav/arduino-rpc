# coding: utf-8

STD_ARRAY_TYPES = {
    'int8_t': 'Int8Array',
    'int16_t': 'Int16Array',
    'int32_t': 'Int32Array',
    'int64_t': 'Int64Array',  # Add this if you support 64-bit ints
    'uint8_t': 'UInt8Array',
    'uint16_t': 'UInt16Array',
    'uint32_t': 'UInt32Array',
    'uint64_t': 'UInt64Array',  # Add this if you support 64-bit uints
    'float': 'FloatArray',
    'double': 'DoubleArray',  # Only if you ever map 'double'
    'char': 'Int8Array',  # (optional, if char* is used for byte arrays)

}

NP_ARRAY_TYPES = {
    'int8': 'Int8Array',
    'int16': 'Int16Array',
    'int32': 'Int32Array',
    'int64': 'Int64Array',  # Add this if needed
    'uint8': 'UInt8Array',
    'uint16': 'UInt16Array',
    'uint32': 'UInt32Array',
    'uint64': 'UInt64Array',  # Add this if needed
    'float32': 'FloatArray',
    'float64': 'DoubleArray',  # If you ever have C++ 'double' <-> np.float64
}

NP_STD_INT_TYPE = {
    'bool': 'uint8',
    'char': 'int8',
    'int8_t': 'int8',
    'uint8_t': 'uint8',
    'float': 'float32',
    'double': 'float64',
    'int32_t': 'int32',
    'int64_t': 'int64',
    'int16_t': 'int16',
    'uint32_t': 'uint32',
    'uint64_t': 'uint64',
    'uint16_t': 'uint16'
}
