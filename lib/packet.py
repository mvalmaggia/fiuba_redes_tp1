# import random

MAX_DATA_SIZE = 1400


class Packet:
    seq_num: int
    checksum: int
    ack: int
    fin: bool
    is_query: bool
    data: str

    def __init__(self, seq_num, end_conection, request_download):
        self.seq_num = seq_num
        self.fin = end_conection
        self.is_query = request_download
        self.data = ''

    def acknowledge(self, prev_pack_seq_num: int):
        self.ack = prev_pack_seq_num + 1

    def insert_data(self, data: str):
        if data.__sizeof__() < MAX_DATA_SIZE:
            self.data = data

    def generate_checksum(self):
        # TODO: revisar como hacer el checksum en UDP
        self.checksum = hash(self)

    def get_data(self):
        return self.data

    def get_seq_num(self):
        return self.seq_num

    def get_checksum(self):
        return self.checksum

    def get_ack(self):
        return self.ack

    def get_fin(self):
        return self.fin

    def get_is_query(self):
        return self.is_query