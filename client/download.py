import sys

VERBOSE = 0
QUIET = 1


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
    args = parse_args()
    if args[0] == '-h' or args[0] == '--help':
        print_help()


def parse_args():
    args = []
    for i in range(1, len(sys.argv)):
        args.append(sys.argv[i])

    return args


def print_help():
    print('usage: download[- h][- v | -q][- H ADDR] [- p PORT][- d FILEPATH] [- n FILENAME]\n')
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
