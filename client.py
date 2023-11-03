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
    def __init__(self, server_host, server_port):
        """
        Constructor: Initializes attributes, to be added more
        """
        # Store information of the centralized server
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Store information of the client
        self.client_hostname = socket.gethostname()
        self.client_host = socket.gethostbyname(socket.gethostname())
        self.client_port = 5001
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.published_files = {}
        if not os.path.exists("published_file.json"):
            with open("published_file.json", "w") as fp:
                pass
        with open("published_file.json", "r") as fp:
            self.published_files = json.load(fp)
        self.ftp_server = None # To be initialized only once per lifetime
        self.message_queue = [] # Synchronized message queue
        self.mutex_queue = Lock()
        self.isRunning = True
        self.isFTPRunning = False
        self.t: list[Thread] = []
    
    def connect(self):
        """
        Establish connection with server and join the P2P network
        
        Return: None
        """
        self.listen_socket.bind((self.client_host, self.client_port))
        try:
            # self.client_socket.connect((self.server_host, self.server_port))
            print("Start running!")
        except Exception as e:
            print(f"An error occurred: {e}")
        # A thread for FTP server -> FTPServerSide class, to be added here instead of down there
        
        # A thread for processing ping requests
        # self.t.append(Thread(target=self.receive_ping_message))
        # A thread for preprocessing file transfers
        # self.t.append(Thread(target=self.preprocess_file_transfer))
        # A thread for listening incoming messages
        self.t.append(Thread(target=self.listen))
        
        self.t[0].start()
        # self.t[1].start()
        # self.t[2].start()
        # self.t[3].start()
    
    def listen(self):
        print("Start listening")
        self.listen_socket.listen()
        while True:
            try:
                recv_socket, src_addr = self.listen_socket.accept()
                new_thread = Thread(target=self.handle_incoming_connection, args=(recv_socket, src_addr))
                new_thread.start()
            except:
                print("Stop accepting connection")
                break
    
    def handle_incoming_connection(self, recv_socket, src_addr):
        try:
            recv_socket.settimeout(10)
            message = recv_socket.recv(2048).decode()
            print("Received sth")
            message = Message(None, None, None, message)
            message_header = message.get_header()
            message_info = message.get_info()
            
            if message_header == Header.PING and src_addr == self.server_host:
                self.reply_ping_message(message, recv_socket)
            elif message_header == Header.PUBLISH:
                self.respond_publish(message)
            # with self.mutex_queue:
            #     self.message_queue.append(message)
        except Exception as e:
            print(f"An error occurred in listen: {e}")
        finally:
            recv_socket.close()
    
    def disconnect(self):
        """
        Disconnect from the server and network and stop running
        
        Return: None
        """
        self.listen_socket.close()
        # try:
        #     self.stop_ftp_server()
        # except Exception as e:
        #     print(f"Disconnect FTP server forbidden: {e}")
        # self.isRunning = False
        # message = Message(Header.END_CONNECTION, Type.REQUEST, None)
        # self.send_message(message, self.server_host, self.server_port)
        # time.sleep(1)
        # self.client_socket.close()
        # for thread in self.t:
        #     thread.join()
    
    def send_message(self, message:Message, dest_ip, dest_port=5000, existed_socket=None):
        """
        Send encoded message to server
        """
        encoded_msg = json.dumps(message.get_packet()).encode()
        if existed_socket == None:
            tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                tmp_sock.connect((dest_ip, dest_port))
                tmp_sock.sendall(encoded_msg)
            except:
                print(f"An error occurred while sending a {message.get_header()} message to {dest_ip}")
            finally:
                tmp_sock.close()
        else:
            existed_socket.sendall(encoded_msg)
    
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
                            self.send_message(response, self.client_socket)
                time.sleep(2)
        except Exception as e:
            print(f"An error occurred in preprocess: {e}")
        finally:
            print("Thread preprocess finished successfully")
    
    def reply_ping_message(self, message, sock):
        """
        Receive ping message from the server
        """
        print("Receive ping from server")
        response = Message(Header.PING, Type.RESPONSE, 'PONG')
        self.send_message(response, self.server_host, 5000, sock)
        sock.close()
    
    def reply_discover_message(self, message, sock):
        """
        Receive discover message from the server
        """
        print("Receive discover from server")
        response = Message(Header.PING, Type.RESPONSE, '')
        self.send_message(response, self.server_host, 5000, sock)
        sock.close()
    
    def initiate_ftp_server(self): # currently opcode 1, to be added in connect()/constructor
        """
        Allocate and establish the server for FTP connection
        
        Return: None
        """
        if isinstance(self.ftp_server, self.FTPServerSide) and self.isFTPRunning:
            return
        self.ftp_server = self.FTPServerSide(self.__check_cached__)
        self.ftp_server.start()
        self.isFTPRunning = True
    
    def stop_ftp_server(self): # currently opcode 3, to be added in disconnect()/destructor
        if not isinstance(self.ftp_server, self.FTPServerSide):
            raise Exception('Not an FTP server')
        if isinstance(self.ftp_server, self.FTPServerSide) and not self.isFTPRunning:
            return
        self.ftp_server.stop()
        self.ftp_server.join()
        self.isFTPRunning = False
    
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
    
    def respond_publish(self, message):
        info = message.get_info()
        fname, lname, result = info['fname'], info['lname'], info['result']
        if result != "ERROR":
            # Add file to repository
            self.published_files[fname] = lname
            with open("published_file.json", "w") as fp:
                json.dump(self.published_files, fp, indent=4)
            print("Publish succeded!")
        else:
            print("Publish failed")
        return result

    def publish(self, lname, fname):
        """
        A local file (which is stored in the client's file system at lname) is added to the client's repository as a file named fname and this information is conveyed to the server.
        
        Parameters:
        - lname: The path to the file in local file system
        - fname: The file to be uploaded and published in the repository
        
        Return: None
        """
        # Send message to server
        request = Message(Header.PUBLISH, Type.REQUEST, {'fname': fname, 'lname': lname})
        self.send_message(request, self.server_host, self.server_port)
    
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
        self.send_message(request, self.client_socket)
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
        self.send_message(request, self.client_socket)
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
        cached_dir = "cache/"
        if not os.path.exists(cached_dir):
            os.mkdir(cached_dir)
        if fname and fname in self.published_files:
            filepath = cached_dir + fname
            if not os.path.exists(filepath):
                shutil.copy2(self.published_files[fname], cached_dir + fname)
    
    #  FTP server on another thread
    class FTPServerSide(Thread):
        def __init__(self, check_cache):
            Thread.__init__(self)
            self.check_cache = check_cache
        
        def run(self):
            # Initialize FTP server
            authorizer = DummyAuthorizer()
            self.check_cache(None)
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
    client = Client('192.168.57.244', 5000)
    client.connect()
    # print(client.publish('D:/Quan/Đề tham khảo các môn chính trị/de-thi-lich-su-dang-hk211-truong-dai-hoc-bach-khoa-dhqg-hcm.pdf', 'de-thi-lsd.pdf'))
    # client.publish('fffffff', 'text.txt')
    # while True:
    #     tmp = input('Choose opcode: ')
    #     if tmp == '1':
    #         client.initiate_ftp_server()
    #     elif tmp == '2':
    #         client.fetch('file3.mp4')
    #     elif tmp == '3':
    #         try:
    #             client.stop_ftp_server()
    #         except Exception as e:
    #             print(f"Disconnect FTP server forbidden: {e}")
    #     else:
    #         print("Stop")
    #         break
    time.sleep(10)
    client.disconnect()

if __name__ == '__main__':
    main()