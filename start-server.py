import pickle
import sys
import threading
import argparse
from socket import *
from lib.packet import Packet
import os
# Por defecto
verbose = True

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000


# Formato linea de comando:
# start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]
# -h:      mostrar ayuda de uso
# -v | -q: ('-v' por defecto) definir cantidad dde informacion por consola
# -H:      Direccion IP del servidor
# -p:      Puerto del servidor
# -s:      Directorio encargado de guardar archivos

def main():
    global verbose
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    dir_path = os.path.dirname(__file__) + '/files'

    parser = argparse.ArgumentParser(description="Server capable of uploading/downloading files")

    # Se elige uno para la verbosidad de los mensajes por consola
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity",
                       action="store_true")
    group.add_argument("-q", "--quiet",
                       help="decrease output verbosity", action="store_true")

    # Especificaciones de conexion/guardado de archivo
    parser.add_argument("-H", "--host", help="service IP address", required=False, type=str)
    parser.add_argument("-p", "--port", help="service port number", required=False, type=int)
    parser.add_argument("-s", "--storage", help="storage dir path",
                        required=False, type=str)

    args = parser.parse_args()

    if args.quiet:
        verbose = False
    if args.host is not None:
        server_host = args.host
    if args.port is not None:
        server_port = args.port
    if args.storage is not None:
        dir_path = args.storage

    print("[DEBUG] args= ", [verbose, server_host, server_port, dir_path])

    listen(server_host, server_port, dir_path)


def listen(host_address: str, port: int, dir_path):
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind((host_address, port))
    print('[INFO] Server listo para recibir consultas')
    clients_pending_upload = {}

    while True:
        # TODO: un mensaje que corte ejecucion del servidor
        packet, client_address = server_socket.recvfrom(1024)
        
        decoded_packet = pickle.loads(packet)

        if decoded_packet.get_fin():
            clients_pending_upload.pop(client_address, None)
            print('[INFO] Conexion finalizada lado server')
            break

        thread = threading.Thread(target=handle_message, args=(decoded_packet, client_address, server_socket, dir_path, clients_pending_upload))
        thread.start()

    server_socket.close()


def handle_message(packet, client_address, server_socket, dir_path, clients_pending_upload):
    # TODO: el servidor puede recibir 2 tipos paquetes -> uno con data para el
    #       upload y otro de consulta para hacer un download

    print('[INFO] Conexion con ', client_address)

    if packet.get_is_download_query():
        seq_num = send_file(server_socket, client_address, packet, dir_path)
        end_pkt = Packet(seq_num + 1, True)
        buff = pickle.dumps(end_pkt)
        server_socket.sendto(buff, client_address)

    elif packet.get_is_upload_query():
        open(dir_path + '/' + packet.get_file_name(), "w").close()
        clients_pending_upload[client_address] = 1
        send_ack(client_address, server_socket, 0)
        print("sent ack to client")

    if client_address in clients_pending_upload and clients_pending_upload[client_address] != packet.get_seq_num():
        print(clients_pending_upload[client_address])
        print(packet.get_seq_num())
        clients_pending_upload[client_address] = packet.get_seq_num()
        receive_file(packet, client_address, server_socket, dir_path)


# devuelve el sequence number con el que termino de mandar el archivo
def send_file(server_socket, client_address, client_pkt: Packet, dir_path: str):
def send_file(server_socket, client_address, client_pkt: Packet, dir_path):
    print('[INFO] Descargando archivo...')
    seq_num = 1

    # mando ack
    ack = Packet(seq_num, False)
    buf = pickle.dumps(ack)
    server_socket.sendto(buf, client_address)

    print('[DEBUG] dir = ', dir_path + '/' + client_pkt.get_data())
    file = open(dir_path + '/' + client_pkt.get_data(), 'r')
    data = file.read()
    file.close()
    dwnl_pkt = Packet(seq_num + 1, False)
    dwnl_pkt.insert_data(data)
    dwnl_pkt.acknowledge(client_pkt.get_seq_num())
    buf = pickle.dumps(dwnl_pkt)
    server_socket.sendto(buf, client_address)

    return seq_num


def receive_file(packet, client_address, server_socket, dir_path):
    print('[INFO] Subiendo archivo...')

    data = packet.get_data()

    print(packet.get_file_name())

    file_path = dir_path + '/' + packet.get_file_name()
    print(file_path)

    with open(file_path, "ab") as file:
            file.write(data.encode())

    send_ack(client_address, server_socket, packet.get_seq_num())


def send_ack(client_address, server_socket, seq_num):
    ack_packet = Packet(0, False)
    ack_packet.acknowledge(seq_num)
    buf = pickle.dumps(ack_packet)
    server_socket.sendto(buf, client_address)


if __name__ == "__main__":
    main()
