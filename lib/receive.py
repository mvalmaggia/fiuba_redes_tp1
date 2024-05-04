import pickle
from packet import Packet


def receive(server_socket, ack_tracker):
    while True:
        packet, client_address = server_socket.recvfrom(1024)
        decoded_packet = pickle.loads(packet)
        # Aquí asumimos que Packet tiene un método para validar el checksum.
        if decoded_packet.validate_checksum():
            ack_tracker.add_ack(client_address, decoded_packet.seq_num)
            ack_packet = pickle.dumps(Packet(decoded_packet.seq_num, False, ack=True))
            server_socket.sendto(ack_packet, client_address)

