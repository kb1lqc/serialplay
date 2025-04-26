"""serial_stream_sim.py: A simple stream simulator for testing frame parsing and CRC checking.

Generates test frames with SYNC headers, payloads of two bytes per item, and a CRC-16-CCITT checksums.
Includes tools for generating noise and parsing frames from noisy streams.
"""

from collections import deque
from construct import Struct, Const, Int16ub, Array, this, Checksum
import crcmod
import io
import logging
import random
from typing import BinaryIO

# Define the frame start
SYNC = b'\xBE\xEF'

# Describes the layout of a single frame:
#   - sync      : Two bytes, fixed 0xBEEF, marks frame start
#   - length    : Two bytes, unsigned big-endian, number of two byte payload items
#   - payload   : List of two byte big-endian unsigned integers
#   - crc       : Two bytes, CRC-16-CCITT over sync + length + payload, provides basic error detection
Frame = Struct(
    "sync" / Const(SYNC),
    "length" / Int16ub,
    "payload" / Array(this.length, Int16ub),
    "crc" / Int16ub
)

# Pre-create CRC-16-CCITT funciton for performance
_crc_func = crcmod.mkCrcFun(
        0x11021,
        initCrc = 0xFFFF,
        rev = False,
        xorOut = 0x0000
)

# Create logger from logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crc16_ccitt(data: bytes) -> int:
    """Computes CRC-16-CCITT checksum for the provided data
    
    Args:
        data (bytes): Input data to compute CRC over.
        
    Returns:
        int: Computed CRC-16-CCITT value.
    """
    return _crc_func(data)

def make_frame(payload_len: int = 6) -> bytes:
    """Generates a frame with SYNC, payload length, payload, and CRC.

    Args:
        payload_len (int, optional): Number of two byte payload items. Defaults to 6.

    Returns:
        bytes: The generated frame (SYNC + length + payload + CRC).
    """
    # Two byte length, six byte payload, two byte CRC
    payload_items = [random.randint(0,0xFFFF) for _ in range(payload_len)]
    payload = b''.join(item.to_bytes(2, 'big') for item in payload_items)
    length = payload_len.to_bytes(2,'big') # 2-byte big-endian
    crc_val = crc16_ccitt(SYNC + length + payload)
    crc = crc_val.to_bytes(2, 'big')
    return SYNC + length + payload + crc

def make_noise() -> bytes:
    """Generates random noise bytes of random length between 1 and 4.

    Returns:
        bytes: Random noise bytes.
    """
    return bytes(random.randint(0, 255) for _ in range(random.randint(1,4)))

def find_sync(buffer: deque[int]) -> int:
    """Find the index of the SYNC in the buffer.

    Args:
        buffer (deque[int]): The byte buffer to search

    Returns:
        int: Index of sync start, or -1 if not found.
    """
    buf = list(buffer)
    for i in range(len(buf) - 1):
         if buf[i] == 0xBE and buf[i + 1] == 0xEF:
              return i
    return -1    

def read_serial_stream(stream: BinaryIO, chunk_size: int = 8) -> None:
    """Reads a serial data stream and parses one at a time.

    Continuously reads from the stream in chunks, searching for the SYNC header.
    Frames with invalid CRCs are reported and skipped.

    Args:
        stream (BinaryIO): A binary stream object (e.g. serial port or BytesIO).
        chunk_size (int, optional): Number of bytes to read per chunk, defaults to 8.

    Returns:
        None
    """
    buffer = deque()

    while True:
        chunk = stream.read(chunk_size)
        # No bytes, stop reading
        if not chunk:
            break
        buffer.extend(chunk)

        while True:
            idx = find_sync(buffer)
            if idx == -1:
                break

            for _ in range(idx):
                buffer.popleft()

            if len(buffer) < 4:
                break
            
            payload_len = (buffer[2] << 8 | buffer[3])
            total_frame_len = 2 + 2 + payload_len * 2 + 2

            if len(buffer) < total_frame_len:
                break

            # Extract full frame
            frame = bytes(buffer.popleft() for _ in range(total_frame_len))

            # Parse frame and CRC check
            try:
                parsed = Frame.parse(frame)
                computed_crc = crc16_ccitt(frame[:-2])
                if parsed.crc == computed_crc:
                    logger.info(f"Valid Frame: payload = {parsed.payload}")
                else:
                    logger.info(f"CRC mismatch: computed {computed_crc:#06x}, received {parsed.crc:#06x}, raw: {frame.hex()}")
            except Exception as e:
                logger.info(f"Frame parse error {e}, raw: {frame.hex()}")

if __name__ == "__main__":   
    # Build a fake serial stream
    stream = io.BytesIO()

    # Simulate stream: frame + optional noise
    for _ in range(10):
        stream.write(make_noise())  # noise before
        stream.write(make_frame())  # frame
        if random.random() < 0.3:
                stream.write(make_noise())

    stream.seek(0)

    # read from the stream
    read_serial_stream(stream)