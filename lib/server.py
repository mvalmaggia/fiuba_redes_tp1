import threading
import pickle

from lib.packet import Packet


class Server:
    def __init__(self, server_socket, dir_path):
        self.secs_num_registry = SecNumberRegistry()
        self.server_socket = server_socket
        self.dir_path = dir_path
        self.clients_pending_upload = {}

    def listen(self):
        print('[INFO] Server listo para recibir consultas')
        while True:
            # TODO: un mensaje que corte ejecucion del servidor
            packet, client_address = self.server_socket.recvfrom(1024)
            decoded_packet: Packet = pickle.loads(packet)
            if decoded_packet.get_fin():
                self.clients_pending_upload.pop(client_address, None)
                print('[INFO] Conexion finalizada lado server')
                continue

            thread = threading.Thread(target=self.handle_message,
                                      args=(decoded_packet,
                                            client_address,
                                            ))
            thread.start()

    def handle_message(self, packet: Packet, client_address):
        print('[INFO] Conexion con ', client_address)

        if packet.get_is_download_query():
            seq_num = self.send_file(self.server_socket, client_address, packet, self.dir_path)
            end_pkt = Packet(seq_num + 1, True)
            buff = pickle.dumps(end_pkt)
            self.server_socket.sendto(buff, client_address)

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

    def send_file(self, server_socket, client_address, client_pkt: Packet,
                  dir_path: str):
        print('[INFO] Descargando archivo...')
        seq_num = 1

        # mando ack
        ack = Packet(seq_num, False)
        buf = pickle.dumps(ack)
        server_socket.sendto(buf, client_address)

        print('[DEBUG] dir = ', dir_path + '/' + client_pkt.get_data())
        file = open(dir_path + '/' + client_pkt.get_data(), 'r')
        data = file.read()
        file.close()
        dwnl_pkt = Packet(seq_num + 1, False)
        dwnl_pkt.insert_data(data)
        dwnl_pkt.acknowledge(client_pkt.get_seq_num())
        buf = pickle.dumps(dwnl_pkt)
        server_socket.sendto(buf, client_address)

        return seq_num

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


class SecNumberRegistry:
    def __init__(self):
        self.sec_num_reg = {}
        self.lock = threading.Lock()

    def add_ack(self, sender_address, seq_num):
        with self.lock:
            if sender_address not in self.sec_num_reg:
                self.sec_num_reg[sender_address] = []
            self.sec_num_reg[sender_address].append(seq_num)

    def check_ack(self, sender_address, seq_num):
        with self.lock:
            if sender_address not in self.sec_num_reg:
                return False
            return seq_num in self.sec_num_reg[sender_address]