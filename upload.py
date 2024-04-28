import socket
import pickle
from lib.packet import Packet, QueryType

# upload [-h] [-v | -q] [-H ADDR ] [-p PORT ] [-s FILEPATH ] [-n FILENAME ]
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
PACKET_SIZE = 1024

def send_file(file_path, file_name, socket, udp_ip, udp_port):
    try:
        with open(file_path, "r") as file:
            file_content = file.read(PACKET_SIZE)
            while file_content:
                # modificar sec_number aca
                data_packet = Packet(0, False, False)
                data_packet.insert_data(file_content)
                socket.sendto(pickle.dumps(data_packet), (udp_ip, udp_port))
                file_content = file.read(PACKET_SIZE)
    except FileNotFoundError:
        print(f"File {file_path} not found")
        exit(1)

def upload(udp_ip, udp_port, file_path, file_name): 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # generate query to send to server
    upload_query_packet = Packet(0, False, True, QueryType.UPLOAD)

    serialised_packet = pickle.dumps(upload_query_packet)

    sock.sendto(serialised_packet, (udp_ip, udp_port))

    send_file(file_path, file_name, sock, udp_ip, udp_port)

    upload_done_packet = Packet(0, True, False)

    sock.sendto(pickle.dumps(upload_done_packet), (udp_ip, udp_port))

def main():
    upload(UDP_IP, UDP_PORT, "test.txt", "test.txt")

if __name__ == "__main__":
    main()

