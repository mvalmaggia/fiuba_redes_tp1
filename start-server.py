import pickle
import sys
import threading
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
# NOTA: TODAS ESTAS OPCIONES NO SON OBLIGATORIAS

def main():
    global verbose
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    dir_path = os.path.dirname(__file__) + '/files'
    [options, args] = parse_args()
    print('[DEBUG] args = ', args)
    print('[DEBUG] options = ', options)

    if options[0]:
        print_help()
        exit()
    elif not options[1]:
        verbose = False
    elif options[2]:
        server_host = args[0]
    elif options[3]:
        server_port = int(args[1])
    elif options[4]:
        dir_path = args[2]

    listen(server_host, server_port, dir_path)


# Devuelve 2 listas:
# options: opciones de funcionamiento del programa (ej: -p)
# args: argumentos pasados por consola (ej: 8080)
def parse_args():
    # [-h, -v|-q, -H, -p, -s]
    options = [False, True, False, False, False]
    # [ADDR, PORT, DIRPATH]
    args = ['', '', '']
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-h' or sys.argv[i] == '--help':
            options[0] = True
        elif sys.argv[i] == '-q' or sys.argv[i] == '--quiet':
            options[1] = False
        elif sys.argv[i] == '-H' or sys.argv[i] == '--host':
            options[2] = True
            args[0] = sys.argv[i + 1]
        elif sys.argv[i] == '-p' or sys.argv[i] == '--port':
            options[3] = True
            args[1] = sys.argv[i + 1]
        elif sys.argv[i] == '-s' or sys.argv[i] == '--storage':
            options[4] = True
            args[2] = sys.argv[i + 1]

    return [options, args]


def print_help():
    print('usage: download [- h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]\n')
    print('< command description >\n')
    print('optional arguments:')
    print('     -h, --help      show this help message and exit')
    print('     -v, --verbose   increase output verbosity')
    print('     -q, --quiet     decrease output verbosity')
    print('     -H, --host      server IP address')
    print('     -p, --port      server port')
    print('     -s, --storage   storage dir path')


def listen(host_address: str, port: int, dir_path):
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind((host_address, port))
    print('[INFO] Server listo para recibir consultas')
    seq_num = 1

    while True:
        # TODO: cada conexion hecha se debe guardar en un hilo
        packet, client_address = server_socket.recvfrom(1024)
        
        decoded_packet = pickle.loads(packet)

        if decoded_packet.get_fin():
            print('[INFO] Conexion finalizada lado server')
            #ver como hacer esto

        thread = threading.Thread(target=handle_message, args=(decoded_packet, client_address, server_socket, dir_path))
        thread.start()

    server_socket.close()


def handle_message(packet, client_address, server_socket, dir_path):
    # TODO: el servidor puede recibir 2 tipos paquetes -> uno con data para el
    #       upload y otro de consulta para hacer un download

    print('[INFO] Conexion con ', client_address)

    if packet.get_is_download_query():
        seq_num = send_file(server_socket, client_address, packet, dir_path)
        end_pkt = Packet(seq_num + 1, True)
        buff = pickle.dumps(end_pkt)
        server_socket.sendto(buff, client_address)

        # TODO: aca trabajar el tema de upload
    elif packet.get_is_upload_query():
        upload_file()

# devuelve el sequence number con el que termino de mandar el archivo
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


def upload_file():
    pass


main()
