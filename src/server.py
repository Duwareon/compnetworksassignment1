#!/usr/bin/env python3
import argparse as a
import socket as s
import threading as t
from multiprocessing import shared_memory
from time import sleep
from datetime import datetime
from os import remove, listdir, path, chdir, getcwd
 
# Make sure user is in local path
chdir(path.dirname(path.realpath(__file__)) + "/repo")

# Set up command line arguments
parser = a.ArgumentParser(
    prog='Networking Assignment 1 - server',
    description='A simple tcp socket server'
)

parser.add_argument('port', help='port to listen for tcp connection on', default=8080, nargs='?')
parser.add_argument('numclients', help='number of clients the server is willing to serve', default=3, nargs='?')

args = parser.parse_args()

# Format args as usable variables
addr = ("localhost", int(args.port))
numclients = int(args.numclients)


# Send file to given client
# Sends size of file in unsigned 32-bit integer format
def transmitfile(client, filepath):
    with open(filepath, "rb") as f:
        # Go to end of file, save cursor position/file size, go back to beginning
        f.seek(0, 2)
        datasize = f.tell() + 1
        f.seek(0, 0)

        # Send client file size
        print(f"Sending {client.name} file {filepath} ({datasize} bytes)")
        client.conn.send(datasize.to_bytes(4))

        # Read file to client
        data = f.read(1024)
        while data:
            client.conn.send(data)
            data = f.read(1024)
    print("File transmission complete.")

class ClientConn:
    def __init__(self, name, conn):
        self.name = name
        self.conn = conn
        self.addr = self.conn.getpeername()
        self.joindate = datetime.now()
        self.closedate = None

    # Close connection and set close time
    # Whether close time is set or not is the indicator of an active connection
    def close(self):
        self.conn.close()
        self.closedate = datetime.now()

    def runclientconn(self, cache):
        close = False
        try:
            while True:
                sendfile = False
                # Recieve message from client
                recv = self.conn.recv(1024)
                recvstring = recv.decode('utf-8')
                print(f"Receieved message from {self.addr[0]}: {recvstring}")
                
                # Format ACK message
                msg = recvstring + ' ACK'
                
                # Overwrite ACK message if command used
                if recvstring.startswith("exit"):
                    close = True
                if recvstring.startswith("name"): msg = self.name
                elif recvstring.startswith("status"):
                    msg = "\nOpen connections:\n" + cache.toString()
                elif recvstring.startswith("list"):
                    # Truncate list from command to get just path to dir to list, if it exists
                    dirpath = recvstring[5:] # Currently vulnerable to path attack, a la "list ../../report" or "list /home/user/"
                    if dirpath == '': dirpath = "."

                    # Check if path is a proper folder before listing
                    if path.exists(dirpath):
                        if not path.isfile(dirpath): 
                            msg = ' '.join(listdir(dirpath))
                        else:
                            msg = "Path is a file."
                    else:
                        msg = "Path does not exist."
                elif recvstring.startswith("download"):
                    filepath = recvstring[9:]

                    # Check if path is proper file before starting transfer
                    if path.exists(filepath):
                        if path.isfile(filepath):
                            sendfile = True
                            msg = "Transmitting file..."
                        else: msg = "Path is not a file."
                    else: msg = "Path does not exist."


                # Send message to client
                print(f"Sending message to {self.addr[0]}: {msg}")
                msgbytes = msg.encode('utf-8')
                self.conn.send(msgbytes)
                
                if close:
                    self.close()
                    break
                elif sendfile:
                    transmitfile(self, filepath)

        except BrokenPipeError:
            self.close()

class Cache:
    def __init__(self):
        self.cache = []

    # Add initiated client to cache
    def addtocache(self, conn):
        name = f"Client{self.lastconn():02d}"
        client = ClientConn(name, conn)
        self.cache.append(client)
        return client

    # Count active connections
    def numconns(self):
        num = 0
        for conn in self.cache:
            if conn.closedate == None:
                num += 1
        return num

    # Count all connections
    def lastconn(self):
        return len(self.cache)
    

    # Print all cached connections
    def toString(self):
        output = ""
        for conn in self.cache:
            joindate = conn.joindate.strftime("%Y %b %d %H:%M:%S:%f")
            if conn.closedate != None:
                closedate = conn.closedate.strftime("%Y %b %d %H:%M:%S:%f")
                output += f"{conn.name}: {conn.addr} connected at {joindate}, closed at {closedate}\n"
            else:
                output += f"{conn.name}: {conn.addr} connected at {conn.joindate}\n"

        return output

    # Close all connections in cache
    def closeall(self):
        for conn in self.cache:
            conn.close()


print(f"Creating server on localhost:{args.port} and listening for {numclients} clients...")
print(f"Allowing access to directory {getcwd()}.")
print("Exit program with CTRL+C.")

# Create cache
cache = Cache()
threads = []

# Build TCP socket
server = s.socket(s.AF_INET, s.SOCK_STREAM)
server.bind(addr)
server.listen()

while True:
    # Only allow certain number of clients
    if cache.numconns() < numclients:
        # Wait for new connection and initiate new client
        clientsocket, clientaddr = server.accept()
        print(f"Connection found from address {clientaddr[0]}:{clientaddr[1]}")

        conn = cache.addtocache(clientsocket)

        # Start a thread for new client
        threads.append(t.Thread(target=conn.runclientconn, args=(cache,)))
        threads[-1].start()

    # Wait for connection to open up to start listening again if client limit reached
    else:
        sleep(3)
