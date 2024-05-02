from enum import Enum

MAX_DATA_SIZE = 1400


class QueryType(Enum):
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"


class Packet:
    seq_num: int
    checksum: int
    ack: int
    fin: bool
    query_type: QueryType
    data: str

    def __init__(self, seq_num, end_conection, query_type=None, file_name=None):
        self.seq_num = seq_num
        self.fin = end_conection
        self.ack = 0
        self.query_type = query_type
        self.file_name = file_name
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

    def get_is_download_query(self):
        return self.query_type == QueryType.DOWNLOAD

    def get_is_upload_query(self):
        return self.query_type == QueryType.UPLOAD

    def get_file_name(self):
        return self.file_name
