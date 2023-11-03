import socket
from threading import Thread
import re
import json
import os
from message import Message, Type, Header


class Server(object):
    def __init__(self, server_port):
        # The server's IP address and port number
        self.server_port = server_port

        # Create dictionary for TCP table
        with open("hostname_to_ip.json", "r") as fp:
            self.hostname_to_ip = json.load(fp)
        with open("ip_to_hostname.json", "r") as fp:
            self.ip_to_hostname = json.load(fp)
        with open("hostname_file.json", "r") as fp:
            self.hostname_file = json.load(fp)

        # Create a socket and bind it to the server's IP and port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((socket.gethostbyname(socket.gethostname()), self.server_port))

        # Create request queue
        self.request_queue = list()

        # Multi-thread lists for communication
        self.register_queue = list()
        self.publish_queue = list()

    def listen(self):
        """
        This method is used for listen to connecting request from clients

        Parameters:

        Return:
        """
        self.server_socket.listen()
        while True:
            client_socket, addr = self.server_socket.accept()
            hostname = self.ip_to_hostname[addr[0]]
            self.active_client[hostname] = client_socket
            client_thread = Thread(target=self.handle_client, args=(client_socket, hostname,))
            client_thread.start()

    def handle_client(self, client_socket, hostname):
        # Listen to message from client
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
            # REQUEST, TAKE_HOST_LIST
            if message_header == Header.TAKE_HOST_LIST:
                self.take_host_list(client_socket, message)

            # REQUEST, RETRIEVE_REQUEST
            elif message_header == Header.RETRIEVE_REQUEST:
                self.retrieve_host(client_socket, message)

            # REQUEST, PUBLISH
            elif message_header == Header.PUBLISH:
                self.publish(client_socket, hostname, message)
                print(self.hostname_file)

            elif message_header == Header.END_CONNECTION:
                client_socket.close()

    def take_host_list(self, client_socket, message):
        fname = message.get_info()
        response_message = Message(Header.TAKE_HOST_LIST, Type.RESPONSE, self.find(fname))
        self.send(client_socket, response_message)

    def retrieve_host(self, client_socket, message):
        hostip, fname = message.get_info()
        print(hostip)
        print(self.ip_socket)
        request = Message(Header.RETRIEVE_REQUEST, Type.RESPONSE, message.get_info())
        self.ip_socket[hostip].send(json.dumps(request.get_packet()).encode())
        print("OK")
        data = self.ip_socket[hostip].recv(2048)
        response_message = Message(Header.RETRIEVE_PROCEED, Type.RESPONSE, None)
        self.send(client_socket, response_message)

    def publish(self, client_socket, hostname, message):
        fname_tuple = message.get_info()
        fname = list(fname_tuple.keys())[0]
        if fname not in self.hostname_file[hostname]:
            self.hostname_file[hostname].append(fname)
            response_message = Message(Header.PUBLISH, Type.RESPONSE, 'OK')
        else:
            response_message = Message(Header.PUBLISH, Type.RESPONSE, 'DUPLICATE')
        self.send(client_socket, response_message)

    def register(self, hostname='abc', address='abc'):
        while True:
            if len(self.register_queue) > 0:
                message = self.register_queue.pop()
                # self.hostname_to_ip[hostname] = address
                # self.hostname_file[hostname] = []
                # print(self.hostname_to_ip)
                # self.send(message)

    def ping(self, hostname, timeout=1000):
        if hostname in list(self.hostname_to_ip.keys()):
            client_ip = self.hostname_to_ip[hostname]
        else:
            pass

        client_socket = self.active_client[hostname]
        message = Message(Header.PING, Type.REQUEST, 'PING')
        client_socket.settimeout(timeout)
        self.send(client_socket, message)
        # response = client_socket.recv(1024)
        # if response == b'PONG':
        #     print("Client is alive")

    def discover(self, hostname):
        """
        This function is used to discover local files in host named hostname

        Parameters:
        - hostname (string): Name of host

        Returns:
        List: List of local files of the host

        """
        host_local_files = self.hostname_file[hostname]
        return host_local_files

    def find(self, fname):
        """
        This function is used to find clients who have file named fname

        Parameters:
        - fname: Name of target file

        Returns:
        List: list of clients having file fname
        """

        hosts_with_file = []

        for host, files in self.hostname_file.items():
            if fname in files:
                hosts_with_file.append((host, self.hostname_to_ip[host]))

        return hosts_with_file

    @staticmethod
    def send(client_socket, message: Message):
        """
        This function is used to reponse to the request of the clients

        Parameters:
        -message: message want to send to client

        Returns:
        """
        try:
            client_socket.send(json.dumps(message.get_packet()).encode())
        except Exception as e:
            print("Server response error: ", e)


server = Server(5000)
server.listen()
