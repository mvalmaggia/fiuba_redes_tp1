import socket
import time

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        sock.sendto(b"Hola", (UDP_IP, UDP_PORT))
        time.sleep(1)


if __name__ == "__main__":
    main()