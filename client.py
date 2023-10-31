import socket
import threading
import os
import shutil
from ftplib import FTP, FTP_TLS
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
import logging
import time

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
        self.client_port = 55555
        self.published_files = {"file1.txt": "D:/Quan/testftp/test.txt", "file2.mp4": "D:/Quan/testftp/sample-30s.mp4", "file3.mp4": "D:/Quan/testftp/round_robin.mp4", "file4.xlsx": "D:/Quan/testftp/Book1.xlsx"}
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

    def retrieve(self, fname='file1.txt', host='localhost'): # currently opcode 2
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
        ftp.login('mmt', 'hk231')
        with open(dest_dir + dest_file, 'wb') as fp:
            ftp.retrbinary(f'RETR {fname}', fp.write)
        
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
    def check_cached(self, fname):
        filepath = "cache/" + fname
        if not os.path.exists(filepath):
            shutil.copy2(self.published_files[fname], "cache/" + fname)

    # FTP server on another thread
    class FTPServerSide(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            
        def run(self):
            # Initialize FTP server
            authorizer = DummyAuthorizer()
            authorizer.add_user('mmt', 'hk231', './cache', perm='rl')
            handler = FTPHandler
            handler.authorizer = authorizer
            handler.banner = "Connection Success"
            # handler.masquerade_address = '171.227.71.146' # external IP address
            # handler.passive_ports = range(60000, 65535)

            self.server = ThreadedFTPServer(('', 21), handler)
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
            for a in obj.published_files.keys():
                obj.check_cached(a)
        elif tmp == '2':
            # obj.inititate_ftp_client('localhost', '', 'D:/sample_data_for_computer_networks/test.txt')
            obj.retrieve()
        elif tmp == '3':
            obj.stop_ftp_server()
        elif tmp == '4':
            obj.check_cached("test.txt")
        else:
            print("Stop")
            break

if __name__ == '__main__':
    main()