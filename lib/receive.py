import pickle
from packet import Packet
from ack_tracker import AckTracker
from packet import Packet


# Falta:
# Trackear los sequence number.
# Tener en cuenta que tanto el cliente y el servidor tienen distintos sequence numbers, independientes entre si.
# Que por convencion el sequence number que se envia en el ack es el sequence number del paquete recibido + 1.
# Que es necesario mantener registro de los sequence numbers pues estos son la cantidad de bytes enviados.
# Ademas es necesario mantener este registro para poder enviar el ack correspondiente y poder ordenar los paquetes.

def receive(server_socket, ack_tracker: AckTracker) -> Packet:
    packet, sender_address = server_socket.recvfrom(1024)
    decoded_packet: Packet = pickle.loads(packet)
    if decoded_packet.ack:
        ack_tracker.add_ack(sender_address, decoded_packet.seq_num)
    ack_packet = pickle.dumps(Packet(decoded_packet.seq_num, False, ack=True))
    server_socket.sendto(ack_packet, sender_address)
    return decoded_packet


