import pickle
import queue
import time
import threading
from enum import Enum

from lib.packet import Packet
from lib.sec_num_registry import SecNumberRegistry
from lib.transmission import receive
from lib.window import Window


class AlgorithmType(Enum):
    SW = "S&W"
    GBN = "GBN"


class Server:
    def __init__(self, server_socket, dir_path, algorithm=AlgorithmType.SW):
        # Aqui se guarda el registro del ultimo numero de secuencia enviado a cada cliente
        # Necesita ser thread-safe porque no puede despues de escribir parar a leer, sino que con esto
        # Se puede despachar el ack, registrarlo y luego hacer polling para ver si se recibio el ack
        self.server_socket = server_socket
        self.send_lock = threading.Lock()
        self.dir_path = dir_path
        self.algorithm = algorithm
        self.client_handlers = {}
        self._clients_pending_upload = {}
        self.seq_nums_sent = SecNumberRegistry()
        self.seq_nums_recv = SecNumberRegistry()

    def listen(self):
        print('[INFO] Server listo para recibir consultas')

        while True:
            packet, client_address = receive(self.server_socket)
            print('[INFO] Paquete recibido: ', packet, ' de ', client_address)
            if packet.get_ack():
                self.seq_nums_sent.set_ack(client_address, packet.get_seq_num())
                continue
            if client_address not in self.client_handlers:
                # Crear una nueva cola para este cliente
                client_queue = queue.Queue()
                self.client_handlers[client_address] = client_queue
                print('[INFO] Nuevo cliente: ', client_address)
                # Iniciar un nuevo hilo para manejar a este cliente
                if self.algorithm == AlgorithmType.GBN:
                    client_thread = threading.Thread(target=self.handle_client_gbn, args=(client_address, client_queue))
                else:
                    client_thread = threading.Thread(target=self.handle_client_sw, args=(client_address, client_queue))
                client_thread.start()

            # Enviar el paquete a la cola del cliente
            self.client_handlers[client_address].put(packet)

    def handle_client_gbn(self, client_address, client_queue):
        window = Window(4)
        window_thread = threading.Thread(target=self.handle_acks_and_retransmissions,
                                         args=(window, client_address, self.seq_nums_recv))
        window_thread.start()
        while True:
            packet = client_queue.get()
            if packet.ack:
                self.seq_nums_sent.set_ack(client_address, packet.get_seq_num())
                window.remove_confirmed(packet.get_seq_num())
                continue

    def handle_client_sw(self, client_address, client_queue):
        while True:
            packet = client_queue.get()  # Bloquea hasta que hay un paquete en la cola
            if packet.ack:
                self.seq_nums_sent.set_ack(client_address, packet.get_seq_num())
                continue
            if self.seq_nums_recv.has(client_address, packet.get_seq_num()):
                print("[INFO] Paquete ya recibido")
                self.send_ack(client_address)
                continue
            self.seq_nums_recv.set_ack(client_address, packet.get_seq_num())
            if packet.get_fin():
                self.send_ack(client_address)
                print('[INFO] Conexion con ', client_address, ' finalizada')
                break
            self.process_packet(packet, client_address)

    def process_packet(self, packet: Packet, client_address):
        if packet.get_is_download_query():
            start_seq_num = 1
            self.send_ack(client_address)
            self.send_file_sw(client_address, self.dir_path + '/' + packet.get_file_name(),
                              start_seq_num)
        elif packet.get_is_upload_query():
            file_path = self.dir_path + '/' + packet.get_file_name()
            open(file_path, "w").close()
            self._clients_pending_upload[client_address] = file_path
            self.send_ack(client_address)
        elif client_address in self._clients_pending_upload:
            file_path = self._clients_pending_upload[client_address]
            self.save_packet_in_file(packet, file_path)
            self.send_ack(client_address)
        else:
            print('[ERROR] Query no reconocida')

    def send_ack(self, client_address):
        last_ack = self.seq_nums_recv.get_last_ack(client_address)
        print('El ultimo ack enviado fue: ', last_ack)
        ack_packet = Packet(last_ack + 1, ack=True)
        self.send_sw(client_address, ack_packet)

    def send_sw(self, client_address, packet: Packet, timeout=0.1, attempts=5):
        if packet.ack:
            self.send_locking(client_address, packet)
            return True
        for i in range(attempts):
            print(f"Enviando paquete {packet.seq_num}")
            self.send_locking(client_address, packet)
            time.sleep(timeout)
            if self.seq_nums_sent.has(client_address, packet.seq_num):
                print(f"Recibido ack para el paquete {packet.seq_num}")
                return True
            print(f"Reintentando enviar paquete {packet.seq_num}, intento {i + 1}/{attempts}")
        raise TimeoutError("No se recibio ack para el paquete")

    def send_file_sw(self, client_address, file_path, start_sec_num, timeout=1, attempts=5):
        print(f"Enviando archivo {file_path}")
        # Primero se abre el archivo y se va leyendo de a pedazos de 1024 bytes para enviarlos al cliente en paquetes
        with open(file_path, "rb") as file:
            file_content = file.read(2048)
            # print(f"Enviando paquete {sec_num} con {len(file_content)} bytes")
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
        print(f"Enviando ack {packet}")

    def send_gbn(self, client_address, packet, window: Window):
        pass
        # while not window.add_packet(packet):
        #     print("La ventana está llena, esperando espacio...")
        #     window.wait_for_space()
        #
        # server_socket.sendto(pickle.dumps(packet), client_address)
        # print(f"Paquete enviado: {packet.seq_num}")

    def handle_acks_and_retransmissions(self, window: Window, client_address, ack_registry: SecNumberRegistry,
                                        timeout=0.2):
        while True:
            ack_registry.wait_for_new_ack(client_address, timeout)  # Espera un nuevo ACK o timeout
            last_ack = ack_registry.get_last_ack(client_address)
            window.remove_confirmed(last_ack)
            unacked_packets = window.get_unacked_packets()
            for packet in unacked_packets:
                self.send_sw(client_address, packet)
                print(f"Reintentando enviar paquete {packet.seq_num}")

    @staticmethod
    def save_packet_in_file(packet: Packet, file_path):
        data = packet.get_data()
        with open(file_path, "ab") as file:
            file.write(data)

