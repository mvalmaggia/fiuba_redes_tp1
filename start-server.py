import pickle
from socket import AF_INET, SOCK_DGRAM, socket
import threading
import argparse
from lib.packet import Packet
import os

from lib.server import Server

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
    dir_path = os.path.dirname(__file__) + '/data/server_storage'

    parser = argparse.ArgumentParser(
        description="Server capable of uploading/downloading uploads")

    # Se elige uno para la verbosidad de los mensajes por consola
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity",
                       action="store_true")
    group.add_argument("-q", "--quiet",
                       help="decrease output verbosity", action="store_true")

    # Especificaciones de conexion/guardado de archivo
    parser.add_argument("-H", "--host", help="service IP address",
                        required=False, type=str)
    parser.add_argument("-p", "--port", help="service port number",
                        required=False, type=int)
    parser.add_argument("-s", "--storage", help="server_storage dir path",
                        default=dir_path,
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
        # Si dir_path especificado por argumento no existe, lo crea
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    print("[DEBUG] args= ", [verbose, server_host, server_port, dir_path])
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind((server_host, server_port))
    server = Server(server_socket, dir_path)
    server.listen()


if __name__ == "__main__":
    main()
