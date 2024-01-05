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
    """
    Our UDP-like server class that handles the sending of segments and receiving of acks to achieve in-order and reliable delivery.
    We implemented selective repeat as our windowing strategy to avoid retransmitting packets that have already been received.
    We tried to keep it clean as possible with least number of locks and thread-safe queues to avoid deadlocks.
    """
    def __init__(self, host, port):
        self.dest = (host, port)
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)
        self.seq = 0
        self.window_size = WINDOW_SIZE
        self.window_base = 0
        self.lock = Lock() # lock to protect the packets dict
        self.notify_sender = Lock() # lock to notify sender thread that window has moved
        self.packets = {} # dict to store acked packets
        self.constructed = {} # dict to store constructed packets
        self.send_queue = queue.Queue() # queue to store segments to be sent to the socket
        self.data_queue = queue.Queue() # queue to store data to be constructed into segments by the sender thread
        self.segment_queue = queue.Queue()
        self.timeout = 0.5 # initial timeout
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
                # print("Possible fault: Received duplicate ack, {} < {}".format(ack, self.window_base))
                continue
            elif ack >= self.window_base + self.window_size:
                print("Possible fault: Received ack out of window")
                continue
            else:
                with self.lock:
                    self.packets[ack] = seg # add ack'd packet to dict
                    self.timeout = (self.timeout * (1-ALPHA) + ALPHA * (time.perf_counter() - self.constructed[ack])) # dynamic timeout using rolling average using RTT
                    if self.timeout > 10:
                        self.timeout = 10 # cap timeout at 10 seconds to avoid waiting too long
                    if ack == self.window_base:
                        self.window_base += 1
                        while self.window_base in self.packets:
                            self.window_base += 1 # advance window until unack'd packet
                        try:
                            self.notify_sender.release() # notify that the window is moved and new packets can be sent
                        except:
                            pass
    def sender(self):
        """
        Thread that only handles constructing segments from the data queue added by the send function.
        """
        while True:
            self.notify_sender.acquire() # wait until window is moved to a unsent packet
            for i in range(self.window_base, self.window_base + self.window_size):
                if i not in self.packets and i not in self.constructed: # if packet is not in constructed (already sent once), it should not be in queue again by the sender, only by the timer when it fails
                    data = self.data_queue.get() # construct segment from data by attaching the next sequence number
                    seg = Segment(i, data)
                    self.constructed[i] = time.perf_counter() # record time of construction to calculate RTT
                    self.send_queue.put(seg) 
    
    def timer(self, seq, segment):
        time.sleep(self.timeout) 
        if seq not in self.packets: # if ACK is not received, resend after wait
            self.send_queue.put(segment)
        
    def queue_sender(self):
        """
        Thread that only handles sending packets to the socket from the queue added by the sender and timer thread.
        This is to avoid multiple threads sending to the socket at the same time, or block either of the threads
        """
        while True:
            seg = self.send_queue.get()
            self.socket.sendto(seg.encode().encode(), self.dest)
            thread = Thread(target=self.timer, args=(seg.seq,seg,)) # start timer thread to wait for ack, if not received, resend
            thread.start()
    
    def send(self, data):
        """
        Our TCP-like send function that adds to the servers buffer
        """
        self.data_queue.put(data)

    def run(self):
        """
        Starts the sender, ack_receiver and queue_sender threads
        """
        sender = Thread(target=self.sender)
        sender.start()
        ack_receiver = Thread(target=self.ack_receiver)
        ack_receiver.start()
        queue_sender = Thread(target=self.queue_sender)
        queue_sender.start()

"""
Following only handles file operations and constructing the segments.
"""

def getfiles(dir):
    small_files = glob.glob(os.path.join(dir, 'small*.obj'))
    large_files = glob.glob(os.path.join(dir, 'large*.obj'))
    return [f for f in small_files if os.path.isfile(f)], [f for f in large_files if os.path.isfile(f)]

def construct_segments():
    """
    Split the files into segments to fit the segment size
    """
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
    """
    Interleave the segments from small and large files to handle simultaneous transmission.
    This is to avoid the large files blocking the small files from being sent (HoL blocking).
    """
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
        server.send(seg) # tcp-like send to socket, abstracting away the segmenting and interleaving


        
    





                        










        
