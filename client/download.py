import sys

# Por defecto
verbose = True

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000


# Formato linea de comando:
# download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]
# -h:      (opcional) mostrar ayuda de uso
# -v | -q: (opcional/ '-v' por defecto) definir cantidad dde informacion por consola
# -H:      Direccion IP del servidor a conectarse
# -p:      Puerto del servidor
# -d:      Directorio a guardar el archivo bajado
# -n:      Nombre del archivo a bajar
# NOTA: SON TODAS OPCIONALES ESTAS OPCIONES
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
    elif not options[1]:
        verbose = False
    elif options[2]:
        server_host = args[0]
    elif options[3]:
        server_port = args[1]
    elif options[4]:
        file_path = args[2]
    elif options[5]:
        file_name = args[3]


# Devuelve 2 listas:
# options: opciones de funcionamiento del programa (ej: -p)
# args: argumentos pasados por consola (ej: 8080)
def parse_args():
    # [-h, -v|-q, -H, -p, -d, -n]
    options = [False, True, False, False, False, False]
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
    print('usage: download[- h][-v | -q][-H ADDR] [-p PORT][-d FILEPATH] [-n FILENAME]\n')
    print('< command description >\n')
    print('optional arguments:')
    print('     -h, --help      show this help message and exit')
    print('     -v, --verbose   increase output verbosity')
    print('     -q, --quiet     decrease output verbosity')
    print('     -H, --host      server IP address')
    print('     -p, --port      server port')
    print('     -d, --dst       destination file path')
    print('     -n, --name      file name')


main()
