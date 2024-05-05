import threading


class SecNumberRegistry:
    def __init__(self):
        self.sec_num_reg = {}
        self.lock = threading.Lock()

    def has(self, client_address, sec_num):
        with self.lock:
            return self.sec_num_reg.get(client_address) == sec_num

    def put(self, client_address, sec_num):
        with self.lock:
            self.sec_num_reg[client_address] = sec_num

    def get(self, client_address):
        with self.lock:
            return self.sec_num_reg.get(client_address)
