import socket
from threading import Thread
import re
import json
from message import Message, Type, Header


class Server(object):
    def __init__(self, server_ip, server_port):
        # The server's IP address and port number
        self.server_ip = server_ip
        self.server_port = server_port

        # Create dictionary for TCP table
        self.hostname_to_ip = {'minhquan': '192.168.1.9'}
        self.hostname_file = {'minhquan': ['file1.txt', 'file3.mp4']}
        self.ip_socket = {}

        # Create a socket and bind it to the server's IP and port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))

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
            self.ip_socket[addr[0]] = client_socket
            print(addr)
            client_thread = Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        try:
            while True:
                # Listen to message from client
                print("Listening...")
                message = client_socket.recv(1024).decode()

                # Clients have terminated the connection
                if not message:
                    break

                # print(message)

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

                elif message_header == Header.END_CONNECTION:
                    break
                # End of Cao Minh Quan needs
                # ----------------------------------------------------------------
                # Add your message handling logic here
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def take_host_list(self, client_socket, message: Message):
        fname = message.get_info()
        response_message = Message(Header.TAKE_HOST_LIST, Type.RESPONSE, self.find(fname))
        self.response(client_socket, response_message)

    def retrieve_host(self, client_socket, message: Message):
        hostip, fname = message.get_info()
        print(hostip)
        print(self.ip_socket)
        request = Message(Header.RETRIEVE_REQUEST, Type.RESPONSE, message.get_info())
        self.ip_socket[hostip].send(json.dumps(request.get_packet()).encode())
        print("OK")
        data = self.ip_socket[hostip].recv(2048)
        response = Message(Header.RETRIEVE_PROCEED, Type.RESPONSE, None)
        client_socket.send(json.dumps(response.get_packet()).encode())

    def add(self, hostname='abc', filename='abc'):
        """
        This method is used to add new file when receive publish function from client

        Parameters:
        - hostname: name of hostname
        - filename: name of file in client's resportity
        """
        while True:
            if len(self.publish_queue) > 0:
                message = self.publish_queue.pop()
                # if hostname not in self.hostname_file.keys():
                #     self.hostname_file[hostname] = [filename]
                # else:
                #     self.hostname_file[hostname].append(filename)
                self.response(message)

    def register(self, hostname='abc', address='abc'):
        """
        This function is used to register hosts to system

        Parameters:
        - hostname (string): Name of host
        - address (string): Address of host

        Returns:
        Boolean: Successful or not
        """
        while True:
            if len(self.register_queue) > 0:
                message = self.register_queue.pop()
                # self.hostname_to_ip[hostname] = address
                # self.hostname_file[hostname] = []
                # print(self.hostname_to_ip)
                self.response(message)

    def ping(self, hostname, timeout=1000):
        """
        This function is used to check live host named hostname

        Parameters:
        - hostname (string): Name of host

        Returns:
        Boolean: Whether that host is live or not
        """

        client_ip = self.hostname_to_ip[hostname]

        if client_ip is None:
            print(f"No IP address found for hostname {hostname}")
            return False

        try:
            # Set the socket timeout
            self.client_socket.settimeout(timeout)

            # Send a ping message
            self.client_socket.send(b"PING")

            # Wait for a response
            response = self.client_socket.recv(1024)

            # If we receive a response, the client is alive
            if response == b'PONG':
                print("Client is alive")
        except socket.timeout:
            # If we don't receive a response within a timeout, the client is not alive
            print("Client is not alive")
        finally:
            # Reset the socket timeout
            self.client_socket.settimeout(None)

        self.flag = True
        return

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

    def response(self, client_socket, message: Message):
        """
        This function is used to reponse to the request of the clients

        Parameters:
        -message: message want to send to client
        Returns:
        """
        client_socket.send(json.dumps(message.get_packet()).encode())

server = Server('192.168.1.9', 5000)
server.listen()
