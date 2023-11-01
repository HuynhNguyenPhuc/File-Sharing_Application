from client import *


client = Client('minhquan', '192.168.1.9', 5000)

client.connect()

client.publish('fffffff', 'text.txt')

# client.fetch('file1.txt')

client.isRunning = False
client.disconnect()
