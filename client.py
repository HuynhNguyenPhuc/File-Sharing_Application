import socket
from ftplib import FTP

class Client(object):

    def __init__(self):
        """

        Initiate for Client's object.
        
        Input Parameters:
        + host (string): The IP address of the client's device.
        + TCP_port (int): The port number of TCP protocol
        + FTP_port (int): The port number of FTP protocol
        
        + username (string): Username of the connection, used for security
        + password (string): Password of the connection, used for security

        Other Parameters:
        + ftp (FTP): Manage the FCP connection between two clients
        + tcp_socket (socket): Manage the TCP connection between client and server
        + repository (List):  A list of files' names and directories.

        """

    def tcp_connection(self):
        """

        Connect to the server using TCP/IP.

        """

    def ftp_connection(self):
        """

        Connect to the FTP server.

        """

    def upload_file(self):
        """

        Upload file to repository, used for 'publish' command.

        Parameters:
        + Iname: Directory of the file
        + fname: Name of the file

        """

    def download_file(self):
        """

        Download file to repository, used for 'fetch' command.

        Parameters:
        + fname: Name of the file

        """

    def tcp_disconnection(self):
        """

        Disconnect to the TCP server.

        """

    def ftp_disconnection(self):
        """

        Disconnect to the FTP server.

        """