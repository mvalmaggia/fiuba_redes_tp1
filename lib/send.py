import time
import pickle
from packet import Packet
from ack_tracker import AckTracker


def send(server_socket, client_address: str, packet: Packet, seq_num: int, ack_tracker: AckTracker, timeout=0.1, attempts=5) -> bool:
    packet_bytes = pickle.dumps(packet)
    for _ in range(attempts):
        server_socket.sendto(packet_bytes, client_address)
        time.sleep(timeout)
        if ack_tracker.check_ack(client_address, seq_num):
            return True
    return False
