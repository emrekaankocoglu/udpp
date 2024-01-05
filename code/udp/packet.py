
HEADER_SEGMENT_CURR_SIZE = 5 # size of the current fragment number
HEADER_SEGMENT_END_SIZE = 5 # size of the total number of fragments
HEADER_TOTAL_SIZE = 10 # size of the total size of the payload - used to get only the payload from the last fragment
HEADER_NAME_SIZE = 20  # size of the name of the resource

SEGMENT_SIZE = 512 - HEADER_NAME_SIZE - HEADER_SEGMENT_CURR_SIZE - HEADER_SEGMENT_END_SIZE - HEADER_TOTAL_SIZE # possible maximum size of the payload

class SegmentedPacket:
    """
    Our HTTP-like message class that handles the segmentation and reassembly of packets.
    Note that our Segment class only handles in-order and reliable delivery, but no details on the payload.
    This class handles the segmentation and reassembly of the payload, similar to a fragmented HTTP message.
    Note that this class may be renamed as a Fragment, but we decided to keep it as a Packet to avoid confusion with the Segment class.
    The wording segment is used to refer to the fragments of the payload, not to be confused with the Segment class, as this is further abstracted away from the reliable UDP layer.
    """
    def __init__(self,name,data):
        self.name = name # name of the resource
        self.data = data # payload
        self.length = len(data) # length of payload
        if len(data) % SEGMENT_SIZE != 0:
            self.data += " " * (SEGMENT_SIZE - (len(data) % SEGMENT_SIZE)) # pad with spaces to make it a multiple of SEGMENT_SIZE to make it easier to decode
    
    def construct(self):
        """
        Split the resource into fragments, and give each fragment a header containing the name, current fragment number, total number of fragments, and total size of the payload
        """
        segments = [] 
        curr = 0
        end = (len(self.data) // SEGMENT_SIZE)
        for i in range(curr, end):
            segments.append(f"{self.name:<{HEADER_NAME_SIZE}}{i:<{HEADER_SEGMENT_CURR_SIZE}}{end-1:<{HEADER_SEGMENT_END_SIZE}}{self.length:<{HEADER_TOTAL_SIZE}}{self.data[i*SEGMENT_SIZE:(i+1)*SEGMENT_SIZE]}")
            # left align properties to have a fixed size to make decoding easier
        return segments
    
    @staticmethod
    def reassemble(segments):
        """
        Reassemble a list of fragments into a resource
        """
        print(segments)
        if not segments:
            return None # fragments not complete
        segments = sorted(segments, key=lambda x: int(x[HEADER_NAME_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE])) # sort by fragment number
        end = int(segments[0][HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE].strip())
        complete = all([x in segments for x in range(end+1)]) # check if all fragments are present
        if not complete:
            return None # fragments not complete
        assembled = ""
        for segment in segments:
            name = segment[:HEADER_NAME_SIZE].strip()
            curr = int(segment[HEADER_NAME_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE].strip())

            total = int(segment[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE+HEADER_TOTAL_SIZE].strip())
            data = segment[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE:] # get payload
            assembled += data # add payload to assembled to have the complete resource
        return name, assembled[:total] # return name and resource removing padding
    
    @staticmethod
    def decode(data):
        """
        Decode a fragment from a string
        """
        name = data[:HEADER_NAME_SIZE].strip()
        curr = int(data[HEADER_NAME_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE].strip())
        end = int(data[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE].strip())
        total = int(data[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE:HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE+HEADER_TOTAL_SIZE].strip())
        data = data[HEADER_NAME_SIZE+HEADER_SEGMENT_CURR_SIZE+HEADER_SEGMENT_END_SIZE+HEADER_TOTAL_SIZE:]
        return name, curr, end, total, data



