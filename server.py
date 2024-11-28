import socket

def custom_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   #establishes it as a UDP socket
    server_socket.bind(("127.0.0.1", 8000))                          #binds it to our local host
    print("Server is listening")

    while True:
        data, addr = server_socket.recvfrom(1024) #receive data 
        print(f"Received {data.decode()} from {addr}")   #print it
        server_socket.sendto("ACK".encode(), addr)#

        if(receive a SYN = 1 message):
            select seqnum = 0 or 1 
            send SYNACK
                if receive ACK for synack:
                    ENTER ESTABLISHED STATE:
                    client_address = addr


window_szie = 5;


            

custom_socket()