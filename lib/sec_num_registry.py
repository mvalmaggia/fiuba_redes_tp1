import threading


class SecNumberRegistry:
    def __init__(self):
        self.ack_registry = {}
        self.lock = threading.Lock()

    def has(self, client_address, sec_num):
        with self.lock:
            return self.ack_registry.get(client_address) is not None and sec_num in self.ack_registry[client_address]

    def put(self, client_address, sec_num):
        with self.lock:
            if client_address not in self.ack_registry:
                self.ack_registry[client_address] = set()
            self.ack_registry[client_address].add(sec_num)

    def get_last_ack(self, client_address):
        with self.lock:
            if client_address not in self.ack_registry:
                return None
            return max(self.ack_registry[client_address])
