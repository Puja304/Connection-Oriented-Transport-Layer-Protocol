import socket

def my_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ("127.0.0.1",8000)

    for i in range (5):
        message = f"Message {i}"
        client_socket.sendto(message.encode(), server_address)
        data,_ = client_socket.recvfrom(1024)
        print(f"Server response: {data.decode()}")

my_client()