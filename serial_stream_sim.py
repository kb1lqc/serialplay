import io
import serial
import random

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
    data = stream.read()
    print("Raw stream bytes:", data.hex(" "))