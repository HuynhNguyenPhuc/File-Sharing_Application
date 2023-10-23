import socket
import threading
from ftplib import FTP, FTP_TLS
from pyftpdlib import server

# To be changed in the future (very soon), please do not rely heavily on this blueprint.
# Discuss more with the author.
# C'est mon anniversaire aujourd'hui.
# 今日は私の誕生日です。
# Kyō wa watashi no tanjōbidesu.

class Client:
    def __init__(self, server_host, server_port):
        """
        Constructor: Initializes attributes
        To be added more (I don't know)
        """
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.published_files = []

    # def __join_network__(self):
    #     try:
    #         pass
    #     except:
    #         pass
    
    
    
    def connectServer(self):
        """
        Establish a TCP connection to the centralized server
        """
        pass
    
    def __requestServer__(self, fname):
        """
        Request from the server the list of hosts having the given file fname

        Parameters:
        - fname: The file to be requested from the server

        Returns: (List) A list of hosts possessing the file fname
        """
        pass
    
    def connectClient(self):
        """
        """
        pass
    
    def transferFile(self):
        pass

    def __upload_file__(self, lname, fname):
        """
        A local file (which is stored in the client's file system at lname) is added to the client's repository as a file named fname and this information is conveyed to the server.

        Parameters:
        - lname: The path to the file in local file system
        - fname: The file to be uploaded and published in the repository

        Return: None
        """
        pass

    def __download_file__(self, fname):
        """
        fetch some copy of the target file and add it to the local repository

        Parameters:
        - fname: The file to be downloaded

        Return: None
        """
        pass

    def publish(self, lname, fname):
        return self.__upload_file__(lname, fname)

    def fetch(self, fname):
        return self.__download_file__(fname)

    def __testFTPClient(self):
        ftp = FTP('ftp.us.debian.org')  # connect to host, default port
        ftp.login()                     # user anonymous, passwd anonymous@
        # ftp.cwd('debian')               # change into "debian" directory
        ftp.retrlines('LIST')           # list directory contents
        with open('README', 'wb') as fp:
            ftp.retrbinary('RETR /debian/doc/bug-log-access.txt', fp.write)
        ftp.quit()


obj = Client('localhost', 12345)
obj.connectClient()
