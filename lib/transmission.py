import time
import pickle
from lib.packet import Packet
from lib.sec_num_registry import SecNumberRegistry
from lib.window import Window


def send_stop_n_wait(server_socket, client_address, packet: Packet, check_ack, timeout=0.1, attempts=50) -> bool:
    if packet.ack:
        server_socket.sendto(pickle.dumps(packet), client_address)
        print(f"Enviando ack {packet}")
        return True

    for i in range(attempts):
        print(f"Enviando paquete {packet.seq_num}")
        server_socket.sendto(pickle.dumps(packet), client_address)
        # print(f"Paquete enviado: {packet}")
        time.sleep(timeout)
        if check_ack(packet.seq_num):
            print(f"Recibido ack para el paquete {packet.seq_num}")
            return True
        print(f"Reintentando enviar paquete {packet.seq_num}, intento {i + 1}/{attempts}")
    raise TimeoutError("No se recibio ack para el paquete")


def receive(server_socket) -> (Packet, str):
    packet, sender_address = server_socket.recvfrom(4096)
    decoded_packet: Packet = pickle.loads(packet)
    return decoded_packet, sender_address


def send_file(server_socket, client_address, file_path, start_sec_num, check_ack, timeout=1, attempts=5):
    print(f"Enviando archivo {file_path}")
    # Primero se abre el archivo y se va leyendo de a pedazos de 1024 bytes para enviarlos al cliente en paquetes
    with open(file_path, "rb") as file:
        file_content = file.read(2048)
        # print(f"Enviando paquete {sec_num} con {len(file_content)} bytes")
        while file_content:
            data_packet = Packet(start_sec_num, False)
            data_packet.insert_data(file_content)
            send_stop_n_wait(server_socket, client_address, data_packet, check_ack, timeout, attempts)
            file_content = file.read(2048)
            start_sec_num += 1
        # Se envia un paquete con el fin de la transmision
        fin_packet = Packet(start_sec_num, True)
        send_stop_n_wait(server_socket, client_address, fin_packet, check_ack, timeout, attempts)


# Algoritmo de retransmision Go-Back-N
def handle_acks_and_retransmissions(server_socket, window: Window, client_address, ack_registry: SecNumberRegistry, timeout=0.2):
    while True:
        ack_registry.wait_for_new_ack(client_address, timeout)  # Espera un nuevo ACK o timeout
        last_ack = ack_registry.get_last_ack(client_address)
        window.remove_confirmed(last_ack)
        unacked_packets = window.get_unacked_packets()
        for packet in unacked_packets:
            server_socket.sendto(pickle.dumps(packet), client_address)
            print(f"Reintentando enviar paquete {packet.seq_num}")


def send_go_back_n(server_socket, client_address, packet: Packet, window: Window):
    while not window.add_packet(packet):
        print("La ventana está llena, esperando espacio...")
        window.wait_for_space()

    server_socket.sendto(pickle.dumps(packet), client_address)
    print(f"Paquete enviado: {packet.seq_num}")