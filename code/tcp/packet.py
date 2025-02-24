import struct

HEADER_SIZE = 10
HEADER_NAME_SIZE = 20
class Packet:
    """
    Our HTTP-like message class that has name, data and data's size to get the payload from a byte stream like TCP.
    Main logic for encoding and decoding the data to be sent over TCP is here.
    """
    def __init__(self, name, data):
        self.name = name
        self.data = data
    def encode(self):
        payload_size = len(self.data)
        return f"{payload_size:<{HEADER_SIZE}}{self.name:<{HEADER_NAME_SIZE}}{self.data}"
    
    @staticmethod
    def decode(data):
        payload_size = int(data[:HEADER_SIZE].strip())
        name = data[HEADER_SIZE:HEADER_SIZE+HEADER_NAME_SIZE].strip()
        data = data[HEADER_SIZE+HEADER_NAME_SIZE:]
        return Packet(name, data[:payload_size])