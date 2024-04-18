# import random


class Packet:
    seq_num: int
    checksum: int
    ack: int
    data: str

    def __init__(self, seq_num):
        self.seq_num = seq_num
        self.data = ''

    def acknowledge(self, prev_pack_seq_num: int):
        self.ack = prev_pack_seq_num + 1

    def insert_data(self, data: str):
        if data.__sizeof__() < 1400:
            self.data = data

    def generate_checksum(self):
        # TODO: revisar como hacer el checksum en UDP
        self.checksum = hash(self)
