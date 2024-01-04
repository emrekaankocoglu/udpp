import socket
from threading import Thread, Lock
from segment import Segment, HEADER_SIZE, TOTAL_SIZE, WINDOW_SIZE
import time

class UDPClient(Thread):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.packets = {}
        self.received = []
        self.ack = 0
        self.window_size = WINDOW_SIZE
        self.window_base = 0
        self.lock = Lock()
        self.notify_receiver = Lock()
        self.addr = None
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
                if seg.seq < self.window_base + self.window_size:
                    with self.lock:
                        self.packets[seg.seq] = seg
                        self.ack = seg.seq
                        self.send_ack()
                        if seg.seq == self.window_base:
                            while self.window_base in self.packets:
                                print("Received segment: {}".format(self.window_base))
                                self.received.append(self.packets[self.window_base])
                                self.window_base += 1
                            try:
                                self.notify_receiver.release()
                            except:
                                pass
                else:
                    print("Possible fault: Segment out of window, {}, {}, {}".format(seg.seq, self.window_base, self.window_size))

    def send_ack(self):
        self.socket.sendto(Segment(self.ack).encode().encode(), self.addr)
    
    def receive(self, count = 1):
        while len(self.received) < count:
            self.notify_receiver.acquire()
        ret = self.received[:count]
        with self.lock:
            self.received = self.received[count:]
        return ret



if __name__ == "__main__":
    client = UDPClient("172.30.0.3", 5000)
    client.start()
    while True:
        for packet in client.receive():
            print("Received packet with seq: {}, data: {}".format(packet.seq, packet.data.split()[0]))
            time.sleep(1)
        
                
            





    
