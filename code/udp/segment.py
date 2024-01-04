WINDOW_SIZE = 2000
HEADER_SIZE = 10
SEGMENT_SIZE = 512
TOTAL_SIZE = HEADER_SIZE + SEGMENT_SIZE
class Segment:
    def __init__(self, seq, data = ''):
        self.seq = seq
        self.data = data
    
    def encode(self):
        return f"{self.seq:<{HEADER_SIZE}}{self.data:<{SEGMENT_SIZE}}"
    
    @staticmethod
    def decode(data):
        seq = int(data[:HEADER_SIZE].strip())
        data = data[HEADER_SIZE:]
        return Segment(seq, data)
    
