import socket
from threading import Thread, Lock
from segment import Segment, HEADER_SIZE, TOTAL_SIZE, WINDOW_SIZE
import time
import csv
from packet import SegmentedPacket
from hashlib import md5

class UDPClient(Thread):
    """
    Our TCP-like client class that handles the receiving of segments and sending of acks to achieve in-order and reliable delivery.
    Interfaces are similar to the socket library, with a blocking receive function.
    We implemented selective repeat as our windowing strategy to avoid retransmitting packets that have already been received.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.packets = {} # dict to store acked packets
        self.received = [] # list to store received packets
        self.ack = 0 # ack number
        self.window_size = WINDOW_SIZE 
        self.window_base = 0
        self.lock = Lock() # lock to protect the packets dict
        self.notify_receiver = Lock() # lock to notify receiver thread that window has moved (new packets are ready)
        self.addr = None # attached client address
        super().__init__()
    
    def run(self):
        with self.socket as s:
            while True:
                data, address = s.recvfrom(TOTAL_SIZE)
                if self.addr is None:
                    self.addr = address
                elif self.addr != address:
                    print("Possible fault: Received packet from unknown source, expected: {}, received: {}".format(self.addr, address))
                    continue
                seg = Segment.decode(data)
                if seg.seq < self.window_base + self.window_size: # selective repeat
                    with self.lock:
                        self.packets[seg.seq] = seg
                        self.ack = seg.seq
                        self.send_ack() # send ack for received packet
                        if seg.seq == self.window_base:
                            while self.window_base in self.packets:
                                self.received.append(self.packets[self.window_base])
                                self.window_base += 1 # advance window until unack'd packet
                            try:
                                self.notify_receiver.release() # notify that the window is moved and new packets can be received
                            except:
                                pass
                else:
                    print("Possible fault: Segment out of window, {}, {}, {}".format(seg.seq, self.window_base, self.window_size))

    def send_ack(self):
        self.socket.sendto(Segment(self.ack).encode().encode(), self.addr) # send ack for received packet
    
    def receive(self, count = 1):
        """
        A TCP socket-like receive function that blocks (with a lock that is notified
        by the receiver thread) until count packets are received
        """
        while len(self.received) < count:
            self.notify_receiver.acquire()
        ret = self.received[:count]
        with self.lock:
            self.received = self.received[count:]
        return ret



if __name__ == "__main__":
    client = UDPClient("172.30.0.3", 5000)
    client.start()
    # This concludes the implementation, the rest of the code is just to handle receiving the files and calculating the md5sum
    packets = {}
    times = {}
    large_times = []
    small_times = []
    start = None
    while True:
        for packet in client.receive():
            if start is None:
                start = time.perf_counter()
            name, curr, end, total, data = SegmentedPacket.decode(packet.data)
            if name not in packets:
                packets[name] = []
                times[name] = time.perf_counter()
            packets[name].append(data.decode())
            if len(packets[name]) == end + 1:
                payload = "".join(packets[name])[:total]
                print("Name {}".format(name))
                if name.decode().startswith("large"):
                    large_times.append(time.perf_counter() - start)
                    print("Large file time: {}".format(time.perf_counter() - times[name]))
                elif name.decode().startswith("small"):
                    print("Small file time: {}".format(time.perf_counter() - times[name]))
                    small_times.append(time.perf_counter() - start)
                print("Time taken: {}".format(time.perf_counter() - start))
                md5sum = md5(payload.encode()).hexdigest()
                with open(f"../objects/{name.decode()}.md5", "r") as f:
                    md5sum2 = f.read().strip()
                print(f"RESULT: {md5sum == md5sum2} MD5 sums: {md5sum} {md5sum2}")
                if len(large_times) == 10 and len(small_times) == 10:
                    avg_large = sum(large_times)/len(large_times)
                    avg_small = sum(small_times)/len(small_times)
                    total = time.perf_counter() - start
                    print("Average large time: {}".format(sum(large_times)/len(large_times)))
                    print("Average small time: {}".format(sum(small_times)/len(small_times)))
                    with open("results.csv", "r") as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                    if len(rows) == 0:
                        rows = [[], [], []]
                    rows[0].append(avg_large)
                    rows[1].append(avg_small)
                    rows[2].append(total)
                    with open("results.csv", "w") as f:
                        writer = csv.writer(f)
                        writer.writerows(rows)

                    exit(0)

                



            
        
                
            





    
