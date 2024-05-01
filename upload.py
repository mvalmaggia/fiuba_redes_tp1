import socket
import pickle
import os
from lib.packet import Packet, QueryType

# upload [-h] [-v | -q] [-H ADDR ] [-p PORT ] [-s FILEPATH ] [-n FILENAME ]
UDP_IP = "127.0.0.1"
UDP_PORT = 8000
PACKET_SIZE = 1024

def send_file(file_path, file_name, socket, udp_ip, udp_port):
    seq_num = 0
    try:
        with open(file_path, "r") as file:
            file_content = file.read(PACKET_SIZE)
            while file_content:
                data_packet = Packet(seq_num, False, file_name=file_name)
                data_packet.insert_data(file_content)
                socket.sendto(pickle.dumps(data_packet), (udp_ip, udp_port))
                file_content = file.read(PACKET_SIZE)
                seq_num += PACKET_SIZE
    except FileNotFoundError:
        print(f"File {file_path} not found")
        exit(1)

def upload(udp_ip, udp_port, file_path, file_name): 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # generate query to send to server
    upload_query_packet = Packet(0, False, QueryType.UPLOAD, file_name=file_name)

    serialised_packet = pickle.dumps(upload_query_packet)

    sock.sendto(serialised_packet, (udp_ip, udp_port))

    packet, server_address = sock.recvfrom(1024)
    decoded_packet = pickle.loads(packet)

    print(decoded_packet.get_ack())
    # if decoded_packet.get_ack() != 0:
    #     print("aca")
    #     return
    # print("received ack after request")

    send_file(file_path, file_name, sock, udp_ip, udp_port)

    upload_done_packet = Packet(0, True)

    sock.sendto(pickle.dumps(upload_done_packet), (udp_ip, udp_port))

def main():
    dir_path = os.path.dirname(__file__) + '/upload_test.txt'
    upload(UDP_IP, UDP_PORT, dir_path, "upload_test.txt")

if __name__ == "__main__":
    main()

