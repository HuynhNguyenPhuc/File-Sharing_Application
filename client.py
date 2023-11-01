import socket
from threading import Thread, Lock
from ftplib import FTP, FTP_TLS
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from message import Message, Type, Header
import os
import shutil
import json
import time

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
        self.published_files = {"file1.txt": "D:/Quan/testftp/test.txt", "file2.mp4": "D:/Quan/testftp/sample-30s.mp4", "file3.mp4": "D:/Quan/testftp/round_robin.mp4", "file4.xlsx": "D:/Quan/testftp/Book1.xlsx"}
        self.ftp_server = None # To be initialized only once per lifetime
        self.message_queue = [] # Synchronized message queue
        self.mutex_queue = Lock()
        self.isRunning = True
        self.t: list[Thread] = []
    
    def connect(self):
        """
        Connect to establish connection with server and join the P2P network
        
        Return: None
        """
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print("Sucessfully Connected!")
        except Exception as e:
            print(f"An error occurred: {e}")
        # A thread for FTP server -> FTPServerSide class, to be added here instead of down there
        # A thread for receiving messages and add to the queue
        self.t.append(Thread(target=self.listen))
        # A thread for processing ping requests
        self.t.append(Thread(target=self.receive_ping_message))
        # A thread for preprocessing file transfers
        self.t.append(Thread(target=self.preprocess_file_transfer))
        
        self.t[0].start()
        self.t[1].start()
        self.t[2].start()
    
    def disconnect(self):
        """
        Disconnect from the server and network
        
        Return: None
        """
        message = Message(Header.END_CONNECTION, Type.REQUEST, None)
        self.send_message_to_server(message)
        time.sleep(1)
        self.client_socket.close()
        for thread in self.t:
            thread.join()
    
    def send_message_to_server(self, message: Message):
        """
        Send encoded message to server
        """
        self.client_socket.send(json.dumps(message.get_packet()).encode())
    
    def listen(self):
        try:
            while self.isRunning:
                message = self.client_socket.recv(2048).decode()
                if not message:
                    break
                message = Message(None, None, None, message)
                with self.mutex_queue:
                    self.message_queue.append(message)
        except Exception as e:
            print(f"An error occurred in listen: {e}")
        finally:
            print("Thread listen finished successfully")
    
    def preprocess_file_transfer(self):
        try:
            while self.isRunning:
                with self.mutex_queue:
                    for message in self.message_queue:
                        if message.get_header() == Header.RETRIEVE_REQUEST:
                            self.message_queue.remove(message)
                            fname = message.get_info()[1]
                            self.__check_cached__(fname)
                            response = Message(Header.RETRIEVE_PROCEED, Type.REQUEST, None)
                            self.send_message_to_server(response)
                time.sleep(2)
        except Exception as e:
            print(f"An error occurred in preprocess: {e}")
        finally:
            print("Thread preprocess finished successfully")
    
    def receive_ping_message(self):
        """
        Receive ping message from the server
        """
        try:
            while self.isRunning:
                with self.mutex_queue:
                    for message in self.message_queue:
                        if message.get_header() == Header.PING:
                            self.message_queue.remove(message)
                            print("Ping from server")
                            response = Message(Header.PING, Type.REQUEST, "Success")
                            self.send_message_to_server(response)
                time.sleep(1)
        except Exception as e:
            print(f"An error occurred in receive ping: {e}")
        finally:
            print("Thread receive ping finished successfully")
    
    def initiate_ftp_server(self): # currently opcode 1, to be added in connect()/constructor
        """
        Allocate and establish the server for FTP connection
        
        Return: None
        """
        if self.ftp_server:
            raise Exception('FTP server already on')
        self.ftp_server = self.FTPServerSide()
        self.ftp_server.start()
    
    def stop_ftp_server(self): # currently opcode 3, to be added in disconnect()/destructor
        if not isinstance(self.ftp_server, self.FTPServerSide):
            raise Exception('Not a server')
        self.ftp_server.stop()
        self.ftp_server = None
    
    def retrieve(self, fname='file1.txt', host='localhost'):
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
        # Send message to server
        request = Message(Header.PUBLISH, Type.REQUEST, {fname: lname})
        self.send_message_to_server(request)
        try:
            while True:
                flag = False
                with self.mutex_queue:
                    for message in self.message_queue:
                        if message.get_header() == Header.PUBLISH:
                            self.message_queue.remove(message)
                            if message.get_info() == "OK":
                                # Add file to repository
                                self.published_files[fname] = lname
                                print("Publish succeded!")
                            else:
                                print("Publish failed")
                            flag = True
                            break
                if flag:
                    break
                time.sleep(1)
        except Exception as e:
            print(f"An error occurred in receive ping: {e}")
    
    def fetch(self, fname):
        """
        Fetch some copy of the target file and add it to the local repository
        
        Parameters:
        - fname: The file to be downloaded
        
        Return: None
        """
        hosts_list = self.__request_server__(fname)
        # Choose host to download file from
        if not hosts_list:
            print("No available host")
            return
        hostname, hostip = hosts_list[0]
        print(f"-----Request from host {hostname}-----")
        request = Message(Header.RETRIEVE_REQUEST, Type.REQUEST, [hostip, fname])
        self.send_message_to_server(request)
        while True:
            flag = False
            with self.mutex_queue:
                for message in self.message_queue:
                    if message.get_header() == Header.RETRIEVE_PROCEED:
                        self.message_queue.remove(message)
                        flag = True
                        break
            if flag:
                break
            time.sleep(1)
        self.retrieve(fname, hostip)
        # Add file to local repository with publish
        
    def __request_server__(self, fname):
        """
        Request from the centralized server the list of hosts having the given file fname
        
        Parameters:
        - fname: The file to be requested from the server
        
        Returns: (List) A list of hosts possessing the file fname
        """
        request = Message(Header.TAKE_HOST_LIST, Type.REQUEST, fname)
        self.send_message_to_server(request)
        hosts_list = None
        while True:
            flag = False
            with self.mutex_queue:
                for message in self.message_queue:
                    if message.get_header() == Header.TAKE_HOST_LIST:
                        self.message_queue.remove(message)
                        hosts_list = message.get_info()
                        flag = True
                        break
            if flag:
                break
            time.sleep(1)
        return hosts_list
    
    def __check_cached__(self, fname):
        """
        Add the file fname to the cache directory if not already cached
        
        Parameters:
        - fname: The name of the file
        
        Returns: None
        """
        filepath = "cache/" + fname
        if not os.path.exists(filepath):
            shutil.copy2(self.published_files[fname], "cache/" + fname)
    
    #  FTP server on another thread
    class FTPServerSide(Thread):
        def __init__(self):
            Thread.__init__(self)
        
        def run(self):
            # Initialize FTP server
            authorizer = DummyAuthorizer()
            authorizer.add_user('mmt', 'hk231', './cache', perm='rl')
            handler = FTPHandler
            handler.authorizer = authorizer
            handler.banner = "Connection Success"
            
            self.server = ThreadedFTPServer(('192.168.1.5', 21), handler)
            self.server.max_cons = 256
            self.server.max_cons_per_ip = 5
            
            self.server.serve_forever()
        
        def stop(self):
            self.server.close_all()

def main():
    client = Client('minhquan', '192.168.43.244', 5000)
    client.connect()
    time.sleep(2)
    client.publish('fffffff', 'text.txt')
    # while True:
    #     tmp = input('Choose opcode: ')
    #     if tmp == '1':
    #         client.initiate_ftp_server()
    #     elif tmp == '2':
    #         client.fetch('file3.mp4')
    #     elif tmp == '3':
    #         client.stop_ftp_server()
    #     else:
    #         print("Stop")
    #         break
    # client.isRunning = False
    # client.disconnect()

if __name__ == '__main__':
    main()