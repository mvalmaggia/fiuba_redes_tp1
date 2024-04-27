import pickle
import sys
from socket import *
from lib.packet import Packet

# Por defecto
verbose = True

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
MAX_PACKET_SIZE = 1400 # MSS <= 1460


# Formato linea de comando:
# download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]
# -h:      (opcional) mostrar ayuda de uso
# -v | -q: (opcional/ '-v' por defecto) definir cantidad dde informacion por consola
# -H:      Direccion IP del servidor a conectarse
# -p:      Puerto del servidor
# -d:      Directorio a guardar el archivo bajado
# -n:      Nombre del archivo a bajar
# NOTA: SON TODAS ESTAS OPCIONES NO SON OBLIGATORIAS
def main():
    global verbose
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    file_path = ''
    file_name = ''
    [options, args] = parse_args()
    print('[DEBUG] args = ', args)
    print('[DEBUG] options = ', options)

    if options[0]:
        print_help()
        exit()
    if not options[1]:
        verbose = False
    if options[2]:
        server_host = args[0]
    if options[3]:
        server_port = int(args[1])
    if options[4]:
        file_path = args[2]
    if options[5]:
        file_name = args[3]

    rcv_file(server_host, server_port, file_path, file_name)


# Devuelve 2 listas:
# options: opciones de funcionamiento del programa (ej: -p)
# args: argumentos pasados por consola (ej: 8080)
def parse_args():
    # [-h, -v|-q, -H, -p, -d, -n]
    options = [False, True, False, False, False, False]
    # [ADDR, PORT, FILEPATH, FILENAME]
    args = ['', '', '', '']
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
        elif sys.argv[i] == '-d' or sys.argv[i] == '--dst':
            options[4] = True
            args[2] = sys.argv[i + 1]
        elif sys.argv[i] == '-n' or sys.argv[i] == '--name':
            options[5] = True
            args[3] = sys.argv[i + 1]

    return [options, args]


def print_help():
    print('usage: download [- h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]\n')
    print('< command description >\n')
    print('optional arguments:')
    print('     -h, --help      show this help message and exit')
    print('     -v, --verbose   increase output verbosity')
    print('     -q, --quiet     decrease output verbosity')
    print('     -H, --host      server IP address')
    print('     -p, --port      server port')
    print('     -d, --dst       destination file path')
    print('     -n, --name      file name')


def retrans_go_back_n():
    pass


def retrans_stop_n_wait():
    pass


def rcv_file(server_host: str, server_port: int, file_path: str, file_name: str):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.bind((server_host, server_port + 1)) # para prueba localhost
    packets = []
    seq_num = 1

    print('[DEBUG] file_path = ', file_path)
    print('[DEBUG] file_name = ', file_name)

    # Creo paquete de consulta para bajar archivos
    query_packet = Packet(seq_num, False, True)
    # Uso el modulo 'pickle' para poder guardar el paquete en bytes y asi poder mandarlo
    query_packet.insert_data(file_name)
    buffer = pickle.dumps(query_packet)
    client_socket.sendto(buffer, (server_host, server_port))

    while True:
        encoded_packet, server_address = client_socket.recvfrom(MAX_PACKET_SIZE)
        decoded_packet = pickle.loads(encoded_packet)

        print('[DEBUG] Paquete recibido: ')
        print('[DEBUG]   seq_num: ', decoded_packet.get_seq_num())
        print('[DEBUG]   ack: ', decoded_packet.get_ack())
        print('[DEBUG]   fin: ', decoded_packet.get_fin())

        if decoded_packet.get_fin():
            print('[INFO] Conexion finalizada lado cliente')
            break

        # TODO: revisar con checksum que el paquete esta intacto
        if decoded_packet.get_ack() != 0:
            packets.append(decoded_packet)
        # client_socket.sendto('ack', server_address)

    # TODO: una vez conseguido el paquete completo -> terminar comunicacion
    fin_pkt = Packet(seq_num + 1, True, False)
    buffer = pickle.dumps(fin_pkt)
    client_socket.sendto(buffer, (server_host, server_port))

    client_socket.close()
    rebuild_file(packets, file_path, file_name)


def rebuild_file(packets: [], file_path: str, file_name: str):
    print('[INFO] Paquete recibido: ', packets[0].get_data())
    dwld_file = open(file_path + file_name, 'w')
    for file_pkt in packets:
        dwld_file.write(file_pkt.get_data())
    dwld_file.close()


def send_ack():
    pass


main()
