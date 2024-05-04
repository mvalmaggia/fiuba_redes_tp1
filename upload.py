import socket
import pickle
import os
import sys
from lib.packet import Packet, QueryType
import argparse
import logging as log

# upload [-h] [-v | -q] [-H ADDR ] [-p PORT ] [-s FILEPATH ] [-n FILENAME ]

# optional arguments:-h,--help show this help message and exit
# -v, --verbose increase output verbosity
# -q, --quiet decrease output verbosity
# -H, --host server IP address
# -p, --port server port
# -s, --src source file path
# -n, --name file name

parser = argparse.ArgumentParser(
    description='Transferencia de un archivo del cliente hacia el servidor.')

group = parser.add_mutually_exclusive_group()
group.add_argument('-v', '--verbose', action='store_true',
                   help="increase output verbosity")
group.add_argument('-q', '--quite', action='store_false',
                   help="decrease output verbosity")

parser.add_argument('-H', '--host', metavar="ADDR", help="server IP address",
                    default="127.0.0.1")
parser.add_argument('-p', '--port', help="server port", default=8000)
# src es el archivo que se va a subir al servidor
parser.add_argument('-s', '--src', metavar="FILEPATH", help="source file path",
                    default=os.path.dirname(__file__) + '/files/test.txt')
# file name es el nombre con el cual se va a guardar el archivo en el storage
parser.add_argument('-n', '--name', metavar="FILENAME", help="file name",
                    default="upload_test.txt")

args = parser.parse_args()

UDP_IP = args.host
UDP_PORT = args.port

PACKET_SIZE = 1024


if args.verbose:
    log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    log.info("Verbose output.")
else:
    log.basicConfig(format="%(levelname)s: %(message)s")

TIMEOUT = 5


def stop_n_wait(socket, packet, udp_ip, udp_port, seq_num):
    socket.settimeout(TIMEOUT)
    try:
        print(f"Enviando el paquete: {packet}")
        socket.sendto(pickle.dumps(packet), (udp_ip, udp_port))

        ack_packet, server_address = socket.recvfrom(1024)
        decoded_packet = pickle.loads(ack_packet)

        if decoded_packet.get_ack() == seq_num + 1:
            return

    except TimeoutError:
        stop_n_wait(socket, packet, udp_ip, udp_port, seq_num)


def send_file(socket, file_path, file_name, udp_ip, udp_port):
    seq_num = 1
    try:
        with open(file_path, "r") as file:
            file_content = file.read(PACKET_SIZE)
            while file_content:
                seq_num += sys.getsizeof(file_content)

                data_packet = Packet(seq_num, False, file_name=file_name)
                data_packet.insert_data(file_content)
                stop_n_wait(socket, data_packet, udp_ip, udp_port, seq_num)

                file_content = file.read(PACKET_SIZE)              

    except FileNotFoundError:
        print(f"File {file_path} not found")
        exit(1)


def upload(udp_ip, udp_port, file_path, file_name): 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    upload_query_packet = Packet(0, False, QueryType.UPLOAD, 
                                 file_name=file_name)

    serialised_packet = pickle.dumps(upload_query_packet)
    sock.sendto(serialised_packet, (udp_ip, udp_port))

    packet, server_address = sock.recvfrom(1024)
    decoded_packet = pickle.loads(packet)

    print(decoded_packet.get_ack())
    if decoded_packet.get_ack() != 1:
        return
    print("received ack after request")

    send_file(sock, file_path, file_name, udp_ip, udp_port)

    upload_done_packet = Packet(0, True)

    sock.sendto(pickle.dumps(upload_done_packet), (udp_ip, udp_port))


def main():
    upload(UDP_IP, UDP_PORT, args.src, args.name)


if __name__ == "__main__":
    main()
