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
    def __init__(self, server_host, server_port):
        """
        Constructor: Initializes attributes, to be added more
        """
        # Store information of the centralized server
        self.server_host = server_host
        self.server_port = server_port
        self.socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Store information of the client
        self.client_host = socket.gethostbyname(socket.gethostname())
        self.published_files = []
        self.ftp_server = None
        
        logging.basicConfig(filename='tmp.log', level=logging.INFO)
    
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
        pass

    def fetch(self, fname):
        """
        fetch some copy of the target file and add it to the local repository

        Parameters:
        - fname: The file to be downloaded

        Return: None
        """
        pass
        
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
    obj = Client('localhost', 12345)
    while True:
        tmp = input('Choose opcode: ')
        if tmp == '1':
            obj.initiate_ftp_server()
        elif tmp == '2':
            # obj.inititate_ftp_client('localhost', '', 'D:/sample_data_for_computer_networks/test.txt')
            obj.inititate_ftp_client('localhost', '', '')
        elif tmp == '3':
            obj.stop_ftp_server()
        else:
            print("Stop")
            break

if __name__ == '__main__':
    main()