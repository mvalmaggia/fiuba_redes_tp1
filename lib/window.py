import threading


class Window:
    def __init__(self, size):
        self.size = size
        self.packets = []
        self.lock = threading.Lock()

    def add_packet(self, packet):
        """Añade un paquete a la ventana si hay espacio disponible."""
        with self.lock:
            if len(self.packets) < self.size:
                self.packets.append(packet)
                return True
            return False

    def remove_confirmed(self, ack_num):
        """Elimina los paquetes confirmados hasta y incluido el número de secuencia especificado."""
        with self.lock:
            self.packets = [pkt for pkt in self.packets if pkt.seq_num > ack_num]

    def get_unacked_packets(self):
        """Obtiene una copia de la lista de paquetes no confirmados."""
        with self.lock:
            return list(self.packets)
