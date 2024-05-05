import threading
import pickle

from lib.packet import Packet
from lib.sec_num_registry import SecNumberRegistry
from lib.transmission import send, receive, send_file


class Server:
    def __init__(self, server_socket, dir_path):
        self.secs_num_registry = SecNumberRegistry()
        self.server_socket = server_socket
        self.dir_path = dir_path
        self.clients_pending_upload = {}

    def listen(self):
        print('[INFO] Server listo para recibir consultas')
        while True:
            received_packet, client_address = receive(self.server_socket, self.secs_num_registry)
            if received_packet.ack:
                continue
            if received_packet.get_fin():
                self.clients_pending_upload.pop(client_address, None)
                print('[INFO] Conexion finalizada lado server')
                continue

            thread = threading.Thread(target=self.handle_message,
                                      args=(received_packet,
                                            client_address,
                                            ))
            thread.start()

    def handle_message(self, packet: Packet, client_address):
        print('[INFO] Conexion con ', client_address)

        if packet.get_is_download_query():
            send_file(self.server_socket, client_address, self.dir_path + '/' + packet.get_file_name(), self.secs_num_registry)

        elif packet.get_is_upload_query():
            open(self.dir_path + '/' + packet.get_file_name(), "w").close()
            self.clients_pending_upload[client_address] = 1
            self.send_ack(client_address, self.server_socket, 0)
            print("sent ack to client to start upload")

        elif (client_address in self.clients_pending_upload and
              self.clients_pending_upload[client_address] != packet.get_seq_num()):
            print(self.clients_pending_upload[client_address])
            print(packet.get_seq_num())
            self.clients_pending_upload[client_address] = packet.get_seq_num()
            self.receive_file(packet, client_address, self.server_socket, self.dir_path)

    def receive_file(self, packet, client_address, server_socket, dir_path):
        print('[INFO] Subiendo archivo...')

        data = packet.get_data()

        print(packet.get_file_name())

        file_path = dir_path + '/' + packet.get_file_name()
        print(file_path)

        with open(file_path, "ab") as file:
            print(f"Se va a escribir en {file_path} el siguiente contenido: {data}")
            file.write(data.encode())

        self.send_ack(client_address, server_socket, packet.get_seq_num())

    def send_ack(self, client_address, server_socket, seq_num):
        ack_packet = Packet(0, False)
        ack_packet.acknowledge(seq_num)
        buf = pickle.dumps(ack_packet)
        server_socket.sendto(buf, client_address)

    def receive_packet(self):
        """  Recibe un paquete y lo decodifica y si corresponde envia un ack
        """
        raw_packet, client_address = self.server_socket.recvfrom(1024)
        packet: Packet = pickle.loads(raw_packet)
        if packet.ack:
            self.secs_num_registry.update_sec_num(client_address, packet.seq_num)