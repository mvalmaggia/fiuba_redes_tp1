import time
import pickle
from packet import Packet


def send(server_socket, client_address, data, seq_num, ack_tracker, timeout=2):
    packet = pickle.dumps(Packet(seq_num, False, data=data))
    while not ack_tracker.check_ack(client_address, seq_num):
        server_socket.sendto(packet, client_address)
        time.sleep(timeout)

