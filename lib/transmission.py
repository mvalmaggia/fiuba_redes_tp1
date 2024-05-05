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

def send(server_socket, client_address: str, data, registry: SecNumberRegistry, timeout=0.1, attempts=5) -> bool:
    seq_num = registry.get_sec_num(client_address)
    packet = Packet(seq_num, False)
    packet.insert_data(data)
    encoded_packet = pickle.dumps(packet)
    for i in range(attempts):
        server_socket.sendto(encoded_packet, client_address)
        server_socket.settimeout(timeout)
        try:
            # ESTO ESTA MAL, TENGO QUE HACER POLLING DE MI ESTRUCTURA DE DATOS
            ack_packet, _ = server_socket.recvfrom(1024)
            decoded_packet = pickle.loads(ack_packet)
            if decoded_packet.get_ack() == seq_num + 1:
                registry.update_sec_num(client_address, seq_num + 1)
                return True
        except:
            continue
    return False

# def receive(server_socket, ack_tracker: SecNumberRegistry) -> Packet:
#     packet, sender_address = server_socket.recvfrom(1024)
#     decoded_packet: Packet = pickle.loads(packet)
#     if decoded_packet.ack:
#         ack_tracker.add_ack(sender_address, decoded_packet.seq_num)
#     ack_packet = pickle.dumps(Packet(decoded_packet.seq_num, False, ack=True))
#     server_socket.sendto(ack_packet, sender_address)
#     return decoded_packet
#

