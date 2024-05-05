import threading

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
            received_packet, client_address = receive(self.server_socket)
            if received_packet.ack:
                self.secs_num_registry.put(client_address, received_packet.get_seq_num())
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
            self.send_ack(client_address, packet.get_seq_num())
            send_file(self.server_socket, client_address, self.dir_path + '/' + packet.get_file_name(), self.secs_num_registry)
        elif packet.get_is_upload_query():
            open(self.dir_path + '/' + packet.get_file_name(), "w").close()
            self.clients_pending_upload[client_address] = 1
            self.send_ack(client_address, packet.get_seq_num())
        elif client_address in self.clients_pending_upload:
            self.clients_pending_upload[client_address] = packet.get_seq_num()
            self.save_packet_in_file(packet)
            self.send_ack(client_address, packet.get_seq_num())
        else:
            print('[ERROR] Query no reconocida')

    def send_ack(self, client_address, seq_num):
        ack_packet = Packet(seq_num + 1, ack=True)
        self.send_server(self.server_socket, client_address, ack_packet)

    def send_server(self, server_socket, client_address, packet):
        send(server_socket, client_address, packet, lambda seq_num: self.secs_num_registry.get(client_address) == seq_num, 0.1, 5)

    def send_file_server(self, client_address, file_path):
        initial_sec_num = self.secs_num_registry.get(client_address)
        send_file(self.server_socket, client_address, file_path, initial_sec_num,
                  lambda seq_num: self.secs_num_registry.get(client_address) == seq_num, 0.1, 5)

    def save_packet_in_file(self, packet: Packet):
        data = packet.get_data()
        file_path = self.dir_path + '/' + packet.get_file_name()
        with open(file_path, "ab") as file:
            file.write(data.encode())
