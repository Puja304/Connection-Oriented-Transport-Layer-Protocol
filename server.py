import socket

def custom_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   #establishes it as a UDP socket
    server_socket.bind(("127.0.0.1", 8000))                          #binds it to our local host
    print("Server is listening")

    while True:
        data, addr = server_socket.recvfrom(1024) #receive data 
        print(f"Received {data.decode()} from {addr}")
        server_socket.sendto("ACK".encode(), addr)




custom_socket()