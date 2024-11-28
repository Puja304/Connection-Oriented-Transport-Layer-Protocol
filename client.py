import socket

def my_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ("127.0.0.1",8000)
    establish_connection(client_socket, server_address)

    for i in range (5):
        message = f"Message {i}"
        client_socket.sendto(message.encode(), server_address)
        data,_ = client_socket.recvfrom(1024)
        print(f"Server response: {data.decode()}")

def establish_connection(client_socket, server_address):
    client_socket.sendto(b"SYN", server_address)
    response, _ = client_socket.recvfrom(1024)
    if response == b"SYN-ACK":
        client_socket.sendto(b"ACK", server_address)

my_client()