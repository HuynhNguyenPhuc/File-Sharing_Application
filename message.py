from enum import Enum
class Type(Enum):
    SEND = 0
    RECEIVE = 1

class Header(Enum):
    PING = 0
    DISCOVER = 1
    PUBLISH = 2
    FETCH = 3
    TAKE_HOST_LIST = 4
    RETRIEVE_REQUEST = 5
    RETRIEVE_PROCEED = 6

class Message:
    def __init__(self, header, type, info):
        self._header = header
        self._type = type
        self._info = info
    
    def get_header(self):
        return self._header
    
    def get_type(self):
        return self._type
    
    def get_info(self):
        return self._info
    
    def get_packet(self):
        return self.__dict__