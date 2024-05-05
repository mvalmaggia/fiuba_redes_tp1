from abc import ABC, abstractmethod


class RetransmitStrategyInterface(ABC):
    @abstractmethod
    def send_packets(self):
        pass

    @abstractmethod
    def receive_packet(self):
        pass


class StopNWait(RetransmitStrategyInterface):

    def send_packets(self):
        pass

    def receive_packet(self):
        pass


class GoBackN(RetransmitStrategyInterface):
    base_seq_num: int
    next_seq_num: int
    last_ack_pkt: int
    repeated_acks: int
    window: int  # el timer

    def __init__(self, window_size: int):
        self.window = window_size
        self.repeated_acks = 0

    def send_packets(self):
        pass

    def receive_packet(self):
        pass
