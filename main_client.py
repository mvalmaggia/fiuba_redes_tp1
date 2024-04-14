import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b"Hola", (UDP_IP, UDP_PORT))


if __name__ == "__main__":
    main()