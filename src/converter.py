"""Binary file to 24-bit BMP conversion."""

import math
import os
import struct
import tempfile
from pathlib import Path
from typing import Callable


BMP_HEADER_SIZE = 54
MAX_BMP_SIZE = 0xFFFFFFFF
COPY_CHUNK_SIZE = 1024 * 1024


def convert_to_bmp(
    source_path: str | Path,
    output_path: str | Path,
    progress_callback: Callable[[int], None] | None = None,
) -> dict[str, int]:
    """Write a file's bytes as the pixel data of a 24-bit BMP image."""
    source = Path(source_path).expanduser()
    output = Path(output_path).expanduser()
    if source.resolve() == output.resolve():
        raise ValueError("The destination must be different from the source file.")

    source_size = source.stat().st_size
    content_pixels = math.ceil(source_size / 3)
    side = max(1, math.ceil(math.sqrt(content_pixels)))
    width = height = side
    row_bytes = width * 3
    padding = (-row_bytes) % 4
    pixel_data_size = (row_bytes + padding) * height
    file_size = BMP_HEADER_SIZE + pixel_data_size

    if width > 0x7FFFFFFF or height > 0x7FFFFFFF or file_size > MAX_BMP_SIZE:
        raise ValueError("The file is too large for the 24-bit BMP format.")

    header = struct.pack(
        "<2sIHHIIiiHHIIiiII",
        b"BM",
        file_size,
        0,
        0,
        BMP_HEADER_SIZE,
        40,
        width,
        height,
        1,
        24,
        0,
        pixel_data_size,
        2835,
        2835,
        0,
        0,
    )

    temporary_path: str | None = None
    last_reported = -1
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False
        ) as output_file:
            temporary_path = output_file.name
            output_file.write(header)
            with source.open("rb") as input_file:
                for row in range(height):
                    row_remaining = row_bytes
                    while row_remaining:
                        chunk = input_file.read(min(row_remaining, COPY_CHUNK_SIZE))
                        if not chunk:
                            break
                        output_file.write(chunk)
                        row_remaining -= len(chunk)
                    if row_remaining:
                        output_file.write(b"\x00" * row_remaining)
                    if padding:
                        output_file.write(b"\x00" * padding)

                    percent = int((row + 1) * 100 / height)
                    if progress_callback and percent != last_reported:
                        progress_callback(percent)
                        last_reported = percent

        os.replace(temporary_path, output)
    except Exception:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
        raise

    return {
        "source_size": source_size,
        "file_size": file_size,
        "pixels": content_pixels,
        "width": width,
        "height": height,
    }
