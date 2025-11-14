# unpack_new_file_id.py

from struct import pack
from pyrogram.file_id import FileId, encode as encode_file_id, encode_file_ref


def unpack_new_file_id(new_file_id: str):
    """
    Convert Pyro v2+ new_file_id → (old file_id, file_ref).

    Returns:
        tuple(file_id: str, file_ref: str)
    """
    decoded = FileId.decode(new_file_id)

    # file_id = type:int, dc_id:int, media_id:int64, access_hash:int64
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )

    # file_ref = raw bytes → encoded
    file_ref = encode_file_ref(decoded.file_reference)

    return file_id, file_ref
