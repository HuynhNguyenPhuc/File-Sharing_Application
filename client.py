import socket
import threading
from ftplib import FTP, FTP_TLS
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
import logging
import time
# class MyHandler(FTPHandler):
#     def __init__(self):
#         FTPHandler.__init__(self)
#     def on_file_sent(self, file):
#         try:
#             time.sleep(5)
#             self.server.close_all()
#             super().on_file_sent(file)
#         except:
#             print("Not closed")
class Client:
    def __init__(self, client_hostname, server_host, server_port):
        """
        Constructor: Initializes attributes, to be added more
        """
        # Store information of the centralized server
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Store information of the client
        self.client_hostname = client_hostname
        self.client_host = socket.gethostbyname(socket.gethostname())
        self.published_files = {}
        self.ftp_server = None

        logging.basicConfig(filename='tmp.log', level=logging.INFO)

    def connect_to_tcp_server(self):
        """

        Connect to the TCP server

        """
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print("Sucessfully Connected!")
            self.send_message_to_server(f'register {self.client_hostname}')
        
        except Exception as e:
            print(f"An error occurred: {e}")

    def disconnect_to_tcp_server(self):
        """
        
        Disconnect to the TCP server

        """
        self.client_socket.close()

    def send_message_to_server(self, message):
        """
        
        Send encoded messgae to server
        
        """
        self.client_socket.send(message.encode())

    def receive_ping_message(self):
        """

        Receive ping message from the server

        """
        try:
            data = self.client_socket.recv(2048)
            if data:
                print(f"Ping message: {data.decode()}")
                self.send_message_to_server("Sucessfully received!")

        except Exception as e:
            print(f"An error occurred: {e}")
    
    def connect(self):
        """
        Register server to join the P2P network

        Return: None
        """
        pass

    def disconnect(self):
        """
        Disconnect from the P2P network

        Return: None
        """

    def initiate_ftp_server(self): # currently opcode 1
        """
        Allocate and establish the server for FTP connection

        Return: None
        """
        if self.ftp_server:
            raise Exception('FTP server already on')
        self.ftp_server = self.FTPServerSide()
        self.ftp_server.start()

    def stop_ftp_server(self): # currently opcode 3
        if not isinstance(self.ftp_server, self.FTPServerSide):
            raise Exception('Not a server')
        self.ftp_server.stop()
        self.ftp_server = None

    def inititate_ftp_client(self, host='localhost', dir='.', fname='test.txt'): # currently opcode 2
        """
        Establish an FTP connection to the host server

        Parameters:
        - host: client's IP address to connect
        - dir: directory to connect to fname on server
        - fname: the file name

        Return: None
        """
        ftp = FTP(host)  # connect to host, default port
        ftp.login()
        filepath = fname
        if dir != '.':
            filepath = dir + '/' + filepath
        x = ''
        with open('taken', 'wb') as fp:
            ftp.retrbinary(f'RETR /sample_data_for_computer_networks/test.mp4', fp.write)
        
        ftp.quit()

    def publish(self, lname, fname):
        """
        A local file (which is stored in the client's file system at lname) is added to the client's repository as a file named fname and this information is conveyed to the server.

        Parameters:
        - lname: The path to the file in local file system
        - fname: The file to be uploaded and published in the repository

        Return: None
        """
        # Add file to repository
        self.published_files[fname] = lname

        # Send message to server 
        self.send_message_to_server(f'publish {fname}')
        while True:
            response = self.client_socket.recv(2048)
            if response:
                print(response)
                break
            time.sleep(1)

    def fetch(self, fname):
        """
        fetch some copy of the target file and add it to the local repository

        Parameters:
        - fname: The file to be downloaded

        Return: None
        """
        data = None

        self.send_message_to_server('fetch ' + fname)

        while True:
            data = self.client_socket.recv(2048)
            if data:
                print(data)
                break
            time.sleep(1)
        return
        
    # Dự phòng
    def __request_server__(self, fname):
        """
        Request from the centralized server the list of hosts having the given file fname

        Parameters:
        - fname: The file to be requested from the server

        Returns: (List) A list of hosts possessing the file fname
        """
        pass
    
    def __transfer_file__(self):
        """
        To be used to transfer file, not yet defined
        """
        pass

    # FTP server on another thread
    class FTPServerSide(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            
        def run(self):
            # Initialize FTP server
            authorizer = DummyAuthorizer()
            authorizer.add_user('user', '54321', '.', perm='rl')
            authorizer.add_anonymous('.', perm='rl')
            handler = FTPHandler
            handler.authorizer = authorizer
            handler.banner = "Connection Success"
            # handler.masquerade_address = '171.227.71.146' # external IP address
            # handler.passive_ports = range(60000, 65535)

            self.server = ThreadedFTPServer(('0.0.0.0', 21), handler)
            self.server.max_cons = 256
            self.server.max_cons_per_ip = 5
            self.server.serve_forever()

        def stop(self):
            self.server.close_all()


def main():
    # obj = Client('localhost', 12345)
    # while True:
    #     tmp = input('Choose opcode: ')
    #     if tmp == '1':
    #         obj.initiate_ftp_server()
    #     elif tmp == '2':
    #         # obj.inititate_ftp_client('localhost', '', 'D:/sample_data_for_computer_networks/test.txt')
    #         obj.inititate_ftp_client('localhost', '', '')
    #     elif tmp == '3':
    #         obj.stop_ftp_server()
    #     else:
    #         print("Stop")
    #         break
    client = Client('nguyenphuc', '10.230.143.196', 5000)
    client.connect_to_tcp_server()
    time.sleep(5)
    client.publish('fffffff', 'text.txt')
    # print(client.client_host)


if __name__ == '__main__':
    main()