import os
import pickle
import argparse
from socket import AF_INET, SOCK_DGRAM, socket
from lib.packet import Packet, QueryType
from lib.retransmit_strategy import RetransmitStrategyInterface, GoBackN

# Por defecto
verbose = True

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
MAX_PACKET_SIZE = 1400  # MSS <= 1460


# Formato linea de comando:
# download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]
# -h:      (opcional) mostrar ayuda de uso
# -v | -q: (opcional/ '-v' por defecto) definir cantidad dde informacion por consola
# -H:      Direccion IP del servidor a conectarse
# -p:      Puerto del servidor
# -d:      Directorio a guardar el archivo bajado
# -n:      Nombre del archivo a bajar
def main():
    global verbose
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    file_path = os.path.dirname(__file__) + '/data/downloads'

    # usamos una estrategia de retransmision hardcodeada
    strategy = GoBackN(3)

    parser = argparse.ArgumentParser(
        description="Download a specified file from the server")

    # Se elige uno para la verbosidad de los mensajes por consola
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity",
                       action="store_true")
    group.add_argument("-q", "--quiet",
                       help="decrease output verbosity", action="store_true")

    # Especificaciones de conexion/bajada de archivo
    parser.add_argument("-H", "--host", help="server IP address",
                        required=False, type=str)
    parser.add_argument("-p", "--port", help="server port number",
                        required=False, type=int)
    parser.add_argument("-d", "--dst", help="destination file path",
                        required=False, type=str)
    parser.add_argument("-n", "--file_name", help="file name", default='upload_test.txt',
                        required=True, type=str)

    args = parser.parse_args()

    if args.quiet:
        verbose = False
    if args.host is not None:
        server_host = args.host
    if args.port is not None:
        server_port = args.port
    if args.dst is not None:
        file_path = args.dst
    file_name = args.file_name

    print("[DEBUG] args= ", [verbose, server_host, server_port, file_path])

    rcv_file(server_host, server_port, file_path, file_name, strategy)


def retrans_go_back_n():
    pass


def retrans_stop_n_wait():
    pass


def rcv_file(server_host: str, server_port: int,
             file_path: str, file_name: str, strategy: RetransmitStrategyInterface):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    packets = []
    seq_num = 1

    print('[DEBUG] file_path = ', file_path)
    print('[DEBUG] file_name = ', file_name)

    # Creo paquete de consulta para bajar archivos
    query_packet = Packet(seq_num, False, QueryType.DOWNLOAD)

    # Serializamos el paquete y lo mandamos a servidor
    query_packet.insert_data(file_name)
    buffer = pickle.dumps(query_packet)
    client_socket.sendto(buffer, (server_host, server_port))

    packets = strategy.receive_packet(client_socket)

    # while True:
    #     encoded_packet, server_address = client_socket.recvfrom(
    #         MAX_PACKET_SIZE)
    #     decoded_packet = pickle.loads(encoded_packet)
    #
    #     print('[DEBUG] Paquete recibido: ')
    #     print('[DEBUG]   seq_num: ', decoded_packet.get_seq_num())
    #     print('[DEBUG]   ack: ', decoded_packet.get_ack())
    #     print('[DEBUG]   fin: ', decoded_packet.get_fin())
    #
    #     if decoded_packet.get_fin():
    #         print('[INFO] Conexion finalizada lado cliente')
    #         break
    #
    #     # TODO: revisar con checksum que el paquete esta intacto
    #     if decoded_packet.get_ack() != 0:
    #         packets.append(decoded_packet)
    #     # client_socket.sendto('ack', server_address)
    #
    # # TODO: una vez conseguido el paquete completo -> terminar comunicacion
    # fin_pkt = Packet(seq_num + 1, True)
    # buffer = pickle.dumps(fin_pkt)
    # client_socket.sendto(buffer, (server_host, server_port))

    client_socket.close()
    rebuild_file(packets, file_path, file_name)


def rebuild_file(packets: list, file_path: str, file_name: str):
    print('[INFO] Paquete recibido: ', packets[0].get_data())
    # TODO: faltaria ordenar los paquetes segun su sequence number
    dwld_file = open(file_path + '/' + file_name, 'w')
    for file_pkt in packets:
        dwld_file.write(file_pkt.get_data())
    dwld_file.close()


def send_ack():
    pass


if __name__ == "__main__":
    main()
