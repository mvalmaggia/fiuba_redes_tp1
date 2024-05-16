import logging
import threading

log = logging.getLogger(__name__)


class SecNumberRegistry:
    def __init__(self):
        self.ack_registry = {}
        self.lock = threading.Lock()
        self.new_ack_events = {}

    def has(self, client_address, sec_num):
        with self.lock:
            log.debug("ACK REGISTRY: %s", self.ack_registry)
            return (
                client_address in self.ack_registry
                and self.ack_registry[client_address] >= sec_num
            )

    def set_ack(self, client_address, sec_num: int):
        with self.lock:
            # Si no está registrado o si está registrado y es el siguiente
            # sec_num, se actualiza
            if (
                client_address not in self.ack_registry
                or self.ack_registry[client_address] + 1 == sec_num
            ):
                self.ack_registry[client_address] = sec_num
            if client_address not in self.new_ack_events:
                self.new_ack_events[client_address] = threading.Event()
            self.new_ack_events[client_address].set()

    def get_last_ack(self, client_address):
        with self.lock:
            return self.ack_registry.get(client_address, 0)

    def wait_for_new_ack(self, client_address, timeout=None):
        event = self.new_ack_events.get(client_address)
        if event:
            event.wait(timeout)
            event.clear()
            return True
        return False