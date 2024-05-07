import queue
import threading
from enum import Enum

from lib.packet import Packet
from lib.sec_num_registry import SecNumberRegistry
from lib.transmission import send_stop_n_wait, receive, send_file


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
                client_thread = threading.Thread(target=self.handle_client, args=(client_address, client_queue))
                client_thread.start()

            # Enviar el paquete a la cola del cliente
            self.client_handlers[client_address].put(packet)

    def handle_client(self, client_address, client_queue):
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
            send_file(self.server_socket, client_address, self.dir_path + '/' + packet.get_file_name(), start_seq_num,
                      lambda seq_num: self.seq_nums_sent.has(client_address, seq_num))
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
        self.send_server(client_address, ack_packet)

    def send_server(self, client_address, packet):
        with self.send_lock:
            send_stop_n_wait(self.server_socket, client_address, packet,
                             lambda seq_num: self.seq_nums_sent.has(client_address, seq_num))

    @staticmethod
    def save_packet_in_file(packet: Packet, file_path):
        data = packet.get_data()
        with open(file_path, "ab") as file:
            file.write(data)

