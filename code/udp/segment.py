WINDOW_SIZE = 2000
HEADER_SIZE = 10
SEGMENT_SIZE = 512
TOTAL_SIZE = HEADER_SIZE + SEGMENT_SIZE
class Segment:
    """
    Our TCP-like segment class containing a sequence number and data
    HEADER_SIZE is the size of the sequence number, SEGMENT_SIZE is the size of the data
    """
    def __init__(self, seq, data = ''):
        self.seq = seq
        self.data = data
    
    def encode(self):
        return f"{self.seq:<{HEADER_SIZE}}{self.data:<{SEGMENT_SIZE}}" # left align data and sequence to have a fixed size to make decoding easier
    
    @staticmethod
    def decode(data):
        """
        Decode a segment from a string
        """
        seq = int(data[:HEADER_SIZE].strip())
        data = data[HEADER_SIZE:]
        return Segment(seq, data)
    
