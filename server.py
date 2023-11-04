# Problem when changing the network, after changing the network, login must happen again
# Write hostname_file and hostname_list

# import re
# import os
import socket
import json
from queue import Queue
from threading import Thread, Lock
from message import Message, Type, Header

SERVER_TIMEOUT = 2


class Server(object):
    def __init__(self, server_port):
        # The server's port number
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

        # Create output queue
        self.output_queue = Queue(maxsize=100)
        self.queue_mutex = Lock()

    def listen(self):
        """
        This method is used to listen upcoming connections from clients, then deliver each client to a thread
        to handle requests

        Parameters:

        Return:
        """
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
        """
        This method is used to handle requests for each client

        Parameters:
        - client_socket (socket): The connection between client and server itself
        - hostname (str): Hostname of client
        - address (str): IP address of client

        Return:
        - None
        """
        output = "<-------------------------------------------->\n"
        output += f"Handling request for client {hostname} ... \n"
        output += ">>\n"
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
                # message_type = message.get_type()

                # Handle each kind of message
                # REQUEST, PUBLISH
                if message_header == Header.PUBLISH:
                    output += f"Client {hostname}: PUBLISH\n"
                    status = self.publish(client_socket, hostname, message)
                    output += f"Status: {status}\n"

                # REQUEST, REGISTER
                elif message_header == Header.REGISTER:
                    output += f"Client {hostname}: REGISTER\n"
                    status = self.register(client_socket, message)
                    output += f"Status: {status}\n"

                # REQUEST, FETCH
                elif message_header == Header.FETCH:
                    output += f"Client {hostname}: FETCH\n"
                    status = self.fetch(client_socket, message)
                    output += f"Status: {status}\n"

                # REQUEST, LOG_IN
                elif message_header == Header.LOG_IN:
                    output += f"Client {hostname}: LOG_IN\n"
                    status = self.login(client_socket, address, message)
                    output += f"Status: {status}\n"

                # REQUEST, LOG_OUT
                elif message_header == Header.LOG_OUT:
                    output += f"Client {hostname}: LOG_OUT\n"
                    status = self.logout(client_socket, hostname)
                    output += f"Status: {status}\n"

                # REQUEST, END_CONNECTION
                elif message_header == Header.END_CONNECTION:
                    output += f"Client {hostname}: END_CONNECTION\n"
                    client_socket.close()
                    output += "Status: OK\n"
        except Exception as e:
            output += f"Server request handling error for client {hostname}. Status: {e}\n"
        finally:
            output += ">>\n"
            output += f'Handling request for client {hostname} done\n'
            self.queue_mutex.acquire()
            if not self.output_queue.full():
                self.output_queue.put(output)
            self.queue_mutex.release()

    def publish(self, client_socket, hostname, message):
        """
        This method is used to reponse to the PUBLISH request. There are two types of response message which are OK
        if the file does not exit in list and DUPLICATE otherwise

        Parameters:
        - client_socket (socket): The connection between client and server itself
        - hostname (str): Hostname of client
        - message (Message): Request message from client

        Return:
        - None
        """
        info = message.get_info()
        fname = info['fname']
        lname = info['lname']
        payload = {'fname': fname, 'lname': lname, 'result': None}
        if fname not in self.hostname_file[hostname]:
            self.hostname_file[hostname].append(fname)
            payload['result'] = 'OK'
            with open("hostname_file.json", "w") as fp:
                json.dump(self.hostname_file, fp, indent=4)
        else:
            payload['result'] = 'DUPLICATE'
        response_message = Message(Header.PUBLISH, Type.RESPONSE, payload)
        self.send(client_socket, response_message)
        return payload['result']

    def ping(self, hostname):
        """
        This method is used to PING to one particular client identified by hostname

        Parameters:
        - hostname (str): Hostname of client

        Return:
        - None
        """
        client_info = f"--Client--: {hostname}\n"
        if hostname in list(self.hostname_list.keys()):
            if hostname in list(self.hostname_to_ip.keys()):
                client_ip = self.hostname_to_ip[hostname]
            else:
                return client_info + "--Status--: NOT LOGIN YET\n"
        else:
            return client_info + "--Status--: NOT REGISTER YET\n"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.PING, Type.REQUEST, 'PING')
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                if response_message:
                    return client_info + "--Status--: ALIVE\n"
            except Exception as e:
                return client_info + f"--Status--: NOT ALIVE - {e}\n"

    def discover(self, hostname):
        """
        This method is used to DISCOVER one particular client identified by hostname

        Parameters:
        - hostname (str): Hostname of client

        Return:
        - None
        """
        client_info = f"--Client--: {hostname}"
        if hostname in list(self.hostname_list.keys()):
            if hostname in list(self.hostname_to_ip.keys()):
                client_ip = self.hostname_to_ip[hostname]
            else:
                return client_info + "--Status--: NOT LOGIN YET\n"
        else:
            return client_info + "--Status--: NOT REGISTER YET\n"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.DISCOVER, Type.REQUEST, 'DISCOVER')
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                file_list = Message(None, None, None, response_message).get_info()
                status = '--Status--: SUCCESS\n--File list--:\n'
                for file in list(file_list.keys()):
                    status += str(file) + '\n'
                return client_info + status
            except Exception as e:
                return client_info + f"--Status--: FAIL - {e}\n"

    def register(self, client_socket, message):
        """
        This method is used to response to REGISTER request. There are two types of response message which are OK if
        provided hostname is available and DUPLICATE otherwise

        Parameters:
        - client_socket (socket): Connection between client and server itself
        - message (Message): Request message from client

        Return:
        - None
        """
        info = message.get_info()
        hostname = info['hostname']
        password = info['password']
        if hostname in list(self.hostname_list.keys()):
            payload = 'DUPLICATE'
        else:
            payload = 'OK'
            self.hostname_list[hostname] = password
            self.hostname_file[hostname] = []
            with open("hostname_list.json", "w") as fp:
                json.dump(self.hostname_list, fp, indent=4)
            with open("hostname_file.json", "w") as fp:
                json.dump(self.hostname_file, fp, indent=4)
        response_message = Message(Header.REGISTER, Type.RESPONSE, payload)
        self.send(client_socket, response_message)
        return payload

    def login(self, client_socket, address, message):
        """
        This method is used to response to LOG_IN request and modifying the mapping between hostname and IP address.
        There are three types of response message which are OK if log in successfully, PASSWORD if incorrect password,
        HOSTNAME if hostname does not exist and AUTHENTIC if list published files list on server not match with on local

        Parameters:
        - client_socket (socket): Connection between client and server itself
        - address (str): IP address of client
        - message (Message): Request message from client

        Return:
        - None
        """
        info = message.get_info()
        hostname = info['hostname']
        password = info['password']
        if hostname in list(self.hostname_list.keys()):
            if password != self.hostname_list[hostname]:
                payload = 'PASSWORD'
            else:
                payload = 'OK'
                if hostname in list(self.hostname_to_ip.keys()):
                    prev_address = self.hostname_to_ip[hostname]
                    self.hostname_to_ip[hostname] = address
                    self.ip_to_hostname.pop(prev_address)
                    self.ip_to_hostname[address] = hostname
                else:
                    self.hostname_to_ip[hostname] = address
                    self.ip_to_hostname[address] = hostname
                if not self.check_authentic(hostname):
                    self.hostname_to_ip.pop(hostname)
                    self.ip_to_hostname.pop(address)
                    payload = 'AUTHENTIC'
        else:
            payload = 'HOSTNAME'
        response_message = Message(Header.LOG_IN, Type.RESPONSE, payload)
        self.send(client_socket, response_message)
        return payload

    def logout(self, client_socket, hostname):
        del_address = self.hostname_to_ip[hostname]
        self.hostname_to_ip.pop(hostname)
        self.ip_to_hostname.pop(del_address)
        response_message = Message(Header.LOG_OUT, Type.RESPONSE, 'OK')
        self.send(client_socket, response_message)
        return 'OK'

    def fetch(self, client_socket, message):
        """
        This method is used to response to FETCH request. The response message to client will contain list of IP
        addresses which are alive and have fetching requested file identified by fname

        Parameters:
        - client_socket (socket): Connection between client and server itself
        - message (Message): Request message from client

        Return:
        - None
        """
        fname = message.get_info()
        ip_with_file_list = self.search(fname)
        payload = {'fname': fname, 'avail_ips': ip_with_file_list}
        response_message = Message(Header.TAKE_HOST_LIST, Type.RESPONSE, payload)
        self.send(client_socket, response_message)
        return 'OK'

    def search(self, fname):
        """
        This method is used to list out all the IP addresses which are alive and have file identified by fname

        Parameters:
        - fname (str): Requested file's name

        Return:
        - list: List of satisfying IP address
        """
        ip_with_file_list = []
        for hostname, file_list in self.hostname_file.items():
            if fname in file_list:
                if self.check_active(hostname):
                    ip_with_file_list.append(self.hostname_to_ip[hostname])
        return ip_with_file_list

    def check_active(self, hostname):
        """
        This method is used to check alive one particular client identified by hostname

        Parameters:
        - hostname (str): Hostname of client

        Return:
        - bool: True if the hostname is alive and False otherwise
        """
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

    def check_authentic(self, hostname):
        """
        This is used to check whether published file list on server matches with one on local or not

        Parameters:
        - hostname (str): Hostname of client

        Return:
        - bool: True if it matches and False otherwise
        """
        if hostname in list(self.hostname_to_ip.keys()):
            client_ip = self.hostname_to_ip[hostname]
        else:
            return False

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.settimeout(SERVER_TIMEOUT)
                client_socket.connect((client_ip, 5001))
                message = Message(Header.DISCOVER, Type.REQUEST, 'DISCOVER')
                self.send(client_socket, message)
                response_message = client_socket.recv(2048).decode()
                file_list = Message(None, None, None, response_message).get_info()
                result = True
                for server_file in list(file_list.keys()):
                    if server_file not in self.hostname_file[hostname]:
                        result = False
                        break
                return result
            except (Exception,):
                return False

    @staticmethod
    def send(client_socket, message: Message):
        """
        This method is used to send message to one particular client through provided connection

        Parameters:
        - client_socket (socket): Connection between client and server itself
        - message (Message): Request message from client

        Return:
        - None
        """
        try:
            client_socket.send(json.dumps(message.get_packet()).encode())
        except Exception as e:
            print("SENDING ERROR: ", e)

    def run(self, opcode, hostname):
        """
        This method is used to run server's actions as PING and DISCOVER

        Parameters:
        - opcode: Code for PING or DISCOVER
        - hostname: Hostname of client

        Return:
        - str: Command output
        """
        if opcode == 'PING':
            output = self.ping(hostname)
        elif opcode == 'DISCOVER':
            output = self.discover(hostname)
        return output

    def start(self):
        """
        This method to start server

        Parameters:
        - None

        Return:
        - None
        """
        listen_thread = Thread(target=self.listen, args=())
        listen_thread.start()


# Randomly run
if __name__ == 'main':
    server = Server(5000)
    server.listen()
    server.run()
