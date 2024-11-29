import socket
from header import ReliableTransportLayerProtocolHeader

CLIENT_ADDRESS = ("127.0.0.1", 8001)

def my_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(CLIENT_ADDRESS)
    server_address = ("127.0.0.1",8000)

    # intialize the connection
    window_size = 5
    synBit = 1
    seq = 0
    message = ReliableTransportLayerProtocolHeader(CLIENT_ADDRESS[1], server_address[1], seq, 0, window_size, app_data=f"Please Connect With Me",syn=synBit, fin = 0, ack= 0)
    client_socket.sendto(message.to_bytes(), server_address)
    print("Initiated handshake, sent SYN request")
    
    #wait for ACK and read it once it is here. no need to store the server address every time!
    data,_ = client_socket.recvfrom(1024)
    received = ReliableTransportLayerProtocolHeader.from_bytes(data)
    if (received.syn & received.ack & received.ack_num == (seq + 1)):
        print("Received SYNACK")
        print(f"Received message : {received.app_data}")

        response = "Great, let's have a connection"
        ackNum = received.seq_num + 1
        seq += 1
        message = ReliableTransportLayerProtocolHeader(CLIENT_ADDRESS[1], server_address[1],seq,ackNum,window_size,app_data=response, syn = 0, fin=0, ack=1)
        client_socket.sendto(message.to_bytes(), server_address)
        print("Completed step 3 of the handshake. Now in the connnected state")

        while True:
            user_input = input("Enter message to send (or 'exit' to terminate)")

            if user_input.lower() == "exit":

                fin_packet = ReliableTransportLayerProtocolHeader(
                    CLIENT_ADDRESS[1], server_address[1], 
                    seq_num=seq, ack_num=received.seq_num + 1,
                    receiver_window=window_size, syn=0, ack=1, fin=1,
                    app_data="Closing connection"
                )
                client_socket.sendto(fin_packet.to_bytes(), server_address)
                print("Connection closed.")
                client_socket.close()
                break
            
            seq += len(user_input) #what we send
            data_packet = ReliableTransportLayerProtocolHeader(
                CLIENT_ADDRESS[1], server_address[1],
                seq, ack_num=received.seq_num + 1, 
                receiver_window=window_size, syn=0, ack=1, fin=0,
                app_data=user_input
            )
            client_socket.sendto(data_packet.to_bytes(), server_address)
            print(f"Sent: {user_input}")

my_client()
