# echo-server.py

import socket
from sender import TCPSender
import traceback
HOST = "server"  # Set to the IP address of the server eth0 if you do not use docker compose 
PORT = 8000  # Port to listen on (non-privileged ports are > 1023)

# This implementation supports only one client
# You have to implement threading for handling multiple TCP connections

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            try:
                sender = TCPSender(conn) # create a sender thread for each client
                sender.run()
            except Exception as e:
                traceback.print_exc()
                break

