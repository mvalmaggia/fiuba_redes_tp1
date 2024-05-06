import pickle
from abc import ABC, abstractmethod
from socket import AF_INET, SOCK_DGRAM, socket
from packet import Packet
from timer import Timer

MAX_SEQ_NUM = 64


class RetransmitStrategyInterface(ABC):
    @abstractmethod
    def send_packets(self, sender_sock: socket, receiver_addr, file):
        pass

    @abstractmethod
    def receive_packet(self):
        pass


class StopNWait(RetransmitStrategyInterface):

    def send_packets(self, sender_sock: socket, receiver_addr, file):
        pass

    def receive_packet(self):
        pass


class GoBackN(RetransmitStrategyInterface):
    base_seq_num: int
    next_seq_num: int
    last_ack_pkt: int
    repeated_acks: int
    window: int

    def __init__(self, window_size: int):
        self.window = window_size
        self.repeated_acks = 0

    def send_packets(self, sender_sock: socket, receiver_addr, file):
        self.base_seq_num, self.next_seq_num = 1, 1
        packets = extract_packets_from(file)
        self.last_ack_pkt = 0

        timer = Timer()
        timeout = 5.0

        while True:
            if self.last_ack_pkt == packets.__sizeof__():
                break

            # evento: timeout
            if (timer.get_time() > timeout) or (self.repeated_acks >= 3):
                timer.reset()
                for pkt_idx in range(self.base_seq_num - 1, self.next_seq_num - 2):
                    retrans_pkt = packets[pkt_idx]
                    buf = pickle.dumps(retrans_pkt)
                    sender_sock.sendto(buf, receiver_addr)

            # deja de enviar paquetes cuando llega al fin de 'packets'
            if self.next_seq_num <= packets.__sizeof__():

                # evento: mandado de paquetes dentro de la ventana
                if self.next_seq_num < (self.base_seq_num + self.window):
                    pending_pkt = packets[self.next_seq_num - 1]
                    print("[DEBUG] pending_pkt= ", pending_pkt)
                    buf = pickle.dumps(pending_pkt)
                    sender_sock.sendto(buf, receiver_addr)

                    if self.base_seq_num == self.next_seq_num:
                        timer.start()
                    self.next_seq_num = self.next_seq_num + 1

            # evento: recibir ack
            ack_pkt = sender_sock.recvfrom(5000)
            if ack_pkt.get_ack() == self.last_ack_pkt:
                self.repeated_acks = self.repeated_acks + 1
            else:
                self.last_ack_pkt = ack_pkt.get_ack()
                self.repeated_acks = 0
                self.base_seq_num = ack_pkt.get_ack() + 1
                if self.base_seq_num == self.next_seq_num:
                    timer.stop()
                else:
                    timer.reset()

    def receive_packet(self):
        pass


def extract_packets_from(file):
    packets = []
    seq_num = 1
    end_while = False
    while not end_while:
        try:
            data = file.read(1024)
            pkt = Packet(seq_num, False)
            pkt.insert_data(data)
            packets.append(pkt)
            seq_num = seq_num + 1
        except IOError:
            end_while = True

    return packets
