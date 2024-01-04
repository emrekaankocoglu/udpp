import socket
from threading import Thread, Lock
from segment import Segment, HEADER_SIZE, TOTAL_SIZE, WINDOW_SIZE
import queue
import time
from packet import SegmentedPacket
import glob
import os
from pathlib import Path

ALPHA = 0.125

class UDPServer(Thread):
    def __init__(self, host, port):
        self.dest = (host, port)
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)
        self.seq = 0
        self.window_size = WINDOW_SIZE
        self.window_base = 0
        self.lock = Lock()
        self.notify_sender = Lock()
        self.packets = {}
        self.constructed = {}
        self.send_queue = queue.Queue()
        self.data_queue = queue.Queue()
        self.segment_queue = queue.Queue()
        self.timeout = 0.5
        super().__init__()

    def ack_receiver(self):
        while True:
            data, addr = self.socket.recvfrom(TOTAL_SIZE)
            if addr != self.dest:
                print("Possible fault: Received packet from unknown source, expected: {}, received: {}".format(self.dest, addr))
                continue
            seg = Segment.decode(data)
            ack = seg.seq
            if ack < self.window_base:
                print("Possible fault: Received duplicate ack, {} < {}".format(ack, self.window_base))
                continue
            elif ack >= self.window_base + self.window_size:
                print("Possible fault: Received ack out of window")
                continue
            else:
                with self.lock:
                    self.packets[ack] = seg
                    self.timeout = (self.timeout * (1-ALPHA) + ALPHA * (time.perf_counter() - self.constructed[ack])) # dynamic timeout using rolling average
                    if self.timeout > 10:
                        self.timeout = 10
                    if ack == self.window_base:
                        self.window_base += 1
                        while self.window_base in self.packets:
                            self.window_base += 1
                        try:
                            self.notify_sender.release()
                        except:
                            pass
    def sender(self):
        while True:
            self.notify_sender.acquire()
            for i in range(self.window_base, self.window_base + self.window_size):
                if i not in self.packets and i not in self.constructed: # TODO: may go with maximum seq number
                    data = self.data_queue.get()
                    seg = Segment(i, data)
                    self.constructed[i] = time.perf_counter()
                    self.send_queue.put(seg) #TODO: change this to add upcoming packets
    
    def timer(self, seq, segment):
        time.sleep(self.timeout)
        if seq not in self.packets:
            self.send_queue.put(segment)
        
    def queue_sender(self):
        while True:
            seg = self.send_queue.get()
            self.socket.sendto(seg.encode().encode(), self.dest)
            thread = Thread(target=self.timer, args=(seg.seq,seg,))
            thread.start()
    
    def send(self, data):
        self.data_queue.put(data)

    def run(self):
        sender = Thread(target=self.sender)
        sender.start()
        ack_receiver = Thread(target=self.ack_receiver)
        ack_receiver.start()
        queue_sender = Thread(target=self.queue_sender)
        queue_sender.start()

def getfiles(dir):
    small_files = glob.glob(os.path.join(dir, 'small*.obj'))
    large_files = glob.glob(os.path.join(dir, 'large*.obj'))
    return [f for f in small_files if os.path.isfile(f)], [f for f in large_files if os.path.isfile(f)]

def construct_segments():
    dir = '../objects'
    small_files, large_files = getfiles(dir)
    small_segments = []
    for n in small_files:
        with open(n, 'r') as f:
            small_segments.extend(SegmentedPacket(Path(f.name).name, f.read()).construct())
    large_segments = []
    for n in large_files:
        with open(n, 'r') as f:
            large_segments.extend(SegmentedPacket(Path(f.name).name, f.read()).construct())
    return small_segments, large_segments

def interleave(small, large):
    segments = []
    for i in range(0, len(large)):
        if len(small) > i:
            segments.append(small[i])
        segments.append(large[i])
    return segments


if __name__ == "__main__":
    server = UDPServer("172.30.0.3", 5000)
    server.start()
    small_segments, large_segments = construct_segments()
    segments = interleave(small_segments, large_segments)
    for seg in segments:
        server.send(seg)


        
    





                        










        
