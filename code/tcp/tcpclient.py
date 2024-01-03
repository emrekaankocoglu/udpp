# echo-client.py

import socket
from packet import Packet, HEADER_SIZE, HEADER_NAME_SIZE
import traceback
from hashlib import md5
HOST = socket.gethostbyname("server")  # Use this if you are using docker compose
# if you do not use docker compose, instead of resolving name
# set host to the ip address directly
#HOST = "172.19.0.2"
PORT = 8000  # socket server port number

  # instantiate
 # connect to the server

with socket.socket() as s:
    s.connect((HOST, PORT))
    while True:
        try:
            size = s.recv(HEADER_SIZE)
            if not size:
                break
            size = int(size.decode())
            name = s.recv(HEADER_NAME_SIZE)
            name = name.decode()
            name = name.split()[0]
            print(f"Receiving {name} with size {size}")
            data = b''
            data = s.recv(size)
            while len(data) < size:
                data += s.recv(size - len(data))
            if not data or len(data) != size:
                print(f"Error receiving data, {name}, {len(data), size}")
                break
            print(f"Received {name}, md5: {md5(data).hexdigest()}")
            with open(f"../objects/{name}.md5", "r") as f:
                md5sum = f.read().strip()
            if md5(data).hexdigest() != md5sum:
                print(f"MD5 sum mismatch, {name}")
                break
            packet = Packet(name, data.decode())
            with open(f"{name}", 'w') as f:
                f.write(packet.data)
                
            print(f"Finished receiving {name}")
        except Exception as e:
            traceback.print_exc()
            break

