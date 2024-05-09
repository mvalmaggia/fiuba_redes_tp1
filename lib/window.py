import logging
import threading

log = logging.getLogger(__name__)


class Window:
    def __init__(self, size, client_address, send_function):
        self.size = size
        # Lista de paquetes sin ack
        self.packets = []
        self.lock = threading.Lock()
        self.timer = None
        self.timeout_interval = 0.2
        self.send_function = send_function
        self.client_address = client_address
        self.condition = threading.Condition(self.lock)

    def try_add_packet(self, packet):
        with self.lock:
            if len(self.packets) < self.size:
                self.packets.append(packet)
                log.debug(
                    f"Paquete {packet.seq_num} agregado, "
                    f"ventana largo: {len(self.packets)}"
                )
                self.restart_timer()
                return True
            return False

    def restart_timer(self):
        # Cancela el temporizador anterior si existe
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(
            self.timeout_interval, self.retransmit_unacknowledged_packets
        )
        self.timer.start()

    def retransmit_unacknowledged_packets(self):
        # Suponiendo que retransmite todos los paquetes no confirmados
        for packet in self.packets:
            log.debug(f"Retransmitiendo paquete {packet.seq_num}")
            self.send_function(self.client_address, packet)

        self.restart_timer()

    def remove_confirmed(self, ack_num):
        # Elimina paquetes confirmados de la ventana
        with self.lock:
            paquetes = [
                self.packets[i].seq_num for i in range(len(self.packets))
            ]
            log.debug(
                f"Se recibio el seq num {ack_num} y los paquetes "
                f"en la ventana son: "
                f"{paquetes}"
            )
            self.packets = [
                packet for packet in self.packets if packet.seq_num >= ack_num
            ]
            paquetes = [
                self.packets[i].seq_num for i in range(len(self.packets))
            ]
            log.debug(
                f"Paquetes en la ventana después de remover: " f"{paquetes}"
            )
            if not self.packets:
                # Notifica a los hilos esperando que la ventana está vacía
                self.condition.notify_all()

    def close_window(self):
        """
        Solo utilizar cuando se está seguro de que la ventana se va a vaciar.
        """
        with self.condition:
            self.condition.wait_for(lambda: not self.packets)
            log.debug("La ventana ahora está vacía.")
        if self.timer:
            self.timer.cancel()
            self.timer.join()
            log.debug("Temporizador detenido")

    def wait_for_empty_window(self, timeout=None):
        with self.condition:
            return self.condition.wait_for(lambda: not self.packets, timeout)
