import argparse
from upload import upload


# usage: upload [-h] [-v | -q] [-H ADDR] [-p PORT]
# [-s FILEPATH] [-n FILENAME]
# usage: download [-h] [-v | -q] [-H ADDR] [-p PORT]
# [-d FILEPATH] [-n FILENAME]
def main():
    parser = argparse.ArgumentParser(
        description="Upload or download files from a server")
    # El comando es requerido
    parser.add_argument("command", help="Command to execute",
                        choices=["upload", "download"], type=str)
    # Se elige una verbosidad para los logs
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="Increase output verbosity",
                       action="store_true", default=True)
    group.add_argument("-q", "--quiet", help="Decrease output verbosity",
                       action="store_true")
    # Se debe especificar obligatoriamente: host, port, file_path y file_name
    parser.add_argument("-H", "--host", help="Host address", required=True,
                        type=str)
    parser.add_argument("-p", "--port", help="Port number", required=True,
                        type=int)
    parser.add_argument("-s", "--file_path", help="File path", required=True,
                        type=str)
    parser.add_argument("-n", "--file_name", help="File name", required=True,
                        type=str)

    args = parser.parse_args()
    if args.command == "upload":
        print('executing upload')
        upload(args.host, args.port, args.file_path, args.file_name)
    elif args.command == "download":
        print('executing download')
        # download(args.host, args.port, args.file_path, args.file_name)
    else:
        print("Invalid command")
        parser.print_help()


if __name__ == "__main__":
    main()
