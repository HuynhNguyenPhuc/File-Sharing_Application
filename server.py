import socket


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

        # Client socket
        self.client_socket = None

    def listen(self):
        """
        This function is used to listen to the request of the clients

        Parametesrs:

        Returns:
        """
        self.server_socket.listen()
        self.client_socket, addr = self.server_socket.accept()

    def add(self, hostname, filename):
        """
        This function is used to add new file when receive publish function from client

        Parameters:
        - hostname: name of hostname
        - filename: name of file in client's resportity
        """
        if hostname not in self.hostname_file.keys():
            self.hostname_file[hostname] = [filename]
        else:
            self.hostname_file[hostname].append(filename)

    def register(self, hostname, address):
        """
        This function is used to register hosts to system

        Parameters:
        - hostname (string): Name of host
        - address (string): Address of host

        Returns:
        Boolean: Successful or not
        """
        self.hostname_to_ip[hostname] = address
        self.hostname_file[hostname] = []

    def ping(self, hostname, timeout=10):
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

    def discover(self, hostname):
        """
        This function is used to discover local files in host named hostname

        Parameters:
        - hostname (string): Name of host

        Returns:
        List: List of local files of the host

        """
        message = self.hostname_file[hostname]
        self.client_socket.send(message)

    def response(self, message):
        """
        This function is used to reponse to the request of the clients

        Parameters:
        -message: message want to send to client
        Returns:
        """

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


server = Server('10.230.143.196', 5000)
server.listen()
