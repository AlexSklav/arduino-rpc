# coding: utf-8
import jinja2
import numpy as np
import pandas as pd

from typing import Optional, Union
from path_helpers import path

from . import get_library_directory
from .dtypes import NP_STD_INT_TYPE, STD_ARRAY_TYPES


def get_c_commands_header_code(df_sig_info: pd.DataFrame, namespace: str,
                               extra_header: Optional[str] = None, extra_footer: Optional[str] = None,
                               **kwargs):
    # TODO: Update doc string to reflect generating commands header
    """
    Generate C++ command processor header code, which decodes a command from an
    incoming array and calls the corresponding method on a wrapped object
    instance.

    Arguments
    ---------

     - `df_sig_info`: A `pandas.DataFrame` with one row per method argument (as
       returned by `arduino_rpc.code_gen.get_multilevel_method_sig_frame`).
     - `namespace`: Namespace to wrap `CommandProcessor` header in.
     - `extra_header`: Extra text to insert before the namespace (optional).
     - `extra_footer`: Extra text to insert after the namespace (optional).
    """
    template = jinja2.Template(r'''
#ifndef ___{{ namespace.upper() }}__COMMANDS___
#define ___{{ namespace.upper() }}__COMMANDS___

#include <PacketParser.h>
#include "CArrayDefs.h"

{% if extra_header is not none %}
{{ extra_header }}
{% endif %}

namespace {{ namespace }} {

{% for (method_i, method_name, camel_name, arg_count), df_method_i in df_sig_info.groupby(['method_i', 'method_name', 'camel_name', 'arg_count']) %}
typedef struct __attribute__((packed)) {
{%- if arg_count > 0 %}
{{ '\n'.join('  ' + df_method_i.struct_atom_type + ' ' + df_method_i.arg_name + ';') }}
{%- endif %}
} {{ camel_name }}Request;

typedef struct __attribute__((packed)) {
{%- if df_method_i.return_atom_type.iloc[0] is not none %}
  {{ df_method_i.return_struct_atom_type.iloc[0] }} result;
{%- endif %}
} {{ camel_name }}Response;
{% endfor %}

{% for i, (method_i, method_name) in df_sig_info.drop_duplicates(subset='method_i')[['method_i', 'method_name']].iterrows() %}
static const int CMD_{{ method_name.upper() }} = {{ '0x%02x' % method_i }};
{%- endfor %}

}  // namespace {{ namespace }}

typedef PacketParser<FixedPacket> parser_t;
{% if extra_footer is not none %}
{{ extra_footer }}
{% endif %}

#endif  // ifndef ___{{ namespace.upper() }}__COMMANDS___
'''.strip())
    return template.render(df_sig_info=df_sig_info, namespace=namespace,
                           extra_header=extra_header,
                           extra_footer=extra_footer, **kwargs)


def get_c_command_processor_header_code(df_sig_info: pd.DataFrame, namespace: str,
                                        extra_header: Optional[str] = None, extra_footer: Optional[str] = None,
                                        **kwargs):
    # TODO: Update doc string to reflect generating command processor header
    """
    Generate C++ command processor header code, which decodes a command from an
    incoming array and calls the corresponding method on a wrapped object
    instance.

    Arguments
    ---------

     - `df_sig_info`: A `pandas.DataFrame` with one row per method argument (as
       returned by `arduino_rpc.code_gen.get_multilevel_method_sig_frame`).
     - `namespace`: Namespace to wrap `CommandProcessor` header in.
     - `extra_header`: Extra text to insert before the namespace (optional).
     - `extra_footer`: Extra text to insert after the namespace (optional).
    """
    template = jinja2.Template(r'''
#ifndef ___{{ namespace.upper() }}__COMMAND_PROCESSOR___
#define ___{{ namespace.upper() }}__COMMAND_PROCESSOR___

#include "CArrayDefs.h"
#include "Commands.h"

{% if extra_header is not none %}
{{ extra_header }}
{% endif %}

namespace {{ namespace }} {

template <typename Obj>
class CommandProcessor {
  /* # `CommandProcessor` #
   *
   * Each call to this functor processes a single command.
   *
   * All arguments are passed by reference, such that they may be used to form
   * a response.  If the integer return value of the call is zero, the call is
   * assumed to have no response required.  Otherwise, the arguments contain
   * must contain response values. */
protected:
  Obj &obj_;
public:
  CommandProcessor(Obj &obj) : obj_(obj) {}

  UInt8Array process_command(UInt8Array request_arr, UInt8Array buffer) {
    /* ## Call operator ##
     *
     * Arguments:
     *
     *  - `request_arr`: Serialized command request structure array,
     *  - `buffer`: Buffer array (available for writing output). */

    UInt8Array result;
    uint16_t &command = *reinterpret_cast<uint16_t *>(&request_arr.data[0]);

    // Interpret first byte of request as command code.
    switch (command) {
{% for (method_i, method_name, camel_name, arg_count), df_method_i in df_sig_info.groupby(['method_i', 'method_name', 'camel_name', 'arg_count']) %}
        case CMD_{{ method_name.upper() }}:
          {
            /* Cast buffer as request. */
    {% if arg_count > 0 %}
            {{ camel_name }}Request &request = *(reinterpret_cast
                                          <{{ camel_name }}Request *>
                                          (&request_arr.data[2]));
    {% endif %}
    {% if df_method_i.ndims.max() > 0 %}
            /* Add relative array data offsets to start payload structure. */
    {% for i, array_i in df_method_i[df_method_i.ndims > 0].iterrows() %}
            request.{{ array_i['arg_name'] }}.data = ({{ array_i.atom_type }} *)((uint8_t *)&request + (unsigned int)request.{{ array_i['arg_name'] }}.data);
    {%- endfor %}
    {%- endif -%}

    {%- if df_method_i.return_atom_type.iloc[0] is not none %}
            {{ camel_name }}Response response;

            response.result = {%- endif %}
            obj_.{{ method_name }}({% if arg_count > 0 %}{{ ', '.join('request.' + df_method_i.arg_name) }}{% endif %});
    {% if df_method_i.return_atom_type.iloc[0] is not none %}
            /* Copy result to output buffer. */
    {%- if df_method_i.return_ndims.iloc[0] > 0 %}
            /* Result type is an array, so need to do `memcpy` for array data. */
            uint32_t length = (response.result.length *
                               sizeof(response.result.data[0]));

            result.data = (uint8_t *)response.result.data;
            result.length = length;
    {%- else %}
            /* Cast start of buffer as reference of result type and assign result. */
            {{ camel_name }}Response &output = *(reinterpret_cast
                                                 <{{ camel_name }}Response *>
                                                 (&buffer.data[0]));
            output = response;
            result.data = buffer.data;
            result.length = sizeof(output);
    {%- endif %}
    {%- else %}
        result.data = buffer.data;
        result.length = 0;
    {%- endif %}
          }
          break;
{% endfor %}
      default:
        result.length = 0xFFFFFFFF;
        result.data = NULL;
    }
    return result;
  }
};

}  // namespace {{ namespace }}

{% if extra_footer is not none %}
{{ extra_footer }}
{% endif %}

#endif  // ifndef ___{{ namespace.upper() }}___
'''.strip())
    return template.render(df_sig_info=df_sig_info, namespace=namespace,
                           extra_header=extra_header,
                           extra_footer=extra_footer, **kwargs)


def get_python_code(df_sig_info: pd.DataFrame,
                    extra_header: Optional[str] = None, extra_footer: Optional[str] = None,
                    pointer_width: int = 16):
    """
    Generate Python `Proxy` class, with one method for each corresponding
    method signature in `df_sig_info`.  Each method on the `Proxy` class:

     - Encodes method command and Python arguments into a serialized command
       array.
     - Sends command to remote device.
     - Decodes the result into Python types.

    Arguments
    ---------

     - `df_sig_info`: A `pandas.DataFrame` with one row per method argument (as
       returned by `arduino_rpc.code_gen.get_multilevel_method_sig_frame`).
     - `extra_header`: Extra text to insert before class definition (optional).
     - `extra_footer`: Extra text to insert after class definition (optional).
    """
    # TODO: The size of an `*Array` struct depends on the architecture.
    #
    # Specifically, on 8-bit AVR processors, addresses are 16-bit, but on
    # 32-bit processors (e.g., Teensy 3.2 ARM) addresses are 32-bit.  Since one
    # of the `*Array` struct member variables (i.e., `data`) is a pointer, the
    # size of the structure differs based on the pointer size for the
    # architecture.
    #
    # How should we handle this?
    #
    # Take a pointer bit-width as an argument, `pointer_width=32`.
    template = jinja2.Template(r'''
import pandas as pd
import numpy as np
from nadamq.NadaMq import cPacket, PACKET_TYPES
{%- if extra_header is not none %}
{% if 'ProxyBase' not in extra_header -%}
from arduino_rpc.proxy import ProxyBase
{% endif -%}{%- endif %}

try:
    from google.protobuf.message import Message
    _translate = (lambda arg: arg.SerializeToString()
                  if isinstance(arg, Message) else arg)
except ImportError:
    _translate = lambda arg: arg

{% if extra_header is not none -%}
{{ extra_header }}
{%- endif %}


class Proxy(ProxyBase):
{%- for i, (method_i, method_name) in 
        df_sig_info.drop_duplicates(subset='method_i')[['method_i', 'method_name']].iterrows() %}
    _CMD_{{ method_name.upper() }} = {{ '0x%02x' % method_i }}
{%- endfor %}
    MAX_COMMAND_CODE = {{ df_sig_info.method_i.max() }}
{% for (method_i, method_name, camel_name, arg_count), df_method_i in 
        df_sig_info.groupby(['method_i', 'method_name', 'camel_name', 'arg_count']) %}
    def {{ method_name }}(self{% if arg_count > 0 %}, {{ ', '.join(df_method_i.arg_name) }}{% endif %}):
        command = np.dtype('uint16').type(self._CMD_{{ method_name.upper() }})
{%- if arg_count > 0 %}
        ARG_STRUCT_SIZE = {{ df_method_i.struct_size.sum() }}
{%- if df_method_i.ndims.max() > 0 %}
{% for i, array_i in df_method_i[df_method_i.ndims > 0].iterrows() %}
        {{ array_i['arg_name'] }} = _translate({{ array_i['arg_name'] }})
        if isinstance({{ array_i['arg_name'] }}, str):
            {{ array_i['arg_name'] }} = map(ord, {{ array_i['arg_name'] }})
        elif isinstance({{ array_i['arg_name'] }}, bytes):
            {{ array_i['arg_name'] }} = list(bytes({{ array_i['arg_name'] }}))
        # Argument is an array, so cast to appropriate array type.
        {{ array_i['arg_name'] }} = np.ascontiguousarray({{ array_i['arg_name'] }}, dtype='{{ array_i.atom_np_type }}')
{%- endfor %}
        array_info = pd.DataFrame([
{%- for arg_name in df_method_i.loc[df_method_i.ndims > 0, 'arg_name'] -%}
        {{ arg_name }}.shape[0], {% endfor -%}],
                                  index=[
{%- for arg_name in df_method_i.loc[df_method_i.ndims > 0, 'arg_name'] -%}
        '{{ arg_name }}', {% endfor -%}],
                                  columns=['length'])
        array_info['start'] = array_info.length.cumsum() - array_info.length
        array_data = b''.join([
{%- for arg_name in df_method_i.loc[df_method_i.ndims > 0, 'arg_name'] -%}
        {{ arg_name }}.tobytes(), {% endfor -%}])
{%- else %}
        array_data = b''
{%- endif %}
        payload_size = ARG_STRUCT_SIZE + len(array_data)
        struct_data = np.array([(
{%- for i, (arg_name, ndims, np_atom_type) in df_method_i[['arg_name', 'ndims', 'atom_np_type']].iterrows() -%}
{%- if ndims > 0 -%}
        array_info.length['{{ arg_name }}'], ARG_STRUCT_SIZE + array_info.start['{{ arg_name }}'], {# #}
{%- else -%}
        {{ arg_name }}, {# #}
{%- endif -%}
{% endfor %})],
                               dtype=[
{%- for i, (arg_name, ndims, np_atom_type) in df_method_i[['arg_name', 'ndims', 'atom_np_type']].iterrows() -%}
{%- if ndims > 0 -%}
        ('{{ arg_name }}_length', 'uint32'), ('{{ arg_name }}_data', 'uint{{ pointer_width }}'), {% else -%}
        ('{{ arg_name }}', '{{ np_atom_type }}'), {% endif %}{% endfor %}])
        payload_data = struct_data.tobytes() + array_data
{%- else %}
        payload_size = 0
        payload_data = b''
{%- endif %}

        payload_data = command.tobytes() + payload_data
        packet = cPacket(data=payload_data, type_=PACKET_TYPES.DATA)
        response = self._send_command(packet)
{% if df_method_i.return_atom_type.iloc[0] is not none %}
        result = np.frombuffer(response.data(), dtype='{{ df_method_i.return_atom_np_type.iloc[0] }}')
{% if df_method_i.return_ndims.iloc[0] > 0 %}
        # Return type is an array, so return entire array.
        return result
{% else %}
        # Return type is a scalar, so return first entry of array.
        return result[0]
{% endif -%}{%- else %}
        return response  
{% endif -%}
{%- endfor %}

{% if extra_footer is not none -%}
{{ extra_footer }}
{%- endif %}
'''.strip())
    df_sig_info_ = df_sig_info.copy()
    # Avoid shadowing builtins
    builtin_names = ['str', 'list', 'dict', 'set', 'len', 'sum', 'max',
                     'min', 'open', 'input', 'id', 'format', 'range', 'type']
    df_sig_info_.arg_name = df_sig_info_.arg_name.replace({name: name + '_' for name in builtin_names})
    return template.render(df_sig_info=df_sig_info_, extra_header=extra_header,
                           extra_footer=extra_footer, pointer_width=pointer_width,
                           )


def get_struct_sig_info_frame(df_sig_info: pd.DataFrame, pointer_width: int = 16) -> pd.DataFrame:
    df_sig_info = df_sig_info.copy()

    df_sig_info['struct_atom_type'] = df_sig_info.atom_type
    df_sig_info.loc[df_sig_info.ndims > 0, 'struct_atom_type'] = \
        df_sig_info.loc[df_sig_info.ndims > 0, 'atom_type'].map(STD_ARRAY_TYPES)

    df_sig_info = df_sig_info[~df_sig_info.return_atom_type.isin([np.NaN])].copy()  # This may get rid of some methods

    df_sig_info['return_atom_np_type'] = None
    none_mask = (~df_sig_info.return_atom_type.isin([None]))
    df_sig_info.loc[none_mask, 'return_atom_np_type'] = \
        df_sig_info.loc[none_mask, 'return_atom_type'].map(NP_STD_INT_TYPE)

    df_sig_info['return_struct_atom_type'] = df_sig_info['return_atom_type']
    df_sig_info.loc[df_sig_info.return_ndims > 0, 'return_struct_atom_type'] = \
        df_sig_info.loc[df_sig_info.return_ndims > 0, 'return_atom_type'].map(STD_ARRAY_TYPES)

    df_sig_info.loc[df_sig_info.arg_count > 0, 'atom_np_type'] = \
        df_sig_info.loc[df_sig_info.arg_count > 0, 'atom_type'].map(NP_STD_INT_TYPE)

    # __N.B.,__ The size of an `*Array` struct depends on the architecture.
    #
    # Specifically, on 8-bit AVR processors, addresses are 16-bit, but on
    # 32-bit processors (e.g., Teensy 3.2 ARM) addresses are 32-bit.  Since one
    # of the `*Array` struct member variables (i.e., `data`) is a pointer, the
    # size of the structure differs based on the pointer size for the
    # architecture.
    #
    # We handle this by taking a pointer bit-width as an argument,
    # default `pointer_width=16`.
    df_sig_info['struct_size'] = 0
    if (df_sig_info.arg_count > 0).any():
        df_sig_info.loc[df_sig_info.arg_count > 0, 'struct_size'] = \
            (df_sig_info.loc[df_sig_info.arg_count > 0, 'struct_atom_type']
             .map(lambda v: np.dtype('uint32').itemsize +  # *Array.length
                            np.dtype(f'uint{pointer_width}').itemsize  # *Array.data
            if v.endswith('Array') else np.dtype(NP_STD_INT_TYPE[v]).itemsize))  # assuming that nan entries are arrays

    return df_sig_info.replace(np.nan, None)


def generate_rpc_buffer_header(output_dir: Union[str, path], **kwargs) -> None:
    """
    .. versionchanged:: 1.11
        Add support for Python 3.  Specifically, use
        :meth:`path_helpers.path.text` method instead of
        :meth:`path_helpers.path.bytes` and open output file for writing in
        text mode.
    """
    import warnings

    source_dir = path(kwargs.pop('source_dir', get_library_directory()))
    template_filename = kwargs.get('template_filename', 'RPCBuffer.ht')

    default_settings = {'PACKET_SIZE': 80,
                        'I2C_PACKET_SIZE': 'PACKET_SIZE'}
    board_settings = {
        'uno': {'code': '__AVR_ATmega328P__', 'settings': default_settings},
        'mega2560': {'code': '__AVR_ATmega2560__', 'settings': dict(default_settings, PACKET_SIZE=256)},
        'default': {'settings': default_settings}
    }

    kwargs.update({'board_settings': board_settings})

    template_file = source_dir.joinpath(template_filename)
    output_file = output_dir.joinpath(template_file.namebase + '.h')

    if not kwargs.get('override', False):
        with output_file.open('w') as output:
            t = jinja2.Template(template_file.text())
            output.write(t.render(**kwargs))
            print(f"Generated '{output_file.name}' > {output_file}")
    elif output_file.isfile():
        warnings.warn(f'Skipping generation of buffer configuration since file already exists: `{output_file}`')
