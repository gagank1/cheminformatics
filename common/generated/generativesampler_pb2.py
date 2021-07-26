# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: generativesampler.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='generativesampler.proto',
  package='nvidia.cheminformatics.grpc',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x17generativesampler.proto\x12\x1bnvidia.cheminformatics.grpc\"\xcb\x01\n\x0eGenerativeSpec\x12;\n\x05model\x18\x01 \x01(\x0e\x32,.nvidia.cheminformatics.grpc.GenerativeModel\x12\x0e\n\x06smiles\x18\x02 \x03(\t\x12\x13\n\x06radius\x18\x03 \x01(\x02H\x00\x88\x01\x01\x12\x19\n\x0cnumRequested\x18\x04 \x01(\x05H\x01\x88\x01\x01\x12\x14\n\x07padding\x18\x05 \x01(\x05H\x02\x88\x01\x01\x42\t\n\x07_radiusB\x0f\n\r_numRequestedB\n\n\x08_padding\"%\n\nSmilesList\x12\x17\n\x0fgeneratedSmiles\x18\x01 \x03(\t\"\"\n\rEmbeddingList\x12\x11\n\tembedding\x18\x01 \x03(\x02\"!\n\x0cIterationVal\x12\x11\n\titeration\x18\x01 \x01(\x05*9\n\x0fGenerativeModel\x12\x08\n\x04\x43\x44\x44\x44\x10\x00\x12\x0b\n\x07MolBART\x10\x01\x12\x0f\n\x0bMegaMolBART\x10\x02\x32\xbc\x03\n\x11GenerativeSampler\x12n\n\x11SmilesToEmbedding\x12+.nvidia.cheminformatics.grpc.GenerativeSpec\x1a*.nvidia.cheminformatics.grpc.EmbeddingList\"\x00\x12\x66\n\x0c\x46indSimilars\x12+.nvidia.cheminformatics.grpc.GenerativeSpec\x1a\'.nvidia.cheminformatics.grpc.SmilesList\"\x00\x12\x65\n\x0bInterpolate\x12+.nvidia.cheminformatics.grpc.GenerativeSpec\x1a\'.nvidia.cheminformatics.grpc.SmilesList\"\x00\x12h\n\x0cGetIteration\x12+.nvidia.cheminformatics.grpc.GenerativeSpec\x1a).nvidia.cheminformatics.grpc.IterationVal\"\x00\x62\x06proto3'
)

_GENERATIVEMODEL = _descriptor.EnumDescriptor(
  name='GenerativeModel',
  full_name='nvidia.cheminformatics.grpc.GenerativeModel',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='CDDD', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='MolBART', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='MegaMolBART', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=372,
  serialized_end=429,
)
_sym_db.RegisterEnumDescriptor(_GENERATIVEMODEL)

GenerativeModel = enum_type_wrapper.EnumTypeWrapper(_GENERATIVEMODEL)
CDDD = 0
MolBART = 1
MegaMolBART = 2



_GENERATIVESPEC = _descriptor.Descriptor(
  name='GenerativeSpec',
  full_name='nvidia.cheminformatics.grpc.GenerativeSpec',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='model', full_name='nvidia.cheminformatics.grpc.GenerativeSpec.model', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='smiles', full_name='nvidia.cheminformatics.grpc.GenerativeSpec.smiles', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='radius', full_name='nvidia.cheminformatics.grpc.GenerativeSpec.radius', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='numRequested', full_name='nvidia.cheminformatics.grpc.GenerativeSpec.numRequested', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='padding', full_name='nvidia.cheminformatics.grpc.GenerativeSpec.padding', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='_radius', full_name='nvidia.cheminformatics.grpc.GenerativeSpec._radius',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_numRequested', full_name='nvidia.cheminformatics.grpc.GenerativeSpec._numRequested',
      index=1, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_padding', full_name='nvidia.cheminformatics.grpc.GenerativeSpec._padding',
      index=2, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=57,
  serialized_end=260,
)


_SMILESLIST = _descriptor.Descriptor(
  name='SmilesList',
  full_name='nvidia.cheminformatics.grpc.SmilesList',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='generatedSmiles', full_name='nvidia.cheminformatics.grpc.SmilesList.generatedSmiles', index=0,
      number=1, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=262,
  serialized_end=299,
)


_EMBEDDINGLIST = _descriptor.Descriptor(
  name='EmbeddingList',
  full_name='nvidia.cheminformatics.grpc.EmbeddingList',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='embedding', full_name='nvidia.cheminformatics.grpc.EmbeddingList.embedding', index=0,
      number=1, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=301,
  serialized_end=335,
)


_ITERATIONVAL = _descriptor.Descriptor(
  name='IterationVal',
  full_name='nvidia.cheminformatics.grpc.IterationVal',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='iteration', full_name='nvidia.cheminformatics.grpc.IterationVal.iteration', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=337,
  serialized_end=370,
)

_GENERATIVESPEC.fields_by_name['model'].enum_type = _GENERATIVEMODEL
_GENERATIVESPEC.oneofs_by_name['_radius'].fields.append(
  _GENERATIVESPEC.fields_by_name['radius'])
_GENERATIVESPEC.fields_by_name['radius'].containing_oneof = _GENERATIVESPEC.oneofs_by_name['_radius']
_GENERATIVESPEC.oneofs_by_name['_numRequested'].fields.append(
  _GENERATIVESPEC.fields_by_name['numRequested'])
_GENERATIVESPEC.fields_by_name['numRequested'].containing_oneof = _GENERATIVESPEC.oneofs_by_name['_numRequested']
_GENERATIVESPEC.oneofs_by_name['_padding'].fields.append(
  _GENERATIVESPEC.fields_by_name['padding'])
_GENERATIVESPEC.fields_by_name['padding'].containing_oneof = _GENERATIVESPEC.oneofs_by_name['_padding']
DESCRIPTOR.message_types_by_name['GenerativeSpec'] = _GENERATIVESPEC
DESCRIPTOR.message_types_by_name['SmilesList'] = _SMILESLIST
DESCRIPTOR.message_types_by_name['EmbeddingList'] = _EMBEDDINGLIST
DESCRIPTOR.message_types_by_name['IterationVal'] = _ITERATIONVAL
DESCRIPTOR.enum_types_by_name['GenerativeModel'] = _GENERATIVEMODEL
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

GenerativeSpec = _reflection.GeneratedProtocolMessageType('GenerativeSpec', (_message.Message,), {
  'DESCRIPTOR' : _GENERATIVESPEC,
  '__module__' : 'generativesampler_pb2'
  # @@protoc_insertion_point(class_scope:nvidia.cheminformatics.grpc.GenerativeSpec)
  })
_sym_db.RegisterMessage(GenerativeSpec)

SmilesList = _reflection.GeneratedProtocolMessageType('SmilesList', (_message.Message,), {
  'DESCRIPTOR' : _SMILESLIST,
  '__module__' : 'generativesampler_pb2'
  # @@protoc_insertion_point(class_scope:nvidia.cheminformatics.grpc.SmilesList)
  })
_sym_db.RegisterMessage(SmilesList)

EmbeddingList = _reflection.GeneratedProtocolMessageType('EmbeddingList', (_message.Message,), {
  'DESCRIPTOR' : _EMBEDDINGLIST,
  '__module__' : 'generativesampler_pb2'
  # @@protoc_insertion_point(class_scope:nvidia.cheminformatics.grpc.EmbeddingList)
  })
_sym_db.RegisterMessage(EmbeddingList)

IterationVal = _reflection.GeneratedProtocolMessageType('IterationVal', (_message.Message,), {
  'DESCRIPTOR' : _ITERATIONVAL,
  '__module__' : 'generativesampler_pb2'
  # @@protoc_insertion_point(class_scope:nvidia.cheminformatics.grpc.IterationVal)
  })
_sym_db.RegisterMessage(IterationVal)



_GENERATIVESAMPLER = _descriptor.ServiceDescriptor(
  name='GenerativeSampler',
  full_name='nvidia.cheminformatics.grpc.GenerativeSampler',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=432,
  serialized_end=876,
  methods=[
  _descriptor.MethodDescriptor(
    name='SmilesToEmbedding',
    full_name='nvidia.cheminformatics.grpc.GenerativeSampler.SmilesToEmbedding',
    index=0,
    containing_service=None,
    input_type=_GENERATIVESPEC,
    output_type=_EMBEDDINGLIST,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='FindSimilars',
    full_name='nvidia.cheminformatics.grpc.GenerativeSampler.FindSimilars',
    index=1,
    containing_service=None,
    input_type=_GENERATIVESPEC,
    output_type=_SMILESLIST,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='Interpolate',
    full_name='nvidia.cheminformatics.grpc.GenerativeSampler.Interpolate',
    index=2,
    containing_service=None,
    input_type=_GENERATIVESPEC,
    output_type=_SMILESLIST,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='GetIteration',
    full_name='nvidia.cheminformatics.grpc.GenerativeSampler.GetIteration',
    index=3,
    containing_service=None,
    input_type=_GENERATIVESPEC,
    output_type=_ITERATIONVAL,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_GENERATIVESAMPLER)

DESCRIPTOR.services_by_name['GenerativeSampler'] = _GENERATIVESAMPLER

# @@protoc_insertion_point(module_scope)