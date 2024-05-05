import time
import pickle
from packet import Packet
from sec_num_registry import SecNumberRegistry


# Falta:
# Trackear los sequence number.
# Tener en cuenta que tanto el cliente y el servidor tienen distintos sequence numbers, independientes entre si.
# Que por convencion el sequence number que se envia en el ack es el sequence number del paquete recibido + 1.
# Que es necesario mantener registro de los sequence numbers pues estos son la cantidad de bytes enviados.
# Ademas es necesario mantener este registro para poder enviar el ack correspondiente y poder ordenar los paquetes.
# Quien envia paquetes es el que debe mantener el registro del ultimo sequence number enviado.
def send(server_socket, client_address: str, packet: Packet, registry: SecNumberRegistry, timeout=0.1, attempts=5) -> bool:
    server_socket.sendto(pickle.dumps(packet), client_address)
    if packet.ack:
        return True

    for _ in range(attempts):
        if registry.has(client_address, packet.seq_num + 1):
            return True
        time.sleep(timeout)
        server_socket.sendto(pickle.dumps(packet), client_address)
    return False


def receive(server_socket, ack_tracker: SecNumberRegistry) -> (Packet, str):
    packet, sender_address = server_socket.recvfrom(1024)
    decoded_packet: Packet = pickle.loads(packet)
    if decoded_packet.ack:
        ack_tracker.put(sender_address, decoded_packet.seq_num)
        return decoded_packet, sender_address
    return decoded_packet, sender_address


def send_file(server_socket, client_address, file_path, registry: SecNumberRegistry):
    # Primero se abre el archivo y se va leyendo de a pedazos de 1024 bytes para enviarlos al cliente en paquetes
    sec_num = registry.get(client_address)
    with open(file_path, "r") as file:
        file_content = file.read(1024)
        while file_content:
            sec_num += len(file_content)
            data_packet = Packet(sec_num, False)
            data_packet.insert_data(file_content)
            send(server_socket, client_address, data_packet, registry)
            file_content = file.read(1024)
        # Se envia un paquete con el fin de la transmision
        fin_packet = Packet(sec_num + 1, True)
        send(server_socket, client_address, fin_packet, registry)


def receive_file(packet: Packet, dir_path):
    data = packet.get_data()
    file_path = dir_path + '/' + packet.get_file_name()
    with open(file_path, "ab") as file:
        file.write(data.encode())
