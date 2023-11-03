# Problem when changing the network, after changing the network, login must happen again
# Write hostname_file and hostname_list

import socket
from threading import Thread
import re
import json
import os
from message import Message, Type, Header

SERVER_TIMEOUT = 2


class Server(object):
    def __init__(self, server_port):
        # The server's IP address and port number
        self.server_port = server_port

        # Create dictionary for TCP table
        self.hostname_to_ip = {}
        self.ip_to_hostname = {}
        with open("hostname_file.json", "r") as fp:
            self.hostname_file = json.load(fp)
        with open("hostname_list.json", "r") as fp:
            self.hostname_list = json.load(fp)

        # Create a socket and bind it to the server's IP and port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((socket.gethostbyname(socket.gethostname()), self.server_port))

    def listen(self):
        self.server_socket.listen()
        while True:
            client_socket, addr = self.server_socket.accept()
            if addr[0] not in list(self.ip_to_hostname.keys()):
                hostname = None
            else:
                hostname = self.ip_to_hostname[addr[0]]
            client_thread = Thread(target=self.handle_client, args=(client_socket, hostname, addr[0]))
            client_thread.start()

    def handle_client(self, client_socket, hostname, address):
        print(f"Handling request for client {hostname} ... ")
        try:
            # Listen to message from client
            client_socket.settimeout(SERVER_TIMEOUT)
            message = client_socket.recv(1024).decode()

            # Clients have terminated the connection
            if not message:
                client_socket.close()
            # Clients have asked for request
            else:
                # Retrieve header and type
                message = Message(None, None, None, message)
                message_header = message.get_header()
                message_type = message.get_type()

                # Handle each kind of message
                # REQUEST, PUBLISH
                if message_header == Header.PUBLISH:
                    self.publish(client_socket, hostname, message)
                    print(self.hostname_file)

                # REQUEST, REGISTER
                elif message_header == Header.REGISTER:
                    self.register(client_socket, message)

                # REQUEST, FETCH
                elif message_header == Header.FETCH:
                    self.fetch(client_socket, message)

                # REQUEST, LOG_IN
                elif message_header == Header.LOG_IN:
                    self.login(client_socket, address, message)

                # REQUEST, END_CONNECTION
                elif message_header == Header.END_CONNECTION:
                    client_socket.close()
                    print("Closing...")
        except Exception as e:
            print(f"Server request handling error for client {hostname}. Status: {e}")
        finally:
            print(f'Handling request for client {hostname} done')

    def publish(self, client_socket, hostname, message):
        info = message.get_info()
        fname = info['fname']
        lname = info['lname']
        payload = {'fname': fname, 'lname': lname, 'result': None}
        if fname not in self.hostname_file[hostname]:
            self.hostname_file[hostname].append(fname)
            payload['result'] = 'OK'
            response_message = Message(Header.PUBLISH, Type.RESPONSE, payload)
        else:
            payload['result'] = 'DUPLICATE'
            response_message = Message(Header.PUBLISH, Type.RESPONSE, payload)
        self.send(client_socket, response_message)

    def ping(self, hostname):
        if hostname in list(self.hostname_list.keys()):
            if hostname in list(self.hostname_to_ip.keys()):
                client_ip = self.hostname_to_ip[hostname]
            else:
                print(f"Client {hostname} not login yet")
                return
        else:
            print(f"Client {hostname} not exist")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.PING, Type.REQUEST, 'PING')
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                response_message = Message(None, None, None, response_message)
                if response_message:
                    print(f"Client {hostname} is alive")
            except Exception as e:
                print(f"Client {hostname} is not alive. Status info: {e}")

    def discover(self, hostname):
        if hostname in list(self.hostname_to_ip.keys()):
            client_ip = self.hostname_to_ip[hostname]
        else:
            print(f"Client {hostname} not exist")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.DISCOVER, Type.REQUEST, 'DISCOVER')
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                # Dictionary of {fname: lname}
                file_list = Message(None, None, None, response_message).get_info()
                print(file_list)
            except Exception as e:
                print(f"Client {hostname} can not be discoverd. Status info: {e}")

    def register(self, client_socket, message):
        info = message.get_info()
        hostname = info['hostname']
        password = info['password']
        if hostname in list(self.hostname_list.keys()):
            payload = 'DUPLICATE'
        else:
            payload = 'OK'
            self.hostname_list[hostname] = password
            self.hostname_file[hostname] = []
        response_message = Message(Header.REGISTER, Type.RESPONSE, payload)
        self.send(client_socket, response_message)

    def login(self, client_socket, address, message):
        info = message.get_info()
        hostname = info['hostname']
        password = info['password']
        if hostname in list(self.hostname_to_ip.keys()):
            prev_address = self.hostname_to_ip[hostname]
            self.hostname_to_ip[hostname] = address
            self.ip_to_hostname.pop(prev_address)
            self.ip_to_hostname[address] = hostname
        else:
            self.hostname_to_ip[hostname] = address
            self.ip_to_hostname[address] = hostname
        if hostname in list(self.hostname_list.keys()):
            if password == self.hostname_list[hostname]:
                payload = 'PASSWORD'
            else:
                payload = 'OK'
        else:
            payload = 'HOSTNAME'
        response_message = Message(Header.LOG_IN, Type.RESPONSE, payload)
        self.send(client_socket, response_message)

    def fetch(self, client_socket, message):
        fname = message.get_info()
        ip_with_file_list = self.search(fname)
        payload = {'fname': fname, 'avail_ips': ip_with_file_list}
        response_message = Message(Header.TAKE_HOST_LIST, Type.RESPONSE, payload)
        self.send(client_socket, response_message)

    def search(self, fname):
        ip_with_file_list = []
        for hostname, file_list in self.hostname_file.items():
            if fname in file_list:
                if self.check_active(hostname):
                    ip_with_file_list.append(self.hostname_to_ip[hostname])
        return ip_with_file_list

    def check_active(self, hostname):
        if hostname in list(self.hostname_to_ip.keys()):
            client_ip = self.hostname_to_ip[hostname]
        else:
            return False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.PING, Type.REQUEST, 'PING')
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                if response_message:
                    return True
            except (Exception,):
                return False

    @staticmethod
    def send(client_socket, message: Message):
        try:
            client_socket.send(json.dumps(message.get_packet()).encode())
        except Exception as e:
            print("Server message sending error: ", e)

    def run(self):
        while True:
            opcode = int(input("Type your task here: "))
            if opcode == 1:
                self.ping('minhquan')
            elif opcode == 2:
                self.discover('minhquan')
            elif opcode == 3:
                pass
            else:
                pass

    def start(self):
        listen_thread = Thread(target=self.listen, args=())
        run_thread = Thread(target=self.run, args=())
        listen_thread.start()
        run_thread.start()


server = Server(5000)
server.run()
