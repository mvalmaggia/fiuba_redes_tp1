import logging

import pickle
import queue
import time
import threading
from enum import Enum

from lib.packet import Packet
from lib.sec_num_registry import SecNumberRegistry
from lib.transmission import receive
from lib.window import Window

log = logging.getLogger(__name__)


class AlgorithmType(Enum):
    SW = "S&W"
    GBN = "GBN"


class ClientContext:
    def __init__(
        self, client_address, client_queue, window: Window | None = None
    ):
        self.client_address = client_address
        self.client_queue = client_queue
        self.window: Window | None = window


class Server:
    def __init__(self, server_socket, dir_path, algorithm):
        """
        Aqui se guarda el registro del ultimo numero de secuencia enviado
        a cada cliente
        Necesita ser thread-safe porque no puede despues de escribir parar
        a leer, sino que con esto
        Se puede despachar el ack, registrarlo y luego hacer polling
        para ver si se recibio el ack
        """

        self.server_socket = server_socket
        self.send_lock = threading.Lock()
        self.dir_path = dir_path
        self.algorithm = algorithm
        self.client_handlers = {}
        self._clients_pending_upload = {}
        self.seq_nums_sent = SecNumberRegistry()
        self.seq_nums_recv = SecNumberRegistry()

    def listen(self):
        log.debug(
            f" Server listo para recibir consultas, "
            f"usando {self.algorithm} como algoritmo"
        )

        while True:
            packet, client_address = receive(self.server_socket)
            if client_address in self.client_handlers and packet.ack:
                if self.algorithm == AlgorithmType.SW:
                    self.seq_nums_sent.set_ack(
                        client_address, packet.get_seq_num()
                    )
                    continue
                else:
                    window = self.client_handlers[client_address].window
                    window.remove_confirmed(packet.get_seq_num())
                    window.restart_timer()
                    continue
            if client_address not in self.client_handlers:
                client_queue = queue.Queue()
                # Crear una nueva cola para este cliente
                log.info("Nuevo cliente: %s", client_address)
                # Iniciar un nuevo hilo para manejar a este cliente
                if self.algorithm == AlgorithmType.GBN:

                    window = Window(10, client_address, self.send_locking)
                    self.client_handlers[client_address] = ClientContext(
                        client_address, client_queue, window
                    )
                    client_thread = threading.Thread(
                        target=self.handle_client_gbn,
                        args=(client_address, client_queue, window),
                    )
                else:
                    self.client_handlers[client_address] = ClientContext(
                        client_address, client_queue, None
                    )
                    client_thread = threading.Thread(
                        target=self.handle_client_sw,
                        args=(client_address, client_queue),
                    )
                client_thread.start()

            # Enviar el paquete a la cola del cliente
            self.client_handlers[client_address].client_queue.put(packet)

    def handle_client_gbn(self, client_address, client_queue, window: Window):
        log.debug("Utilizando GBN para cliente ", client_address)
        while True:
            packet = client_queue.get()
            log.debug(f"Manejando el paquete: {packet}")
            if (
                self.seq_nums_recv.get_last_ack(client_address)
                != packet.get_seq_num() - 1
            ):
                log.info(
                    f"El paquete {packet.get_seq_num()} "
                    f"no es el esperado, "
                    f"enviando ack solicitando el proximo"
                )
                last_ack = self.seq_nums_recv.get_last_ack(client_address)
                self.send_gbn(
                    client_address, Packet(last_ack + 1, ack=True), window
                )
                continue
            self.seq_nums_recv.set_ack(client_address, packet.get_seq_num())

            if packet.get_fin():
                self.send_gbn(
                    client_address,
                    Packet(packet.seq_num + 1, end_conection=True, ack=True),
                    window,
                )
                log.info("Conexion con %s finalizada", client_address)
                break
            self.process_packet_gbn(packet, client_address, window)
        window.close_window()

    def process_packet_gbn(self, packet, client_address, window: Window):
        if packet.get_is_download_query():
            self.send_gbn(
                client_address, Packet(packet.seq_num + 1, ack=True), window
            )
            start_seq_num = 1
            self.send_file_gbn(
                client_address,
                self.dir_path + "/" + packet.get_file_name(),
                start_seq_num,
                window,
            )
        elif packet.get_is_upload_query():
            file_path = self.dir_path + "/" + packet.get_file_name()
            open(file_path, "w").close()
            self._clients_pending_upload[client_address] = file_path
            self.send_gbn(
                client_address, Packet(packet.seq_num + 1, ack=True), window
            )
        elif client_address in self._clients_pending_upload:
            last_seq_num = self.seq_nums_recv.get_last_ack(client_address)
            log.debug(
                f"Seq num recibido: {packet.get_seq_num()} "
                f"y el ultimo seq num recibido es {last_seq_num}"
            )
            if packet.get_seq_num() == last_seq_num:
                file_path = self._clients_pending_upload[client_address]
                self.save_packet_in_file(packet, file_path)
            self.send_gbn(
                client_address, Packet(packet.seq_num + 1, ack=True), window
            )
        else:
            log.error("Query no reconocida")

    def handle_client_sw(self, client_address, client_queue):
        # Esto se puede hacer en el hilo principal porque no se bloquea
        while True:
            packet = (
                client_queue.get()
            )  # Bloquea hasta que hay un paquete en la cola
            if self.seq_nums_recv.has(client_address, packet.get_seq_num()):
                log.info(
                    f"Paquete {packet.get_seq_num()} "
                    f"ya fue recibido, descartando"
                )
                self.send_ack_sw(client_address)
                continue
            self.seq_nums_recv.set_ack(client_address, packet.get_seq_num())
            if packet.get_fin():
                self.send_ack_sw(client_address)
                log.info("Conexion con %s finalizada", client_address)
                break
            self.process_packet_sw(packet, client_address)

    def process_packet_sw(self, packet: Packet, client_address):
        if packet.get_is_download_query():
            start_seq_num = 1
            self.send_ack_sw(client_address)
            self.send_file_sw(
                client_address,
                self.dir_path + "/" + packet.get_file_name(),
                start_seq_num,
            )
        elif packet.get_is_upload_query():
            file_path = self.dir_path + "/" + packet.get_file_name()
            open(file_path, "w").close()
            self._clients_pending_upload[client_address] = file_path
            self.send_ack_sw(client_address)
        elif client_address in self._clients_pending_upload:
            # Verifico si es el paquete necesito.
            last_seq_num = self.seq_nums_recv.get_last_ack(client_address)
            if packet.get_seq_num() == last_seq_num:
                file_path = self._clients_pending_upload[client_address]
                self.save_packet_in_file(packet, file_path)
            self.send_ack_sw(client_address)
        else:
            log.error("Query no reconocida")

    def send_ack_sw(self, client_address):
        last_ack = self.seq_nums_recv.get_last_ack(client_address)
        log.debug("El ultimo ack enviado fue: %s", last_ack)
        ack_packet = Packet(last_ack + 1, ack=True)
        self.send_sw(client_address, ack_packet)

    def send_sw(
        self, client_address, packet: Packet, timeout=0.1, attempts=50
    ):
        log.debug(f"Enviando paquete {packet}")
        if packet.ack:
            self.send_locking(client_address, packet)
            return True
        for i in range(attempts):
            self.send_locking(client_address, packet)
            time.sleep(timeout)
            if (
                self.seq_nums_sent.get_last_ack(client_address)
                > packet.seq_num
            ):
                log.debug(f"Recibido ack para el paquete {packet.seq_num}")
                return True
            log.debug(
                f"Reintentando enviar paquete {packet.seq_num}, "
                f"intento {i + 1}/{attempts}"
            )
        raise TimeoutError("No se recibio ack para el paquete")

    def send_file_sw(
        self,
        client_address,
        file_path,
        start_sec_num,
        timeout=0.1,
        attempts=50,
    ):
        log.debug(f"Enviando archivo {file_path}")
        # Primero se abre el archivo y se va leyendo de a pedazos de 1024
        # bytes para enviarlos al cliente en paquetes
        with open(file_path, "rb") as file:
            file_content = file.read(2048)
            # log.debug(f"Enviando paquete {sec_num} con
            # {len(file_content)} bytes")
            while file_content:
                data_packet = Packet(start_sec_num, False)
                data_packet.insert_data(file_content)
                self.send_sw(client_address, data_packet, timeout, attempts)
                file_content = file.read(2048)
                start_sec_num += 1
            # Se envia un paquete con el fin de la transmision
            fin_packet = Packet(start_sec_num, True)
            self.send_sw(client_address, fin_packet, timeout, attempts)

    def send_locking(self, client_address, packet: Packet):
        with self.send_lock:
            self.server_socket.sendto(pickle.dumps(packet), client_address)

    def send_gbn(self, client_address, packet, window):
        while True:
            if packet.ack or window.try_add_packet(packet):
                self.send_locking(client_address, packet)
                log.debug(f"Enviando paquete {packet}")
                break
            else:
                log.debug(
                    f"Ventana llena, esperando para enviar "
                    f"paquete {packet.seq_num} "
                    f"a {client_address}"
                )
                # TODO: Implementar un mecanismo
                # de espera más eficiente (eventos)
                time.sleep(0.5)
                # Espera activa

    def send_file_gbn(
        self, client_address, file_path, start_sec_num, window: Window
    ):
        log.debug(f"Enviando archivo {file_path}")
        # Primero se abre el archivo y se va leyendo de a pedazos
        # de 1024 bytes para enviarlos al cliente en paquetes
        with open(file_path, "rb") as file:
            file_content = file.read(2048)
            # log.debug(f"Enviando paquete {sec_num} "
            # f"con {len(file_content)} bytes")
            while file_content:
                data_packet = Packet(start_sec_num, False)
                data_packet.insert_data(file_content)
                self.send_gbn(client_address, data_packet, window)
                file_content = file.read(2048)
                start_sec_num += 1
            # Se envia un paquete
            fin_packet = Packet(start_sec_num, True)
            self.send_gbn(client_address, fin_packet, window)

    @staticmethod
    def save_packet_in_file(packet: Packet, file_path):
        data = packet.get_data()
        with open(file_path, "ab") as file:
            file.write(data)
