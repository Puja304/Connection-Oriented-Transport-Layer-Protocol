import socket

def custom_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   #establishes it as a UDP socket
    server_socket.bind(("127.0.0.1", 8000))                          #binds it to our local host
    print("Server is listening")

    while True:
        establish_connection(server_socket)
        data, addr = server_socket.recvfrom(1024)
        print(f"Received {data.decode()} from {addr}")
        
def establish_connection(server_socket):
    data, addr = server_socket.recvfrom(1024)
    if data == b"SYN":
        server_socket.sendto(b"SYN-ACK", addr)
        ack, _ = server_socket.recvfrom(1024)
        if ack == b"ACK":
            print("Connection Established")
        
custom_socket()
