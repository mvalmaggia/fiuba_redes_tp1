import select
import socket
import pickle
import os
import sys
import threading
import time

from lib.packet import Packet, QueryType
from lib.server import AlgorithmType
import argparse
import logging as log

from lib.sec_num_registry import SecNumberRegistry
from lib.transmission import send_stop_n_wait, send_file_sw, receive
from lib.window import Window

# upload [-h] [-v | -q] [-H ADDR ] [-p PORT ] [-s FILEPATH ] [-n FILENAME ]

# optional arguments:-h,--help show this help message and exit
# -v, --verbose increase output verbosity
# -q, --quiet decrease output verbosity
# -H, --host server IP address
# -p, --port server port
# -s, --src source file path
# -n, --name file name

PACKET_SIZE = 1024
TIMEOUT = 5


def upload(udp_ip, udp_port, file_path, file_name, algorithm=AlgorithmType.GBN):
    if not os.path.isabs(file_path):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_directory, file_path)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    upload_query_packet = Packet(1, False, QueryType.UPLOAD,
                                 file_name=file_name)
    address = (udp_ip, udp_port)
    if algorithm == AlgorithmType.SW:
        function_check_ack = lambda seq_num: check_ack_client(sock, seq_num)
        send_stop_n_wait(sock, address, upload_query_packet, function_check_ack)
        print("received ack after request, starting upload...")
        send_file_sw(sock, address, file_path, 2, function_check_ack, algorithm=AlgorithmType.SW)
    else:
        window = Window(4, address, lambda client_address, packet: send_straightforward(sock, client_address, packet))
        thread_window_manager = threading.Thread(target=window_manager, args=(window, sock))
        thread_window_manager.start()
        send_gbn(sock, address, upload_query_packet, window)
        print("received ack after request, starting upload...")
        send_file_gbn(sock, address, file_path, 2, window)
        thread_window_manager.join()


    print("upload finished")


def window_manager(window: Window, sock):
    # Si hay un nuevo ack, limpia los paquetes de la ventana y reinicio el temporizador
    # Como corre en un nuevo hilo, se queda esperando a que llegue un ack
    while True:
        decoded_packet, _ = receive(sock)
        if decoded_packet.get_ack():
            print(f"Se recibio el paquete: {decoded_packet.seq_num - 1}")
            window.remove_confirmed(decoded_packet.seq_num)
            window.restart_timer()
        if decoded_packet.get_fin():
            print("Fin de la transmision")
            break
    window.close_window()

def send_file_gbn(sock, client_address, file_path, start_sec_num, window: Window):
    print(f"Enviando archivo {file_path}")
    # Primero se abre el archivo y se va leyendo de a pedazos de 1024 bytes para enviarlos al cliente en paquetes
    with open(file_path, "rb") as file:
        file_content = file.read(2048)
        # print(f"Enviando paquete {sec_num} con {len(file_content)} bytes")
        while file_content:
            data_packet = Packet(start_sec_num, False)
            data_packet.insert_data(file_content)
            send_gbn(sock, client_address, data_packet, window)
            file_content = file.read(2048)
            start_sec_num += 1
        # Se envia un paquete
        fin_packet = Packet(start_sec_num, True)
        send_gbn(sock, client_address, fin_packet, window)


def send_gbn(sock, client_address, packet, window):
    while True:
        if packet.ack or window.try_add_packet(packet):
            sock.sendto(pickle.dumps(packet), client_address)
            # print(f"Enviando paquete {packet.seq_num} a {client_address}")
            break
        else:
            print(f"Ventana llena, esperando para enviar paquete {packet.seq_num} a {client_address}")
            # TODO: Implementar un mecanismo de espera más eficiente (eventos)
            time.sleep(0.5)  # Espera activa, considerar usar un mecanismo de espera más eficiente

def send_straightforward(sock, client_address, packet):
    sock.sendto(pickle.dumps(packet), client_address)
    # print(f"Enviando paquete {packet.seq_num} a {client_address}")


def check_ack_client(sock, seq_num):
    readable, _, _ = select.select([sock], [], [], 0)
    if readable:
        packet, _ = sock.recvfrom(PACKET_SIZE)
        decoded_packet = pickle.loads(packet)
        if decoded_packet.ack and decoded_packet.seq_num == seq_num + 1:
            return True
    return False


def main():
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
    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    upload(UDP_IP, UDP_PORT, args.src, args.name, algorithm=AlgorithmType.GBN)


if __name__ == "__main__":
    main()
