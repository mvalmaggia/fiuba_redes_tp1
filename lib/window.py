import threading


class Window:
    def __init__(self, size, client_address, send_function):
        self.size = size
        self.packets = []
        self.lock = threading.Lock()
        self.timer = None
        self.timeout_interval = 3
        self.send_function = send_function
        self.client_address = client_address

    def try_add_packet(self, packet):
        with self.lock:
            if len(self.packets) < self.size:
                print(f"Paquete agregado, ventana largo: {len(self.packets)}")
                self.packets.append(packet)
                self.restart_timer()
                return True
            return False

    def restart_timer(self):
        # Cancela el temporizador anterior si existe
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout_interval, self.retransmit_unacknowledged_packets)
        self.timer.start()

    def retransmit_unacknowledged_packets(self):
        # Suponiendo que retransmite todos los paquetes no confirmados
        with self.lock:
            for packet in self.packets:
                print(f"Retransmitiendo paquete {packet.seq_num}")
                self.send_function(self.client_address, packet)

    def remove_confirmed(self, ack_num):
        # Elimina paquetes confirmados de la ventana
        with self.lock:
            self.packets = [pkt for pkt in self.packets if pkt.seq_num > ack_num]
