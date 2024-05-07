import select
import socket
import pickle
import os
import sys
from lib.packet import Packet, QueryType
import argparse
import logging as log

from lib.sec_num_registry import SecNumberRegistry
from lib.transmission import send_stop_n_wait, send_file

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

parser.add_argument('-s', '--src', metavar="FILEPATH", help="source file path",
                    default=os.path.dirname(__file__) +
                    '/data/uploads/test.txt')

# file name es el nombre con el cual se va a guardar el archivo en el
# server_storage
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


def upload(udp_ip, udp_port, file_path, file_name):
    if not os.path.isabs(file_path):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_directory, file_path)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    upload_query_packet = Packet(1, False, QueryType.UPLOAD,
                                 file_name=file_name)
    address = (udp_ip, udp_port)
    function_check_ack = lambda seq_num: check_ack_client(sock, seq_num)
    send_stop_n_wait(sock, address, upload_query_packet, function_check_ack)
    print("received ack after request, starting upload...")
    send_file(sock, address, file_path, 2, function_check_ack)
    print("upload finished")


def check_ack_client(sock, seq_num):
    readable, _, _ = select.select([sock], [], [], 0)
    if readable:
        packet, _ = sock.recvfrom(PACKET_SIZE)
        decoded_packet = pickle.loads(packet)
        if decoded_packet.ack and decoded_packet.seq_num == seq_num + 1:
            return True
    return False


def main():
    upload(UDP_IP, UDP_PORT, args.src, args.name)


if __name__ == "__main__":
    main()
