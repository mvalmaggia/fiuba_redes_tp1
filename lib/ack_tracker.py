import threading


class AckTracker:
    def __init__(self):
        self.acks_received = {}
        self.lock = threading.Lock()

    def add_ack(self, client_address, seq_num):
        with self.lock:
            self.acks_received[(client_address, seq_num)] = True

    def check_ack(self, client_address, seq_num):
        with self.lock:
            return self.acks_received.get((client_address, seq_num), False)
