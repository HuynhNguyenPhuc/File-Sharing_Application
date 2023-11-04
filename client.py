import socket
from threading import Thread, Lock
from ftplib import FTP, FTP_TLS
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from message import Message, Type, Header
import os
import shutil
import json
import time

class Client:
    def __init__(self, server_host, server_port, client_hostname, client_password):
        """
        Constructor: Initializes attributes, to be added more
        """
        # Store information of the centralized server
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Store information of the client
        self.client_hostname = client_hostname
        self.client_password = client_password
        self.client_host = socket.gethostbyname(socket.gethostname())
        self.client_port = 5001
        self.login_succeeded = False
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.published_files = {}
        if not os.path.exists("published_file.json"):
            with open("published_file.json", "w") as fp:
                pass
        with open("published_file.json", "r") as fp:
            self.published_files = json.load(fp)
        self.ftp_server = None # To be initialized only once per lifetime
        self.message_queue = [] # Synchronized message queue
        self.mutex_queue = Lock()
        self.isRunning = True
        self.isFTPRunning = False
        self.t: dict[str, Thread] = {}
    
    def connect(self):
        """
        Establish connection with server and join the P2P network and start running
        
        Return: None
        """
        print('Start running')
        self.listen_socket.bind((self.client_host, self.client_port))
        # A thread for FTP server -> FTPServerSide class, to be added here instead of down there
        
        # A thread for listening incoming messages
        self.t['listen_thread'] = Thread(target=self.listen)
        # A thread for preprocessing file transfers
        # self.t.append(Thread(target=self.preprocess_file_transfer))
        
        for thread in self.t.values():
            thread.start()
    
    def disconnect(self):
        """
        Disconnect from the server and network and stop running
        
        Return: None
        """
        print('Shut down')
        self.listen_socket.close()
        # try:
        #     self.stop_ftp_server()
        # except Exception as e:
        #     print(f"Disconnect FTP server forbidden: {e}")
        # self.isRunning = False
        message = Message(Header.END_CONNECTION, Type.REQUEST, None)
        self.send_message(message, self.server_host, self.server_port)
        # time.sleep(1)
        # self.client_socket.close()
        for thread in self.t.values():
            thread.join()
    
    def listen(self):
        print(f"Start listening at {self.client_host} port {self.client_port}")
        self.listen_socket.listen()
        while True:
            try:
                recv_socket, src_addr = self.listen_socket.accept()
                print(f"Accept connection from {self.client_host} port {self.client_port}")
                new_thread = Thread(target=self.handle_incoming_connection, args=(recv_socket, src_addr))
                new_thread.start()
            except OSError:
                print("Stop accepting connection")
                break
    
    def handle_incoming_connection(self, recv_socket, src_addr):
        try:
            recv_socket.settimeout(5)
            message = recv_socket.recv(2048).decode()
            message = Message(None, None, None, message)
            self.notify_message(message, src_addr[0])
            message_header = message.get_header()
            
            if message_header == Header.PING and src_addr[0] == self.server_host:
                self.reply_ping_message(recv_socket)
            elif message_header == Header.DISCOVER and src_addr[0] == self.server_host:
                self.reply_discover_message(recv_socket)
            elif message_header == Header.FETCH:
                self.contact_fetch(message)
            else:
                print('Forbidden message')
            # with self.mutex_queue:
            #     self.message_queue.append(message)
        except Exception as e:
            print(f"An error occurred in listen: {e}")
        finally:
            recv_socket.close()
    
    def send_message(self, message, dest_ip, dest_port=5000, existing_socket=None):
        """
        Send an encoded message to a host or an existing socket
        Parameters:
        - message: Message to send
        - dest_ip: IP address to send to
        - dest_port: Port to send to
        - 
        Return: True if message sent successfully, False otherwise
        """
        encoded_msg = json.dumps(message.get_packet()).encode()
        if existing_socket:
            sock = existing_socket
        else:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((dest_ip, dest_port))
            except:
                print(f"Failed to connect to {dest_ip}:{dest_port}")
                return False
        res = True
        try:
            sock.sendall(encoded_msg)
        except:
            print(f"An error occurred while sending a {message.get_header()} message to {sock.getpeername()}")
            res = False
        if not existing_socket:
            sock.close()
        return res
    
    def register(self):
        """
        Client registers its hostname and password to the server
        
        Parameters: None
        
        Return: True if registered successfully, False otherwise
        """
        # Request to register
        request = Message(Header.REGISTER, Type.REQUEST, {"hostname": self.client_hostname, "password": self.client_password})
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            print(f"Failed to connect to {self.server_host}:{self.server_port}")
        self.send_message(request, None, None, tmp_sock)
        # Receive register response
        response = tmp_sock.recv(2048).decode()
        response = Message(None, None, None, response)
        self.notify_message(response, self.server_host)
        if response.get_header() != Header.REGISTER:
            print('Forbidden message')
            return False
        result = response.get_info()
        print(f"Register status: {result}")
        tmp_sock.close()
        return True
    
    def log_in(self):
        """
        Client logs in to server
        
        Parameters: None
        
        Return: True if logged in successfully, False otherwise
        """
        # Send login request
        request = Message(Header.LOG_IN, Type.REQUEST, {"hostname": self.client_hostname, "password": self.client_password})
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            print(f"Failed to connect to {self.server_host}:{self.server_port}")
        self.send_message(request, None, None, tmp_sock)
        # Receive login response
        response = tmp_sock.recv(2048).decode()
        response = Message(None, None, None, response)
        self.notify_message(response, self.server_host)
        if response.get_header() != Header.LOG_IN:
            print('Forbidden message')
            return False
        result = response.get_info()
        if result == 'OK':
            self.login_succeeded = True
        else:
            self.login_succeeded = False
        print(f"Login status: {result}")
        tmp_sock.close()
        return self.login_succeeded
    
    def log_out(self):
        """
        Client logs out of server
        
        Parameters: None
        
        Return: True if logged out successfully, False otherwise
        """
        # Send logout request
        if not self.is_login():
            return False
        request = Message(Header.LOG_OUT, Type.REQUEST, None)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            print(f"Failed to connect to {self.server_host}:{self.server_port}")
        self.send_message(request, None, None, tmp_sock)
        # Receive logout response
        response = tmp_sock.recv(2048).decode()
        response = Message(None, None, None, response)
        self.notify_message(response, self.server_host)
        if response.get_header() != Header.LOG_OUT:
            print('Forbidden message')
            return False
        result = response.get_info()
        if result == 'OK':
            self.login_succeeded = False
        print(f"Logout status: {result}")
        tmp_sock.close()
        return True
    
    def reply_ping_message(self, sock):
        """
        Receive ping message from the server
        """
        print("Receive ping from server")
        response = Message(Header.PING, Type.RESPONSE, 'PONG')
        self.send_message(response, None, None, sock)
        sock.close()
    
    def reply_discover_message(self, sock):
        """
        Receive discover message from the server
        """
        print("Receive discover from server")
        response = Message(Header.DISCOVER, Type.RESPONSE, self.published_files)
        self.send_message(response, None, None, sock)
        sock.close()
    
    def publish(self, lname, fname):
        """
        A local file (which is stored in the client's file system at lname) is added to the client's repository as a file named fname and this information is conveyed to the server.
        
        Parameters:
        - lname: The path to the file in local file system
        - fname: The file to be uploaded and published in the repository
        
        Return: True if the file was successfully published, False otherwise
        """
        # Send publish request
        request = Message(Header.PUBLISH, Type.REQUEST, {'fname': fname, 'lname': lname})
        self.send_message(request, self.server_host, self.server_port)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            print(f"Failed to connect to {self.server_host}:{self.server_port}")
        self.send_message(request, None, None, tmp_sock)
        # Receive publish response
        response = tmp_sock.recv(2048).decode()
        response = Message(None, None, None, response)
        self.notify_message(response, self.server_host)
        info = response.get_info()
        if response.get_header() != Header.PUBLISH or fname != info['fname'] or lname != info['lname']:
            print('Forbidden message')
            return False
        result = info['result']
        if result == "ERROR":
            print("Publish failed")
            return False
        # Add file to repository
        self.published_files[fname] = lname
        with open("published_file.json", "w") as fp:
            json.dump(self.published_files, fp, indent=4)
        print("Publish succeded!")
        return True
    
    def preprocess_file_transfer(self):
        try:
            while self.isRunning:
                with self.mutex_queue:
                    for message in self.message_queue:
                        if message.get_header() == Header.RETRIEVE_REQUEST:
                            self.message_queue.remove(message)
                            fname = message.get_info()[1]
                            self.__check_cached__(fname)
                            response = Message(Header.RETRIEVE_PROCEED, Type.REQUEST, None)
                            self.send_message(response, self.client_socket)
                time.sleep(2)
        except Exception as e:
            print(f"An error occurred in preprocess: {e}")
        finally:
            print("Thread preprocess finished successfully")
    
    
    def initiate_ftp_server(self): # currently opcode 1, to be added in connect()/constructor
        """
        Allocate and establish the server for FTP connection
        
        Return: None
        """
        if isinstance(self.ftp_server, self.FTPServerSide) and self.isFTPRunning:
            return
        self.ftp_server = self.FTPServerSide(self.client_host, self.__check_cached__)
        self.ftp_server.start()
        self.isFTPRunning = True
    
    def stop_ftp_server(self): # currently opcode 3, to be added in disconnect()/destructor
        if not isinstance(self.ftp_server, self.FTPServerSide):
            raise Exception('Not an FTP server')
        if isinstance(self.ftp_server, self.FTPServerSide) and not self.isFTPRunning:
            return
        self.ftp_server.stop()
        self.ftp_server.join()
        self.isFTPRunning = False
    
    def retrieve(self, fname='file1.txt', host='localhost'):
        """
        Establish an FTP connection to the host server
        
        Parameters:
        - fname: the file name
        - host: client's IP address to connect
        
        Return: None
        """
        dest_dir, dest_file = "download/", fname
        # Handle non-existing download directory
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
        
        i = 0
        # Handle existing files
        while os.path.exists(dest_dir + dest_file):
            i += 1
            dest_file = f"Copy_{i}_" + fname
        
        ftp = FTP(host)
        ftp.log_in('mmt', 'hk231')
        with open(dest_dir + dest_file, 'wb') as fp:
            ftp.retrbinary(f'RETR {fname}', fp.write)
        
        ftp.quit()
    
    def notify_message(self, message, src):
        message_header = message.get_header()
        message_type = message.get_type()
        print(f"Received a {message_header.name}-{message_type.name} message from {'server' if src == self.server_host else src}")
    
    
    
    def fetch(self, fname):
        """
        Fetch some copy of the target file and add it to the local repository
        First, request from the centralized server the list of online hosts having the given file fname
        
        Parameters:
        - fname: The file to be downloaded
        
        Return: None
        """
        request = Message(Header.FETCH, Type.REQUEST, fname)
        self.send_message(request, self.server_host, self.server_port)
        
    def contact_fetch(self, message):
        """
        The second phase of the fetch command. After requesting the list of hosts, communicate with other client(s) to retrieve the file
        """
        info = message.get_info()
        fname, host_list = info['fname'], info['avail_ips']
        # Choose host to download file from
        if not host_list:
            print("No available host to fetch file")
            return
        final_dest = None
        for host_ip in host_list:
            print(f"-----Request from host {host_ip}-----")
            request = Message(Header.RETRIEVE, Type.REQUEST, [host_ip, fname])
            self.send_message(request, self.server_host, self.server_port)
            # while True:
            #     flag = False
            #     with self.mutex_queue:
            #         for message in self.message_queue:
            #             if message.get_header() == Header.RETRIEVE_PROCEED:
            #                 self.message_queue.remove(message)
            #                 flag = True
            #                 break
            #     if flag:
            #         break
            #     time.sleep(1)
        self.retrieve(fname, final_dest)
        # Add file to local repository with publish
    
    def __check_cached__(self, fname):
        """
        Add the file fname to the cache directory if not already cached
        
        Parameters:
        - fname: The name of the file
        
        Returns: None
        """
        cached_dir = "cache/"
        if not os.path.exists(cached_dir):
            os.mkdir(cached_dir)
        if fname and fname in self.published_files:
            filepath = cached_dir + fname
            if not os.path.exists(filepath):
                shutil.copy2(self.published_files[fname], cached_dir + fname)
    
    def is_login(self):
        return self.login_succeeded
    #  FTP server on another thread
    class FTPServerSide(Thread):
        def __init__(self, host_ip, check_cache):
            Thread.__init__(self)
            self.host_ip = host_ip
            self.check_cache = check_cache
        
        def run(self):
            # Initialize FTP server
            authorizer = DummyAuthorizer()
            self.check_cache(None)
            authorizer.add_user('mmt', 'hk231', './cache', perm='rl')
            handler = FTPHandler
            handler.authorizer = authorizer
            handler.banner = "Connection Success"
            
            self.server = ThreadedFTPServer((self.host_ip, 21), handler)
            self.server.max_cons = 256
            self.server.max_cons_per_ip = 5
            
            self.server.serve_forever()
        
        def stop(self):
            self.server.close_all()