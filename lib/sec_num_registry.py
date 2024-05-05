import threading


class SecNumberRegistry:
    def __init__(self):
        self.sec_num_reg = {}
        self.lock = threading.Lock()

    def get_sec_num(self, client_address):
        with self.lock:
            if client_address not in self.sec_num_reg:
                self.sec_num_reg[client_address] = 1
            return self.sec_num_reg[client_address]

    def update_sec_num(self, client_address, sec_num):
        with self.lock:
            self.sec_num_reg[client_address] = sec_num
            return self.sec_num_reg[client_address]
