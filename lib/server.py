import threading

from lib.packet import Packet
from lib.sec_num_registry import SecNumberRegistry
from lib.transmission import send, receive, send_file


class Server:
    def __init__(self, server_socket, dir_path):
        # Aqui se guarda el registro del ultimo numero de secuencia enviado a cada cliente
        # Necesita ser thread-safe porque no puede despues de escribir parar a leer, sino que con esto
        # Se puede despachar el ack, registrarlo y luego hacer polling para ver si se recibio el ack
        self.seq_nums_sent = SecNumberRegistry()
        self.seq_nums_recv = SecNumberRegistry()
        self._clients_pending_upload = {}
        self.server_socket = server_socket
        self.dir_path = dir_path

    def listen(self):
        print('[INFO] Server listo para recibir consultas')
        while True:
            received_packet, client_address = receive(self.server_socket)
            print('[INFO] Paquete recibido: ', received_packet, ' de ', client_address)
            if received_packet.ack:
                self.seq_nums_sent.put(client_address, received_packet.get_seq_num())
                continue
            if self.seq_nums_recv.has(client_address, received_packet.get_seq_num()):
                self.send_ack(client_address, received_packet.get_seq_num())
                continue
            self.seq_nums_recv.put(client_address, received_packet.get_seq_num())
            if received_packet.get_fin():
                self._clients_pending_upload.pop(client_address, None)
                self.send_ack(client_address, received_packet.get_seq_num())
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
            send_file(self.server_socket, client_address, self.dir_path + '/' + packet.get_file_name(), packet.get_seq_num(),
                      lambda seq_num: self.seq_nums_sent.get(client_address) == seq_num)
        elif packet.get_is_upload_query():
            file_path = self.dir_path + '/' + packet.get_file_name()
            open(file_path, "w").close()
            self._clients_pending_upload[client_address] = file_path
            self.send_ack(client_address, packet.get_seq_num())
        elif client_address in self._clients_pending_upload:
            # self.clients_pending_upload[client_address] = packet.get_seq_num()
            file_path = self._clients_pending_upload[client_address]
            self.save_packet_in_file(packet, file_path)
            self.send_ack(client_address, packet.get_seq_num())
        else:
            print('[ERROR] Query no reconocida')

    def send_ack(self, client_address, seq_num):
        ack_packet = Packet(seq_num + 1, ack=True)
        self.send_server(self.server_socket, client_address, ack_packet)

    def send_server(self, server_socket, client_address, packet):
        send(server_socket, client_address, packet, lambda seq_num: self.seq_nums_sent.get(client_address) == seq_num)

    def send_file_server(self, client_address, file_path):
        initial_sec_num = self.seq_nums_sent.get(client_address)
        send_file(self.server_socket, client_address, file_path, initial_sec_num,
                  lambda seq_num: self.seq_nums_sent.get(client_address) == seq_num)

    def save_packet_in_file(self, packet: Packet, file_path):
        data = packet.get_data()
        with open(file_path, "ab") as file:
            file.write(data)
