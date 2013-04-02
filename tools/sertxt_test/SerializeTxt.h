/* Copyright 2013 the SumatraPDF project authors (see AUTHORS file).
   License: Simplified BSD (see COPYING.BSD) */

#ifndef SerializeTxt_h
#define SerializeTxt_h

namespace sertxt {

struct FieldMetadata;

typedef struct {
    uint16_t                size;
    uint16_t                nFields;
    const char *            fieldNames;
    const FieldMetadata *   fields;
} StructMetadata;

typedef enum {
    TYPE_BOOL,
    TYPE_I16,
    TYPE_U16,
    TYPE_I32,
    TYPE_U32,
    TYPE_U64,
    TYPE_FLOAT,
    TYPE_COLOR,
    TYPE_STR,
    TYPE_WSTR,
    TYPE_STRUCT_PTR,
    TYPE_ARRAY,
    TYPE_NO_FLAGS_MASK = 0xFF,
    // a flag, if set the value is not to be serialized
    TYPE_NO_STORE_MASK = 0x4000,
    // a flag, if set the value is serialized in a compact form
    TYPE_STORE_COMPACT_MASK = 0x8000,
} Type;

// information about a single field
struct FieldMetadata {
    uint16_t         nameOffset;
    // from the beginning of the struct
    uint16_t         offset;
    Type             type;
    // for TYP_ARRAY and TYPE_STRUCT_PTR, otherwise NULL
    const StructMetadata * def;
};

uint8_t *   Serialize(const uint8_t *data,  const StructMetadata *def, size_t *sizeOut);
uint8_t*    Deserialize(char *data, size_t dataSize, const StructMetadata *def);
uint8_t*    DeserializeWithDefault(char *data, size_t dataSize, char *defaultData, size_t defaultDataSize, const StructMetadata *def);
void        FreeStruct(uint8_t *data, const StructMetadata *def);

} // namespace sertxt

#endif
