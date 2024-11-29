import socket

class ReliableTransportLayerProtocolHeader:

    # will have the following fields
    def __init__(self,source_port_num, dest_port_num, seq_num, ack_num, receiver_window, app_data= "", syn = False, ack = False, fin = False):
        self.source_port_num = source_port_num
        self.dest_port_num = dest_port_num
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.receiver_window = receiver_window
        self.syn = syn
        self.ack = ack
        self.fin = fin
        self.app_data = app_data

    def to_bytes(self):
        flags = self.syn << 2 | self.ack << 1 | self.fin     #a single byte to represent all flags
        # all fields seperated with a comma, and a delimmiter | used to separate the actual data from the header
        header = f"{self.source_port_num} , {self.dest_port_num}, {self.seq_num}, {self.ack_num}, {self.receiver_window},{flags}|{self.app_data}"
        return header.encode('utf-8')
    
    @staticmethod
    # is a static method so we can decode a header without already having a transport header before
    def from_bytes(data):
        # the decoded date
        decoded_header = data.decode('utf-8')
        # split into header and the actual application data
        header,payload = decoded_header.split('|')

        # extracting all header fields, seperated by commans
        source_port_num, dest_port_num, seq_num, ack_num, receiver_window, flags = map(int, header.split(','))

        #extracting the flag bits
        syn,ack,fin = (flags & 4) >> 2, (flags & 2) >> 1, (flags & 1)

        #turn it all into a new header and return it:
        return ReliableTransportLayerProtocolHeader(syn = syn, ack = ack, fin=fin, source_port_num=source_port_num, dest_port_num=dest_port_num, seq_num=seq_num, ack_num=ack_num, receiver_window=receiver_window, app_data=payload)
    

        