# echo-client.py

import socket
from packet import Packet, HEADER_SIZE, HEADER_NAME_SIZE
import traceback
from hashlib import md5
import time
import csv
HOST = socket.gethostbyname("server")  # Use this if you are using docker compose
# if you do not use docker compose, instead of resolving name
# set host to the ip address directly
#HOST = "172.19.0.2"
PORT = 8000  # socket server port number

  # instantiate
 # connect to the server

with socket.socket() as s:
    s.connect((HOST, PORT))
    start = time.perf_counter() # start timer
    large_times = []
    small_times = []
    while True:
        try:
            size = s.recv(HEADER_SIZE) # receive size of packet
            if not size:
                break
            size = int(size.decode())
            name = s.recv(HEADER_NAME_SIZE)  # receive name of packet
            name = name.decode()
            name = name.split()[0]
            print(f"Receiving {name} with size {size}")
            data = b''
            data = s.recv(size)
            while len(data) < size:
                data += s.recv(size - len(data)) # receive all data of a packet
            if not data or len(data) != size:
                print(f"Error receiving data, {name}, {len(data), size}")
                break
            print(f"Received {name}, md5: {md5(data).hexdigest()}")
            if name.startswith("large"):
                large_times.append(time.perf_counter() - start) # calculate time taken
            elif name.startswith("small"):
                small_times.append(time.perf_counter() - start)
            print(f"Time taken: {time.perf_counter() - start}")
            with open(f"../objects/{name}.md5", "r") as f:
                md5sum = f.read().strip() # read md5 sum from file
            if md5(data).hexdigest() != md5sum:
                print(f"MD5 sum mismatch, {name}")
                break
            packet = Packet(name, data.decode())
            with open(f"{name}", 'w') as f:
                f.write(packet.data)
                
            print(f"Finished receiving {name}")
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
        except Exception as e:
            traceback.print_exc()
            break

