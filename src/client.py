#!/usr/bin/env python3
import argparse as a
import socket as s 
from os import path

# Loop through received data given file size from server
def receivefile(conn, filepath):
    print(f"Downloading file \"{filename}\" from server...")

    with open(filename, "wb") as f:
        datasize = int.from_bytes(conn.recv(4))
        while f.tell() < datasize:
            data = conn.recv(1024)
            f.write(data)
    print("File download complete")
    return


# Set up command line arguments
parser = a.ArgumentParser(
    prog="Networking Assignment 1 - client",
    description="A simple tcp socket client"
)

parser.add_argument('ip', help='ip to connect to tcp server at', default="localhost", nargs='?')
parser.add_argument('port', help='port to connect to tcp server on', default=8080, nargs='?')

args = parser.parse_args()

addr = (args.ip, int(args.port))

# Initialize TCP socket
print(f"Connecting to server on {args.ip}:{args.port}...")
client = s.socket(s.AF_INET, s.SOCK_STREAM)
client.settimeout(15)
client.connect(addr)

# Handshake with server, times out after 15 seconds
# For some reason, the client will think it connected to the server after reaching the client limit
# so we send a handshake packet in order to test whether the server actually responds.
print("Sending HANDSHAKE...")
msg = client.send("HANDSHAKE".encode('utf-8'))
recv = client.recv(1024).decode('utf-8')
print(f"Received \"{recv}\"")

# Enter message loop
while True:
    msgstr = input("Input message: ")
    msg = msgstr.encode('utf-8')
    client.send(msg)

    recv = client.recv(1024)
    recvstring = recv.decode('utf-8')
    print(f"Recieved message: {recvstring}")

    # Run command if used
    if msgstr.startswith('exit'):
        client.close()
        break
    elif msgstr.startswith('download') and recvstring.startswith("Transmitting"):
        filename = path.basename(msgstr[9:])
        try:
            with open(filename, "x") as f: f.write('')
        except: pass
        receivefile(client, msgstr[9:]) 
