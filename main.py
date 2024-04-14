import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(1024)
        print("received message: ", data)
        print("from: ", addr)
        sock.sendto(data, addr)


if __name__ == "__main__":
    main()