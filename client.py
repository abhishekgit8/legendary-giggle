import socket
import queue
import pickle
import threading
import time 
import os

# Function to check if lock file exists
def check_lock_file():
    return os.path.exists('client.lock')

# Function to create lock file
def create_lock_file():
    with open('client.lock', 'w') as f:
        f.write('Client lock file')

# Function to remove lock file
def remove_lock_file():
    if os.path.exists('client.lock'):
        os.remove('client.lock')

# Check if lock file exists, if so, exit with error message
if check_lock_file():
    print("Error: The client is already in use.")
    #exit(1)

# Create lock file
create_lock_file()

def receive_thread(host, port, queue):
    # Create a TCP socket and listen for incoming connections
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Enable TCP Keep-Alive
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Set the idle time before sending the first keep-alive packet (in seconds)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)  # Adjust as needed
        # Set the interval between subsequent keep-alive packets (in seconds)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)  # Adjust as needed
        # Set the number of failed keep-alive probes before considering the connection dead
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)  
        s.settimeout(0.01)  # Timeout set to 10ms
        s.bind((host, port))
        s.listen()
        print("Waiting for connection...")
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    print('Connected by', addr)
                    while True:
                        start_time = time.time()
                        # Receive the length of the data
                        length_bytes = conn.recv(4)
                        if not length_bytes:
                            break  # If no data received, exit loop
                        # Convert length bytes to integer
                        data_length = int.from_bytes(length_bytes, byteorder='big')
                        # Receive the serialized data
                        serialized_data = b''
                        while len(serialized_data) < data_length:
                            packet = conn.recv(data_length - len(serialized_data))
                            if not packet:
                                break
                            serialized_data += packet
                        if len(serialized_data) != data_length:
                            print("Incomplete data received")
                            continue
                        # Unpickle the object
                        unpickled_obj = pickle.loads(serialized_data)
                        # Put the received object into the queue
                        queue.put(unpickled_obj)
                        end_time = time.time()  # Stop the timer
                        total_time = end_time - start_time
                        print(f"Total time taken: {total_time:.8f} seconds")
            except socket.timeout:
                pass
                # print("Timeout while waiting for connection")
            except EOFError:
                print("EOF Error")

q = queue.Queue(maxsize=100)
thread = threading.Thread(target=receive_thread, args=("127.0.0.1", 12345, q))
thread.daemon = True
thread.start()
count=0

try:
    while True:
        try:
            data = q.get(timeout=10)
            print("Received:", data)
        except queue.Empty:
            count+=1
            print("Server Error Occurred. Waiting...")
            if count >= 2:
                print("Server Error. Try again later!")
                break
except KeyboardInterrupt:
    print("Client stopping...")
finally:
    # Remove lock file on script termination
    remove_lock_file()
