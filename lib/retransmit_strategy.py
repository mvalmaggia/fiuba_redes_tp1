import pickle
import sys
from abc import ABC, abstractmethod
from socket import AF_INET, SOCK_DGRAM, socket
from lib.packet import Packet
from lib.timer import Timer

MAX_SEQ_NUM = 64


class RetransmitStrategyInterface(ABC):
    @abstractmethod
    def send_packets(self, sender_sock: socket, receiver_addr, file_path: str):
        pass

    @abstractmethod
    def receive_packet(self, recv_sock: socket):
        pass


class StopNWait(RetransmitStrategyInterface):

    def send_packets(self, sender_sock: socket, receiver_addr, file_path: str):
        pass

    def receive_packet(self, recv_sock: socket):
        pass


class GoBackN(RetransmitStrategyInterface):
    base_seq_num: int
    next_seq_num: int
    expected_seq_num: int
    last_ack_pkt: int
    repeated_acks: int
    window: int

    def __init__(self, window_size: int):
        self.window = window_size
        self.repeated_acks = 0

    def send_packets(self, sender_sock: socket, receiver_addr, file_path: str):
        self.base_seq_num = 1
        self.next_seq_num = 1
        packets = extract_packets_from(file_path)
        print('[DEBUG] packets = ', packets)
        print('[DEBUG] len(packets) = ', len(packets))
        self.last_ack_pkt = 0

        timer = Timer()
        timeout = 5.0

        while True:
            if self.last_ack_pkt == len(packets):
                print('[DEBUG] Paquete enviado')
                break

            print('[DEBUG] next_seq_num actual = ', self.next_seq_num)
            print('[DEBUG] base_seq_num actual = ', self.base_seq_num)
            print('[DEBUG] last_ack_pkt actual = ', self.last_ack_pkt)

            # evento: timeout
            if (timer.get_time() > timeout) or (self.repeated_acks >= 3):
                print('[DEBUG] Hubo un timeout!')
                print('[DEBUG] repeated_acks = ', self.repeated_acks)
                print('[DEBUG] Tiempo transcurrido = ', timer.get_time())
                timer.reset()
                for pkt_idx in range(self.base_seq_num - 1, self.next_seq_num - 2):
                    retrans_pkt = packets[pkt_idx]
                    buf = pickle.dumps(retrans_pkt)
                    sender_sock.sendto(buf, receiver_addr)

            # deja de enviar paquetes cuando llega al fin de 'packets'
            if self.next_seq_num <= len(packets):

                # evento: mandado de paquetes dentro de la ventana
                if self.next_seq_num < (self.base_seq_num + self.window):
                    pending_pkt = packets[self.next_seq_num - 1]
                    print("[DEBUG] pending_pkt= ", pending_pkt)
                    buf = pickle.dumps(pending_pkt)
                    sender_sock.sendto(buf, receiver_addr)

                    if self.base_seq_num == self.next_seq_num:
                        timer.start()
                    self.next_seq_num += 1

            # evento: recibir ack
            ack_pkt, receiver_addr = sender_sock.recvfrom(5000)
            decoded_ack_pkt = pickle.loads(ack_pkt)
            if decoded_ack_pkt.get_seq_num() == self.last_ack_pkt:
                print(f'[DEBUG] El paquete numero {decoded_ack_pkt.get_seq_num()} '
                        f'todavia no se recibio')
                self.repeated_acks += 1
            else:
                print(f'[DEBUG] El paquete numero {decoded_ack_pkt.get_seq_num()} '
                    f'fue recibido exitosamente')
                self.last_ack_pkt = decoded_ack_pkt.get_seq_num()
                self.repeated_acks = 0
                self.base_seq_num = decoded_ack_pkt.get_seq_num() + 1
                if self.base_seq_num == self.next_seq_num:
                    timer.stop()
                else:
                    timer.reset()

        fin_pkt = Packet(self.next_seq_num, True)
        buffer = pickle.dumps(fin_pkt)
        sender_sock.sendto(buffer, receiver_addr)

        return self.next_seq_num

    def receive_packet(self, recv_sock: socket):
        self.expected_seq_num = 1
        pkts = []

        while True:
            recv_pkt, sender_addr = recv_sock.recvfrom(5000)
            decoded_recv_pkt = pickle.loads(recv_pkt)
            print('[DEBUG] paquete recibido = ', decoded_recv_pkt)
            print('[DEBUG] tamaño del paquete = ', sys.getsizeof(decoded_recv_pkt) +
                  sys.getsizeof(decoded_recv_pkt.get_data()))
            print('[DEBUG] tamaño data del paquete = ', sys.getsizeof(decoded_recv_pkt.get_data()))
            print('[DEBUG] tiene fin? = ', decoded_recv_pkt.get_fin())
            if decoded_recv_pkt.get_fin():
                break

            # evento: paquete se recibe exitosamente
            elif decoded_recv_pkt.get_seq_num() == self.expected_seq_num:
                pkts.append(decoded_recv_pkt)
                ack_pkt = Packet(self.expected_seq_num, False)
                print('[DEBUG] enviando ack = ', ack_pkt)
                print('[DEBUG] pkts = ', pkts)
                buf = pickle.dumps(ack_pkt)
                recv_sock.sendto(buf, sender_addr)
                self.expected_seq_num += 1

            # evento: no recibio paquete -> mandar ack de ultimo paquete recibido
            else:
                print('[DEBUG] Se solicita reenvio de = ', decoded_recv_pkt.get_seq_num())
                ack_pkt = Packet(self.expected_seq_num, False)
                buf = pickle.dumps(ack_pkt)
                recv_sock.sendto(buf, sender_addr)

        # manda fin de comunicacion
        fin_pkt = Packet(self.expected_seq_num, True)
        buf = pickle.dumps(fin_pkt)
        recv_sock.sendto(buf, sender_addr)

        return pkts


def extract_packets_from(file_path: str):
    packets = []
    seq_num = 1

    file = open(file_path, 'r')

    while True:
        data = file.read(1024)
        if not data:
            break
        print('[DEBUG] data read = ', data)
        pkt = Packet(seq_num, False)
        pkt.insert_data(data)
        packets.append(pkt)
        seq_num = seq_num + 1

    file.close()

    return packets
