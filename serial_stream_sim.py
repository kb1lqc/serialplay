import io
import serial
import random
import crcmod
from collections import deque

# Frame constants
SYNC = b'\xBE\xEF'

def crc16_ccitt(data: bytes) -> int:
    crc_func = crcmod.mkCrcFun(
        0x11021,
        initCrc = 0xFFFF,
        rev = False,
        xorOut = 0x0000
    )
    return crc_func(data)

def make_frame(payload_len=6):
    # Two byte length, six byte payload, two byte CRC
    payload = bytes(random.randint(0,255) for _ in range (payload_len))
    length = len(payload).to_bytes(2,'big') # 2-byte big-endian
    crc_val = crc16_ccitt(SYNC + length + payload)
    crc = crc_val.to_bytes(2, 'big')
    return SYNC + length + payload + crc

def make_noise():
    return bytes(random.randint(0, 255) for _ in range(random.randint(1,4)))

def find_sync(buffer):
    buf = list(buffer)
    for i in range(len(buf) - 1):
         if buf[i] == 0xBE and buf[i + 1] == 0xEF:
              return i
    return -1    

def read_serial_stream(stream, chunk_size=8):
     buffer = deque()

     while True:
        chunk = stream.read(chunk_size)
        # no bytes, stop reading
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
            total_frame_len = 2 + 2 + payload_len + 2

            if len(buffer) < total_frame_len:
                break

            #Extract full frame
            frame = bytes(buffer.popleft() for _ in range (total_frame_len))

            # CRC check
            received_crc = int.from_bytes(frame[-2:], 'big')
            computed_crc = crc16_ccitt(frame[:-2])
            if received_crc == computed_crc:
                print(f" Valid Frame: {frame.hex()}")
            else:
                print(f"CRC mismatchj: {frame.hex()}")
        

if __name__ == "__main__":   
    # Build a fake serial stream
    stream = io.BytesIO()

    # Simulate stream: frame + optional noise
    for _ in range (10):
        stream.write(make_noise())  # noise before
        stream.write(make_frame())  # frame
        if random.random() < 0.3:
                stream.write(make_noise())

    stream.seek(0)

    # read from the stream
    read_serial_stream(stream)