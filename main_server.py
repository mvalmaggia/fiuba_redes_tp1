import socket
import threading
import pickle

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def handle_message(data, addr):
    print("received message: ", data)
    print("from: ", addr)

    received_packet = pickle.loads(data)

    if received_packet.get_is_query() == True:
        # check if is upload or download
        print("processing query")

    elif received_packet.get_fin() == True:
        # send ack for ending connection
        print("file transfer finished")

    else: 
        #aca tengo data si o si     

# Servidor
def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(1024)

        thread = threading.Thread(target=handle_message, args=(data, addr))
        thread.start()


if __name__ == "__main__":
    main()