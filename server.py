import socket
from threading import Thread
import re


class Server(object):
    def __init__(self, server_ip, server_port):
        # The server's IP address and port number
        self.server_ip = server_ip
        self.server_port = server_port

        # Create dictionary for TCP table
        self.hostname_to_ip = {}
        self.hostname_file = {}

        # Create a socket and bind it to the server's IP and port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))

        # Create client socket
        self.client_socket = None

        # Create request queue
        self.request_queue = list()

        # Multi-thread lists for communication
        self.register_queue = list()
        self.publish_queue = list()

    def listen(self):
        """
        This function is used to listen to the request of the clients

        Parametesrs:

        Returns:
        """
        self.server_socket.listen()
        self.client_socket, addr = self.server_socket.accept()

        # Flag for testing multi-thread
        flag = True

        while True:
            message = self.client_socket.recv(1024).decode()
            if not message:
                break
            print(message)
            if flag:
                self.register_queue.append(message)
                flag = False
            else:
                self.publish_queue.append(message)
                break
            # self.request_queue.append(message)

            # self.work_on_message(message)

    def work_on_message(self, message):
        self.response(message)

    def add(self, hostname='abc', filename='abc'):
        """
        This function is used to add new file when receive publish function from client

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

    def response(self, message):
        """
        This function is used to reponse to the request of the clients

        Parameters:
        -message: message want to send to client
        Returns:
        """
        self.client_socket.send(message.encode())
        self.flag = True
        return

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
                hosts_with_file.append(host)

        return hosts_with_file

    def run(self):
        listenning_thread = Thread(target=self.listen)
        register_thread = Thread(target=self.register)
        publish_thread = Thread(target=self.add)

        listenning_thread.start()
        register_thread.start()
        publish_thread.start()

        listenning_thread.join()
        register_thread.join()
        publish_thread.join()



server = Server('192.168.1.9', 5000)
server.run()
