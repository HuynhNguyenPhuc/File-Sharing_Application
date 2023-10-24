import socket
import threading
from ftplib import FTP, FTP_TLS
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
import logging
import time

class Client:
    def __init__(self, server_host, server_port):
        """
        Constructor: Initializes attributes
        To be added more (I don't know)
        """
        # Initialize server information
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.published_files = []

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

        logging.basicConfig(filename='tmp.log', level=logging.INFO) # log file
    
    
    def connect(self):
        """
        Register server to join the P2P network

        Return: None
        """
        pass

    def disconnect(self):
        """
        Disconnect from the P2P network
        """

    def ftp_server(self):
        """
        Allocate and establish the server for FTP connection

        Return: None
        """
        pass

    def ftp_client(self, host='localhost'):
        """
        Establish an FTP connection to the host server

        Parameters:
        - host: client's IP address to connect

        Return: None
        """
        pass

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

    # These are for testing purposes of the libraries, do not use them
    def testFTPClient(self, host='localhost', dir='.', fname='test.txt'):
        ftp = FTP(host)  # connect to host, default port
        ftp.login()
        filepath = dir + '/' + fname
        
        with open('README', 'wb') as fp:
            ftp.retrbinary(f'RETR {filepath}', fp.write)
        
        ftp.quit()

    def FTP_serve__(self):
        thread1 = threading.Thread(target=self.server.serve_forever)
        thread1.start()
        # time.sleep(5)
        # print(1)

    def FTP_shutdown__(self):
        self.server.close_all()

def main():
    obj = Client('localhost', 12345)
    while True:
        tmp = input('Choose opcode: ')
        if tmp == '1':
            obj.FTP_serve__()
        elif tmp == '2':
            obj.FTP_shutdown__()
        elif tmp == '3':
            obj.testFTPClient()
        else:
            break

if __name__ == '__main__':
    main()