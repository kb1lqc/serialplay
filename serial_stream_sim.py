import io
import serial
import random
from collections import deque

# Frame constants
SYNC = b'\xBE\xEF'

def make_frame():
    # Two byte length, six byte payload, two byte CRC
    payload = bytes(random.randint(0,255) for _ in range (6))
    length = len(payload).to_bytes(2,'big') # 2-byte big-endian
    crc = b'\x12\x34' # Placeholder CRC
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
        
            print(f"SYNC found at buffer index {idx}")
            for _ in range(idx):
                buffer.popleft()
            # Simulate a single SYNC detection
            break
        

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