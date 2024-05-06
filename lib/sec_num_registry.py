import threading


class SecNumberRegistry:
    def __init__(self):
        self.ack_registry = {}
        self.lock = threading.Lock()
        self.new_ack_event = threading.Event()

    def has(self, client_address, sec_num):
        with self.lock:
            print("[DEBUG] ACK REGISTRY: ", self.ack_registry)
            return client_address in self.ack_registry and self.ack_registry[client_address] >= sec_num

    def set_ack(self, client_address, sec_num: int):
        # Recibo el paquete sec_num
        with self.lock:
            # Si no está registrado o si está registrado y es el siguiente sec_num, se actualiza
            if client_address not in self.ack_registry or self.ack_registry[client_address] + 1 == sec_num:
                self.ack_registry[client_address] = sec_num
                self.new_ack_event.set()

    def get_last_ack(self, client_address):
        with self.lock:
            return self.ack_registry.get(client_address, 0)

    def wait_for_new_ack(self, timeout=None):
        self.new_ack_event.wait(timeout)
        self.new_ack_event.clear()

