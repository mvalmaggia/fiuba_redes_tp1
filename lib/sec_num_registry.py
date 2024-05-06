import threading


class SecNumberRegistry:
    def __init__(self):
        self.ack_registry = {}
        self.lock = threading.Lock()
        self.new_ack_event = threading.Event()

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

    def get_acks(self, client_address):
        with self.lock:
            return set(self.ack_registry.get(client_address, set()))

    def clear_acks(self, client_address):
        with self.lock:
            if client_address in self.ack_registry:
                self.ack_registry[client_address].clear()

    def wait_for_new_ack(self, timeout=None):
        self.new_ack_event.wait(timeout)
        self.new_ack_event.clear()

