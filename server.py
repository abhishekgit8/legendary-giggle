import socket
import pickle
import threading
from queue import Queue
import time
import numpy as np
import os

class TCPConnectionThread(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.queue = Queue()
        self.stop_event = threading.Event()
        self.sock = None

    def connect(self):
        count=0
        while not self.stop_event.is_set():
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                return True
            except Exception as e:
                print("Error connecting:", e)
                time.sleep(1)  # Retry after 1 second
                count+=1
                if(count>=10):
                    print("No response from client,Try Again Later")
                    os._exit(0)

        return False

    def run(self):
        while not self.stop_event.is_set():
            if not self.sock:
                if not self.connect():
                    # If unable to connect, wait before retrying
                    time.sleep(1)
                    continue
                    
            try:
                while not self.stop_event.is_set():
                    if not self.queue.empty():
                        data = self.queue.get()
                        # Pickle the data
                        serialized_data = pickle.dumps(data)
                        # Calculate the length of the data
                        data_length = len(serialized_data)
                        # Convert data length to bytes (4 bytes for an integer)
                        length_bytes = data_length.to_bytes(4, byteorder='big')
                        # Send the length of the data
                        self.sock.sendall(length_bytes)
                        # Send the data
                        self.sock.sendall(serialized_data)
                    else:
                        time.sleep(0.1)  # Sleep briefly to avoid busy waiting
            except Exception as e:
                print("Error sending data:", e)
                self.sock.close()
                self.sock = None

    def stop(self):
        self.stop_event.set()
        if self.sock:
            self.sock.close()

    def send_message(self, obj):
        self.queue.put(obj)

# Example usage
host = '127.0.0.1'
port = 12345

# Start the connection thread
connection_thread = TCPConnectionThread(host, port)
connection_thread.start()

# Send messages asynchronously (example loop)
try:
    while True:
        obj1 = [1, 2, np.random.randint(10)]
        obj2 = {'a': 1, 'b': 2}
        connection_thread.send_message(obj1)
        connection_thread.send_message(obj2)
        time.sleep(0.001)
except KeyboardInterrupt:
    print("Stopping...")
    connection_thread.stop()
    connection_thread.join()
