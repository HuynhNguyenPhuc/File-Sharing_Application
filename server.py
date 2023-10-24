import socket

class Server(object):
    def __init__(self):
        return

    def send_location_file_message(owner_file , client_request):
        """
        This function will send back the location of file the 'client_request' request, which is the 'owner_file'

        Parameters
        - owner_file: the hostname of client who has the file requested
        - client_request: the address of the client who request the file
        """

    def send_client_file(client_request, client_target_hostname):
        """
        This function will send back list of files that 'client_target' has

        Parameters
        - client_request: the address of client who request to know files 'client_target' has
        - client_target_hostname: the hostname of target client to know what files he/she has
        """

    def client_live_check(client_target_address):
        """
        This function check whether a hostname is alive

        Parameters
        - client_target_address: the address of client need to be checked
        """
        
    def add_up_client(client_address, client_hostname):
        """
        This function add a new client to client's table

        Parameters
        - client_address: IP address of the new client
        - client_hostname: hostname of the new client
        """
        
    def add_file_client(client_address, file_name):
        """
        This function add a file a client has to client's table

        Parameters
        - client_address: address of client
        - file_name: name of the new file
        """
    
        
        
