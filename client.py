import socket
from threading import Thread
from ftplib import FTP, FTP_TLS
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from message import Message, Type, Header
import os
import shutil
import json

class Client:
    def __init__(self, server_host, server_port, client_hostname, client_password):
        """
        Constructing a Client instance.
        
        Parameters:
        - server_host: The IP address of the server
        - server_port: The port of the server
        - client_hostname: The hostname of the client
        - client_password: The password of the client
        """
        # Store information of the centralized server
        self.server_host = server_host
        self.server_port = server_port
        
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
        else:
            with open("published_file.json", "r") as fp:
                self.published_files = json.load(fp)
        self.ftp_server = None # To be initialized only once per lifetime
        self.__isFTPRunning = False
        self.__isConnected = False
        self.t: dict[str, Thread] = {}
        
        self.connect()
    
    def connect(self):
        """
        Establish connection with server and join the P2P network and start running.
        Must be called after object initialization.
        """
        if self.__isConnected:
            return
        # Bind a socket to this client
        self.listen_socket.bind((self.client_host, self.client_port))
        
        # A thread for FTP server -> FTPServerSide class, to be added here instead of down there
        self.initiate_ftp_server()
        
        # A thread to start listening incoming messages on the bound socket
        self.t['listen_thread'] = Thread(target=self.listen)
        
        for thread in self.t.values():
            thread.start()
        
        self.__isConnected = True
    
    def stop(self):
        """
        Disconnect from the server and network and stop running.
        Must be called before destroying the object.
        """
        if not self.__isConnected:
            return
        # Log out
        if self.is_login():
            self.log_out()
        
        # Close the listening socket
        self.listen_socket.close()
        
        # Close FTP server if it is running
        try:
            self.stop_ftp_server()
        except Exception as e:
            print(f"Disconnect FTP server forbidden: {e}")
        
        # Destroy cache directory
        if os.path.exists('cache'):
            shutil.rmtree('cache')
        
        for thread in self.t.values():
            thread.join()
        
        self.__isConnected = False
    
    def initiate_ftp_server(self): # currently option 1 in testcase, to be added to connect()/constructor
        """
        Allocate and establish the server for FTP connection.
        """
        if isinstance(self.ftp_server, self.FTPServerSide) and self.__isFTPRunning:
            return
        self.ftp_server = self.FTPServerSide(self.client_host, self.__check_cached__)
        self.ftp_server.start()
        self.__isFTPRunning = True
    
    def stop_ftp_server(self): # currently option 2 in testcase, to be added to disconnect()/destructor
        """
        Shut down the FTP server.
        """
        if not isinstance(self.ftp_server, self.FTPServerSide):
            raise Exception('Not an FTP server')
        if isinstance(self.ftp_server, self.FTPServerSide) and not self.__isFTPRunning:
            return
        self.ftp_server.stop()
        self.ftp_server.join()
        self.__isFTPRunning = False
    
    def listen(self):
        """
        Listen on the opening socket and create a new thread whenever it accepts a connection
        """
        self.listen_socket.listen()
        while True:
            try:
                recv_socket, src_addr = self.listen_socket.accept()
                new_thread = Thread(target=self.handle_incoming_connection, args=(recv_socket, src_addr))
                new_thread.start()
            except OSError:
                break
    
    def handle_incoming_connection(self, recv_socket, src_addr):
        """
        Handle a new connection and pass the message to the appropriate function.
        """
        try:
            recv_socket.settimeout(5)
            message = recv_socket.recv(2048).decode()
            message = Message(None, None, None, message)
            message_header = message.get_header()
            
            if message_header == Header.PING and src_addr[0] == self.server_host:
                self.reply_ping_message(recv_socket)
            elif message_header == Header.DISCOVER and src_addr[0] == self.server_host:
                self.reply_discover_message(recv_socket)
            elif message_header == Header.RETRIEVE:
                self.__preprocess_file_transfer__(recv_socket, message.get_info())
        except Exception as e:
            print(f"An error occurred in listen: {e}")
        finally:
            recv_socket.close()
    
    def send_message(self, message:Message, sock:socket.socket):
        """
        Send an encoded message to an existing socket
        Parameters:
        - message: Message to be sent
        - sock: Socket to which the message is sent
        
        Return: True if the message sent successfully, False otherwise
        """
        encoded_msg = json.dumps(message.get_packet()).encode()
        dest = 'server' if sock.getpeername()[0] == self.server_host else sock.getpeername()[0]
        
        try:
            sock.sendall(encoded_msg)
            print(f"Send a {message.get_header().name} - {message.get_type().name} message to {dest}")
            res = True
        except:
            print(f"An error occurred while sending a {message.get_header().name} message to {dest}")
            res = False
        
        return res
    
    def notify_message(self, message:Message, src):
        """
        Send an info string about the received message
        
        Parameters:
        - message: The message to see info
        - src: The source IP address
        
        Returns: (str) The info string
        """
        src = 'server' if src == self.server_host else src
        return f"Receive a {message.get_header().name} - {message.get_type().name} message from {src}"
    
    def register(self):
        """
        Client registers its hostname and password to the server
        
        Parameters: None
        
        Return: Response message from the server
        """
        # Request to register
        request = Message(Header.REGISTER, Type.REQUEST, {"hostname": self.client_hostname, "password": self.client_password})
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'SERVER_CONNECT_ERROR'
        self.send_message(request, tmp_sock)
        # Receive register response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        # Process the response
        response = Message(None, None, None, response)
        return response.get_info() # OK/DUPLICATE
    
    def log_in(self):
        """
        Client logs in to server to participate in the network and exchange information
        
        Parameters: None
        
        Return: Response message from the server
        """
        # Send login request
        request = Message(Header.LOG_IN, Type.REQUEST, {"hostname": self.client_hostname, "password": self.client_password})
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'SERVER_CONNECT_ERROR'
        self.send_message(request, tmp_sock)
        # Receive login response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        # Process the response
        response = Message(None, None, None, response)
        result = response.get_info()
        if result == 'OK':
            self.login_succeeded = True
        else: # HOSTNAME/PASSWORD/AUTHENTIC
            self.login_succeeded = False
        return result
    
    def log_out(self):
        """
        Client logs out of server
        
        Parameters: None
        
        Return: Response message from the server
        """
        # Send logout request
        if not self.is_login():
            return
        request = Message(Header.LOG_OUT, Type.REQUEST, None)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'SERVER_CONNECT_ERROR'
        self.send_message(request, tmp_sock)
        # Receive logout response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        # Process the response
        response = Message(None, None, None, response)
        result = response.get_info()
        if result == 'OK':
            self.login_succeeded = False
        return result
    
    def reply_discover_message(self, sock):
        """
        Receive discover message from the server
        """
        response = Message(Header.DISCOVER, Type.RESPONSE, self.published_files)
        self.send_message(response, sock)
    
    def reply_ping_message(self, sock):
        """
        Receive ping message from the server
        """
        response = Message(Header.PING, Type.RESPONSE, 'PONG')
        self.send_message(response, sock)
    
    def publish(self, lname, fname):
        """
        A local file (which is stored in the client's file system at lname) is added to the client's repository as a file named fname and this information is conveyed to the server.
        
        Parameters:
        - lname: The path to the file in local file system
        - fname: The file to be uploaded and published in the repository
        
        Return: Response message from the server
        """
        # Send publish request
        request = Message(Header.PUBLISH, Type.REQUEST, {'fname': fname, 'lname': lname})
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'SERVER_CONNECT_ERROR'
        self.send_message(request, tmp_sock)
        # Receive publish response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        # Process the response
        response = Message(None, None, None, response)
        # self.notify_message(response, self.server_host)
        info = response.get_info()
        result = info['result']
        # Publish failed, do not add file to repository (ERROR)
        if result == "ERROR":
            return result
        # Add file to repository (OK/DUPLICATE)
        self.published_files[fname] = lname
        with open("published_file.json", "w") as fp:
            json.dump(self.published_files, fp, indent=4)
        return result
    
    def fetch(self, fname):
        """
        Fetch some copy of the target file and add it to the local repository.
        First, request from the centralized server the list of online hosts having the given file fname.
        The list is then sent to the UI for the client to choose its peer
        
        Parameters:
        - fname: The file to be downloaded
        
        Return: List of IP addresses of the available peers requested from server, otherwise 'NO_AVAILABLE_HOST'
        """
        ### 
        # Request server
        request = Message(Header.FETCH, Type.REQUEST, fname)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tmp_sock.connect((self.server_host, self.server_port))
        except:
            return 'SERVER_CONNECT_ERROR'
        self.send_message(request, tmp_sock)
        # Server's response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        # Process the response
        response = Message(None, None, None, response)
        # self.notify_message(response, self.server_host)
        host_list = response.get_info()['avail_ips']
        if not host_list:
            return 'NO_AVAILABLE_HOST'
        return host_list
    
    def retrieve(self, fname, host):
        """
        After a peer is chosen, reach a peer to ask for downloading file. If reachable, establish an 
        FTP connection to the host server and retrieve the file. Otherwise, return and try other peers.
        
        Parameters:
        - fname: the file name
        - host: client's IP address to connect
        
        Return: 'UNREACHABLE' if host is unreachable, 'DENIED' if host refused to send the file fname, or 
        the file path in which the file was saved if retrieved successfully
        """
        # Ask that host to download the file
        request = Message(Header.RETRIEVE, Type.REQUEST, fname)
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmp_sock.settimeout(5)
        try:
            tmp_sock.connect((host, 5001))
        except:
            return 'UNREACHABLE'
        
        # If request cannot be sent, return
        if not self.send_message(request, tmp_sock):
            tmp_sock.close()
            return 'UNREACHABLE'
        
        # Receive the response
        response = tmp_sock.recv(2048).decode()
        tmp_sock.close()
        
        # Process the response
        response = Message(None, None, None, response)
        result = response.get_info()
        # Check if it accepts or refuses to send the file. If DENIED, try other hosts
        if result == 'DENIED':
            return result
        
        # If it has accepted, proceed file transfering using FTP
        dest_dir, dest_file = "download/", fname
        # Handle non-existing download directory
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
        
        i = 0
        # Handle existing files
        while os.path.exists(dest_dir + dest_file):
            i += 1
            dest_file = f"Copy_{i}_" + fname
        
        # File transfer protocol begins
        ftp = FTP(host)
        ftp.log_in('mmt', 'hk231')
        with open(dest_dir + dest_file, 'wb') as fp:
            ftp.retrbinary(f'RETR {fname}', fp.write)
        
        ftp.quit()
        # File transfer protocol ends
        
        # Publish file
        self.publish(os.path.abspath(dest_dir + dest_file).replace('\\', '/'), fname)
        return 'OK'
    
    def is_login(self):
        return self.login_succeeded
    
    def get_fname(self):
        return list(self.published_files.keys())
    
    def __preprocess_file_transfer__(self, sock, fname):
        if fname in self.published_files:
            result = 'DENIED'
        else:
            self.__check_cached__(fname)
            result = 'OK'
        response = Message(Header.RETRIEVE, Type.RESPONSE, result)
        self.send_message(response, sock)
    
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
    
    # FTP server on another thread
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