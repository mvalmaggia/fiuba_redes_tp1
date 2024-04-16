import sys

# Por defecto
verbose = True


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
    print('[DEBUG] verbose = ', verbose)
    args = parse_args()
    print('[DEBUG] args = ', args)
    if args[0]:
        print_help()
        exit()
    elif not args[1]:
        verbose = False
        print('[DEBUG] verbose = ', verbose)


def parse_args():
    # [-h, -v|-q, -H, -p, -d, -n]
    args = [False, True, False, False, False, False]
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-h' or sys.argv[i] == '--help':
            args[0] = True
        elif sys.argv[i] == '-q' or sys.argv[i] == '--quiet':
            args[1] = False
        elif sys.argv[i] == '-H' or sys.argv[i] == '--host':
            args[2] = True
        elif sys.argv[i] == '-p' or sys.argv[i] == '--port':
            args[3] = True
        elif sys.argv[i] == '-d' or sys.argv[i] == '--dst':
            args[4] = True
        elif sys.argv[i] == '-n' or sys.argv[i] == '--name':
            args[5] = True

    return args


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
