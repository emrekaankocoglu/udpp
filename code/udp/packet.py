
HEADER_SEGMENT_CURR_SIZE = 5
HEADER_SEGMENT_END_SIZE = 5
HEADER_TOTAL_SIZE = 10
HEADER_NAME_SIZE = 20

SEGMENT_SIZE = 512 - HEADER_NAME_SIZE - HEADER_SEGMENT_CURR_SIZE - HEADER_SEGMENT_END_SIZE - HEADER_TOTAL_SIZE

class SegmentedPacket:
    def __init__(self,name,data):
        self.name = name
        self.data = data
        self.length = len(data)
        if len(data) % SEGMENT_SIZE != 0:
            self.data += " " * (SEGMENT_SIZE - (len(data) % SEGMENT_SIZE))
    
    def construct(self):
        segments = []
        curr = 0
        end = (len(self.data) // SEGMENT_SIZE)
        for i in range(curr, end):
            segments.append(f"{self.name:<{HEADER_NAME_SIZE}}{i:<{HEADER_SEGMENT_CURR_SIZE}}{end-1:<{HEADER_SEGMENT_END_SIZE}}{self.length:<{HEADER_TOTAL_SIZE}}{self.data[i*SEGMENT_SIZE:(i+1)*SEGMENT_SIZE]}")
        return segments
    
    @staticmethod
    def reassemble(segments):
        print(segments)
        if not segments:
            return None
        segments = sorted(segments, key=lambda x: int(x[HEADER_NAME_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE]))
        end = int(segments[0][HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE].strip())
        complete = all([x in segments for x in range(end+1)])
        if not complete:
            return None
        assembled = ""
        for segment in segments:
            name = segment[:HEADER_NAME_SIZE].strip()
            curr = int(segment[HEADER_NAME_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE].strip())

            total = int(segment[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE+HEADER_TOTAL_SIZE].strip())
            data = segment[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE:]
            assembled += data
        return name, assembled[:total]
    
    @staticmethod
    def decode(data):
        name = data[:HEADER_NAME_SIZE].strip()
        curr = int(data[HEADER_NAME_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE].strip())
        end = int(data[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE].strip())
        total = int(data[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE+HEADER_TOTAL_SIZE].strip())
        data = data[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE+HEADER_TOTAL_SIZE:]
        return name, curr, end, total, data



