import threading


class Window:
    def __init__(self, size):
        self.size = size
        self.packets = []
        self.lock = threading.Lock()
        self.space_available = threading.Event()
        self.space_available.set()  # Inicialmente, hay espacio disponible.

    def add_packet(self, packet):
        with self.lock:
            if len(self.packets) < self.size:
                self.packets.append(packet)
                return True
            return False

    def remove_confirmed(self, ack_num):
        with self.lock:
            initial_length = len(self.packets)
            self.packets = [pkt for pkt in self.packets if pkt.seq_num > ack_num]
            if len(self.packets) < initial_length:
                self.space_available.set()  # Hay espacio disponible después de eliminar paquetes.

    def wait_for_space(self):
        self.space_available.wait()  # Espera hasta que haya espacio disponible.
        self.space_available.clear()  # Reinicia el estado para futuras esperas.

    def get_unacked_packets(self):
        """Obtiene una copia de la lista de paquetes no confirmados."""
        with self.lock:
            return list(self.packets)
