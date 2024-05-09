import logging
import os
import pickle
import argparse
from socket import AF_INET, SOCK_DGRAM, socket
from lib.packet import Packet, QueryType
from upload import check_ack_client
from lib.transmission import send_stop_n_wait, receive


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_PACKET_SIZE = 1400  # MSS <= 1460

log = logging.getLogger(__name__)


# Formato linea de comando:
# download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]
# -h:      (opcional) mostrar ayuda de uso
# -v | -q: (opcional/ '-v' por defecto) definir cantidad
# de informacion por consola
# -H:      Direccion IP del servidor a conectarse
# -p:      Puerto del servidor
# -d:      Directorio a guardar el archivo bajado
# -n:      Nombre del archivo a bajar
def main():
    verbose = True
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    file_path = (
        os.path.dirname(__file__) + "/data/downloads/downloaded_file.txt"
    )

    parser = argparse.ArgumentParser(
        description="Download a specified file from the server"
    )

    # Se elige uno para la verbosidad de los mensajes por consola
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true",
    )
    group.add_argument(
        "-q", "--quiet", help="decrease output verbosity", action="store_true"
    )

    # Especificaciones de conexion/bajada de archivo
    parser.add_argument(
        "-H", "--host", help="server IP address", required=False, type=str
    )
    parser.add_argument(
        "-p", "--port", help="server port number", required=False, type=int
    )
    parser.add_argument("-d", "--dst", help="destination file path", type=str)
    parser.add_argument(
        "-n", "--file_name", help="file name", required=True, type=str
    )

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            format="%(levelname)s: %(message)s", level="DEBUG"
        )
        log.debug("Verbose output.")
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
        verbose = False
    if args.quiet:
        verbose = False
    if args.host is not None:
        server_host = args.host
    if args.port is not None:
        server_port = args.port
    if args.dst is not None:
        file_path = args.dst
    file_name = args.file_name

    log.debug("args= %s", [verbose, server_host, server_port, file_path])

    rcv_file(server_host, server_port, file_path, file_name)


def rcv_file(
    server_host: str, server_port: int, file_path: str, file_name: str
):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.setblocking(True)
    server_address = (server_host, server_port)
    seq_num_client = 1
    seq_num_expected = 1
    packets = {}

    # reemplazo la lambda por Flake8

    def function_check_ack(sec_num_to_check):
        return check_ack_client(client_socket, sec_num_to_check)

    log.debug("file_path = %s", file_path)
    log.debug("file_name = %s", file_name)
    # Query
    query_packet = Packet(
        seq_num_client, False, QueryType.DOWNLOAD, file_name=file_name
    )
    send_stop_n_wait(
        client_socket, server_address, query_packet, function_check_ack
    )

    log.info("Comenzando descarga...")

    while True:
        decoded_packet, _ = receive(client_socket)
        log.debug(f"Paquete recibido: {decoded_packet}")
        if decoded_packet.get_seq_num() != seq_num_expected:
            ack_packet = Packet(seq_num_expected, ack=True)
            send_stop_n_wait(
                client_socket, server_address, ack_packet, function_check_ack
            )
            continue
        seq_num_expected += 1
        if decoded_packet.get_fin():
            ack_packet = Packet(decoded_packet.get_seq_num() + 1, ack=True)
            send_stop_n_wait(
                client_socket, server_address, ack_packet, function_check_ack
            )
            break
        if (
            not decoded_packet.get_ack()
            and decoded_packet.get_seq_num() not in packets
        ):
            packets[decoded_packet.get_seq_num()] = decoded_packet
            ack_packet = Packet(decoded_packet.get_seq_num() + 1, ack=True)
            send_stop_n_wait(
                client_socket, server_address, ack_packet, function_check_ack
            )

    fin_pkt = Packet(seq_num_client + 1, True)
    buffer = pickle.dumps(fin_pkt)
    client_socket.sendto(buffer, (server_host, server_port))

    ordered_packets = [packets[seq] for seq in sorted(packets)]
    rebuild_file(ordered_packets, file_path)

    log.info("Archivo descargado exitosamente")

    client_socket.close()


def rebuild_file(packets: list, file_path: str):
    log.debug(f"Guardando {len(packets)} paquetes recibidos en {file_path}")
    dwld_file = open(file_path, "wb")
    for file_pkt in packets:
        dwld_file.write(file_pkt.get_data())
    dwld_file.close()


if __name__ == "__main__":
    main()
