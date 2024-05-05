import time
import pickle
from packet import Packet
from sec_num_registry import SecNumberRegistry


def send(server_socket, client_address, packet: Packet, check_ack, timeout=0.1, attempts=5) -> bool:
    server_socket.sendto(pickle.dumps(packet), client_address)
    if packet.ack:
        return True

    for _ in range(attempts):
        if check_ack(packet.seq_num):
            return True
        time.sleep(timeout)
        server_socket.sendto(pickle.dumps(packet), client_address)
    return False


def receive(server_socket) -> (Packet, str):
    packet, sender_address = server_socket.recvfrom(1024)
    decoded_packet: Packet = pickle.loads(packet)
    return decoded_packet, sender_address


def send_file(server_socket, client_address, file_path, sec_num, check_ack, timeout=0.1, attempts=5):
    # Primero se abre el archivo y se va leyendo de a pedazos de 1024 bytes para enviarlos al cliente en paquetes
    with open(file_path, "r") as file:
        file_content = file.read(1024)
        while file_content:
            sec_num += len(file_content)
            data_packet = Packet(sec_num, False)
            data_packet.insert_data(file_content)
            send(server_socket, client_address, data_packet, check_ack, timeout, attempts)
            file_content = file.read(1024)
        # Se envia un paquete con el fin de la transmision
        fin_packet = Packet(sec_num + 1, True)
        send(server_socket, client_address, fin_packet, check_ack)

