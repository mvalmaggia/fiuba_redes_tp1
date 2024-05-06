import pickle
from socket import AF_INET, SOCK_DGRAM, socket
import threading
import argparse
from lib.packet import Packet
import os
from lib.retransmit_strategy import RetransmitStrategyInterface, GoBackN

# Por defecto
verbose = True

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
BLOCK_SIZE = 1024 * 4

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

    # usamos una estrategia de retransmision hardcodeada
    strategy = GoBackN(3)

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

    listen(server_host, server_port, dir_path, strategy)


def listen(host_address: str, port: int, dir_path, strategy: RetransmitStrategyInterface):
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind((host_address, port))
    print('[INFO] Server listo para recibir consultas')
    clients_pending_upload = {}

    while True:
        data, client_address = server_socket.recvfrom(BLOCK_SIZE)
        # Deserializo el Packet
        decoded_packet = pickle.loads(data)

        if decoded_packet.get_fin():
            clients_pending_upload.pop(client_address, None)
            print('[INFO] Conexion finalizada lado server')
            break

        thread = threading.Thread(target=handle_message,
                                  args=(decoded_packet,
                                        client_address,
                                        server_socket,
                                        dir_path,
                                        clients_pending_upload,
                                        strategy))
        thread.start()

    server_socket.close()


def handle_message(packet, client_address, server_socket, dir_path,
                   clients_pending_upload, strategy: RetransmitStrategyInterface):
    # TODO: el servidor puede recibir 2 tipos paquetes -> uno con data para el
    #       upload y otro de consulta para hacer un download

    print('[INFO] Conexion con ', client_address)

    if packet.get_is_download_query():
        seq_num = send_file(server_socket, client_address, packet, dir_path, strategy)
        end_pkt = Packet(seq_num + 1, True)
        buff = pickle.dumps(end_pkt)
        server_socket.sendto(buff, client_address)

    elif packet.get_is_upload_query():
        open(dir_path + '/' + packet.get_file_name(), "w").close()
        clients_pending_upload[client_address] = 1
        send_ack(client_address, server_socket, 0)
        print("sent ack to client to start upload")

    elif (client_address in clients_pending_upload and
            clients_pending_upload[client_address] != packet.get_seq_num()):
        print(clients_pending_upload[client_address])
        print(packet.get_seq_num())
        clients_pending_upload[client_address] = packet.get_seq_num()
        receive_file(packet, client_address, server_socket, dir_path)


# devuelve el sequence number con el que termino de mandar el archivo
def send_file(server_socket, client_address, client_pkt: Packet, 
              dir_path: str, strategy: RetransmitStrategyInterface):
    print('[INFO] Descargando archivo...')
    print('[DEBUG] dir = ', dir_path + '/' + client_pkt.get_data())

    file_path = dir_path + '/' + client_pkt.get_data()
    seq_num = strategy.send_packets(server_socket, client_address, file_path)

    return seq_num


def receive_file(packet, client_address, server_socket, dir_path):
    print('[INFO] Subiendo archivo...')

    data = packet.get_data()

    print(packet.get_file_name())

    file_path = dir_path + '/' + packet.get_file_name()
    print(file_path)

    # wb porque si existe el archivo debo sobreescribirlo
    with open(file_path, "wb") as file:
        print(f"Se va a escribir en {file_path} el siguiente "
              f"contenido: {data}")
        file.write(data.encode())

    send_ack(client_address, server_socket, packet.get_seq_num())


def send_ack(client_address, server_socket, seq_num):
    ack_packet = Packet(0, False)
    ack_packet.acknowledge(seq_num)
    buf = pickle.dumps(ack_packet)
    server_socket.sendto(buf, client_address)


if __name__ == "__main__":
    main()
