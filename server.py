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
        self.hostname_to_ip = {'minhquan': '192.168.1.5'}
        self.hostname_file = {'minhquan': ['file1.txt', 'file3.mp4']}
        self.ip_socket = {}

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

    def handle_client(self, client_socket):
        try:
            while True:
                print("hearing")
                message = client_socket.recv(1024).decode()
                if not message:  # Client has disconnected
                    break
                print(message)
                message = Message(None, None, None, message)
                header = message.get_header()
                # ----------------------------------------------------------------
                # Message from Cao Minh Quan: This is the least that the server has to implement to assist file transfer functionality
                # Whatever you do, please ask me before changing this code
                if header == Header.TAKE_HOST_LIST:
                    print("send host list")
                    fname = message.get_info()
                    response = Message(Header.TAKE_HOST_LIST, Type.RESPONSE, self.find(fname))
                    client_socket.send(json.dumps(response.get_packet()).encode())
                elif header == Header.RETRIEVE_REQUEST:
                    hostip, fname = message.get_info()
                    print(hostip)
                    print(self.ip_socket[hostip])
                    request = Message(Header.RETRIEVE_REQUEST, Type.RESPONSE, message.get_info())
                    self.ip_socket[hostip].send(json.dumps(request.get_packet()).encode())
                    print("OK")
                    data = self.ip_socket[hostip].recv(2048)
                    response = Message(Header.RETRIEVE_PROCEED, Type.RESPONSE, None)
                    client_socket.send(json.dumps(response.get_packet()).encode())
                elif header == Header.END_CONNECTION:
                    break
                # End of Cao Minh Quan needs
                # ----------------------------------------------------------------
                # Add your message handling logic here
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def listen(self):
        self.server_socket.listen()
        while True:
            client_socket, addr = self.server_socket.accept()
            self.ip_socket[addr[0]] = client_socket
            client_thread = Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

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
                hosts_with_file.append((host, self.hostname_to_ip[host]))

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



server = Server('192.168.1.5', 5000)
server.run()
