import socket

class Server(object):
    def __init__(self):
        return

    def response(self, address, message):
        """
        This function is used to send response message to requested client

        Parameter:
        - address: address of requested client
        - message: string type, response message
        """
        
    def register(self, hostname, address):
        """ 
        This function is used to add a new client to the table when there is a register request

        Return:
        - Boolean: True if register success
        
        Parameter:
        - hostname: Name of new client
        - address: IP address of new client
        """

    def ping(self, hostname):
        """
        This function is used to check whether a client is alive

        Return:
        - Boolean: True if the server is alive, otherwise False
        """

    def discover(self, hostname):
        """
        This function is used to discover the list of local files of the host named hostname

        Return:
        - List: List of file of the host
        
        Parameter:
        - hostname: name of the target host
        """

    def find(self, filename)
        """
        This function is used to discover the clients who store the requested file

        Return:
        - List: List of hostnames having the requested file

        Parameter:
        - filename: name of requested file
        """

    
        
        
