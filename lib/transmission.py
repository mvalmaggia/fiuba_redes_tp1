import time
import pickle
from typing import Tuple
import zlib

from lib.packet import Packet


def send_stop_n_wait(
    server_socket,
    client_address,
    packet: Packet,
    check_ack,
    timeout=0.1,
    attempts=50,
) -> bool:
    if packet.ack:
        server_socket.sendto(pickle.dumps(packet), client_address)
        print(f"Enviando ack {packet}")
        return True

    for i in range(attempts):
        server_socket.sendto(pickle.dumps(packet), client_address)
        print(f"Paquete enviado: {packet}")
        time.sleep(timeout)
        if check_ack(packet.seq_num):
            print(f"Recibido ack para el paquete {packet.seq_num}")
            return True
        print(
            f"Reintentando enviar paquete {packet.seq_num}, "
            f"intento {i + 1}/{attempts}"
        )
    raise TimeoutError("No se recibio ack para el paquete")


def receive(server_socket) -> Tuple[Packet, str]:
    packet, sender_address = server_socket.recvfrom(4096)
    decoded_packet: Packet = pickle.loads(packet)
    # print(f"Paquete recibido: {decoded_packet}")

    # Validar que todos los atributos necesarios están presentes
    required_attributes = [
        "seq_num",
        "checksum",
        "ack",
        "fin",
        "query_type",
        "data",
    ]
    for attr in required_attributes:
        if not hasattr(decoded_packet, attr):
            print(f"El paquete recibido no tiene el atributo {attr}")
            raise AttributeError(
                f"El paquete recibido no tiene el atributo {attr}"
            )

    # Se recalcula el checksum de la data recibida
    calculated_checksum = zlib.crc32(decoded_packet.data) & 0xFFFFFFFF

    # Chequeo de integridad de data recibida
    if calculated_checksum != decoded_packet.checksum:
        print("[ERROR] Checksum erroneo, data podria haber sido corrompida.")
        raise ValueError("Checksum does not match, data may be corrupted.")

    return decoded_packet, sender_address


def send_file_sw(
    server_socket,
    client_address,
    file_path,
    start_sec_num,
    check_ack,
    timeout=0.1,
    attempts=50,
):
    print(f"Enviando archivo {file_path}")
    # Primero se abre el archivo y se va leyendo de a pedazos de 1024
    # bytes para enviarlos al cliente en paquetes
    with open(file_path, "rb") as file:
        file_content = file.read(2048)
        # print(f"Enviando paquete {sec_num} con {len(file_content)} bytes")
        while file_content:
            data_packet = Packet(start_sec_num, False)
            data_packet.insert_data(file_content)
            send_stop_n_wait(
                server_socket,
                client_address,
                data_packet,
                check_ack,
                timeout,
                attempts,
            )
            file_content = file.read(2048)
            start_sec_num += 1

        # Se envia un paquete con el fin de la transmision
        fin_packet = Packet(start_sec_num, True)
        send_stop_n_wait(
            server_socket,
            client_address,
            fin_packet,
            check_ack,
            timeout,
            attempts,
        )
