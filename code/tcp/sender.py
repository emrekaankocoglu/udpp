from packet import Packet, HEADER_SIZE, HEADER_NAME_SIZE
from threading import Thread
import socket
import os
import glob
from traceback import print_exc
from pathlib import Path

class TCPSender(Thread):
    def __init__(self, socket):
        super().__init__()
        self.socket = socket

    def getfiles(self,dir):
        small_files = glob.glob(os.path.join(dir, 'small*.obj'))
        large_files = glob.glob(os.path.join(dir, 'large*.obj'))
        return [f for f in small_files if os.path.isfile(f)], [f for f in large_files if os.path.isfile(f)]

    def run(self):
        dir = '../objects'
        small_files, large_files = self.getfiles(dir)
        while True:
            try:
                if len(small_files) == 0 and len(large_files) == 0:
                    break
                with open(small_files.pop(), 'r') as f:
                    data = f.read()
                    packet = Packet(Path(f.name).name, data)
                    self.socket.send(packet.encode().encode())
                    print(f"Sent {Path(f.name).name}")
                with open(large_files.pop(), 'r') as f:
                    data = f.read()
                    packet = Packet(Path(f.name).name, data)
                    self.socket.send(packet.encode().encode())
            except BrokenPipeError as e:
                self.socket.close()
                break
            except OSError as e:
                self.socket.close()
                print_exc()
                break
            except Exception as e:
                print_exc()
                break
        self.socket.close()
        return






