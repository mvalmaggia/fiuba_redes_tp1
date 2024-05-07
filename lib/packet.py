from enum import Enum
import zlib


MAX_DATA_SIZE = 2048


class QueryType(Enum):
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"


class Packet:
    seq_num: int
    checksum: int
    ack: bool
    fin: bool
    query_type: QueryType
    data: bytes

    def __init__(self, seq_num, end_conection=False, query_type=None, file_name=None, ack=False):
        self.seq_num = seq_num
        self.fin = end_conection
        self.ack = ack
        self.query_type = query_type
        self.file_name = file_name
        self.data = b''
        self.checksum = self.generate_checksum()

    def acknowledge(self):
        self.ack = True

    def insert_data(self, data: bytes):
        if len(data) > MAX_DATA_SIZE:
            raise ValueError("Data size exceeds the maximum allowed size.")
        self.data = data
        self.checksum = self.generate_checksum()

    def generate_checksum(self):
        return zlib.crc32(self.data) & 0xffffffff

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

    def get_is_download_query(self):
        return self.query_type == QueryType.DOWNLOAD

    def get_is_upload_query(self):
        return self.query_type == QueryType.UPLOAD

    def get_file_name(self):
        return self.file_name

    def __str__(self):
        return f"Packet(seq_num={self.seq_num}, ack={self.ack}, fin={self.fin}, query_type={self.query_type}, data_length={len(self.data)}), checksum={self.checksum})"
