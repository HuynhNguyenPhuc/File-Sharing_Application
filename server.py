import socket


class Server(object):
    def __init__(self):
        pass

    def discover(self, hostname):
        """
        This function is used to discover local files in host named hostname

        Parameters:
        - hostname (string): Name of host

        Returns:
        List: List of local files of the host

        """

    def ping(self, hostname):
        """
        This function is used to check live host named hostname

        Parameters:
        - hostname (string): Name of host

        Returns:
        Boolean: Whether that host is live or not

        """

    def listen(self):
        """
        This function is used to listen to the request of the clients

        Parametesrs:

        Returns:
        """

    def response(self):
        """
        This function is used to reponse to the request of the clients

        Parameters:

        Returns:
        """

    def broadcast(self, filename):
        """
        This function is used to broadcast asking one file from other clients

        Parameters:
        - filename (string): The name of file that requesting client searching for

        Returns:
        String: Address of client keeping that file
        """

    def register(self, hostname, address):
        """
        This function is used to register hosts to system

        Parameters:
        - hostname (string): Name of host
        - address (string): Address of host

        Returns:
        Boolean: Successful or not
        """
