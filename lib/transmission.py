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


def receive(server_socket, ack_tracker: SecNumberRegistry) -> Packet:
    packet, sender_address = server_socket.recvfrom(1024)
    decoded_packet: Packet = pickle.loads(packet)
    if decoded_packet.ack:
        ack_tracker.put(sender_address, decoded_packet.seq_num)
        return decoded_packet
    ack_packet = Packet(decoded_packet.seq_num + 1, ack=True)
    send(server_socket, sender_address, ack_packet, ack_tracker)
    return decoded_packet


