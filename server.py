import socket
from header import ReliableTransportLayerProtocolHeader

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   #establishes it as a UDP socket
SERVER_ADDRESS = ("127.0.0.1", 8000)    #server's address

def custom_socket():
    server_socket.bind(SERVER_ADDRESS)                          #binds it to our local host
    print("Server is listening")

    while True:
        data, client_addr = server_socket.recvfrom(1024)
        received = ReliableTransportLayerProtocolHeader.from_bytes(data)
        if(received.syn):
            print("Received request for Step 1 of handshake")
            print(f"Received message : {received.app_data}")
            #intiate step 2
            ackNum = 1 + received.seq_num
            seq = 0
            message = ReliableTransportLayerProtocolHeader(SERVER_ADDRESS[1], received.source_port_num, seq, ackNum, 5, app_data=f"I got your message. Do you still want  to connect?",syn=1, fin = 0, ack= 1)
            server_socket.sendto(message.to_bytes(), client_addr)
            print("Initiated step 2 of handshake")

            #get client's response
            data,client_addr = server_socket.recvfrom(1024)
            received = ReliableTransportLayerProtocolHeader.from_bytes(data)

            #if the response is an ACK
            if (received.ack & received.ack_num == (seq + 1)):
                #the connection has been established
                print("Step 3 has been completed. The connection has been established")
                print(f"Received message : {received.app_data}")
                handle_connection(client_addr, seq, ackNum)
                break
                       
            else:
                print("Failed to initialize connection")

        print("Please Initialize Connection First")


def handle_connection(client_address, initial_sequence, initial_ACK):
    print(f"Connected to {client_address}")

    current_seq = initial_sequence
    current_ACK = initial_ACK

    while True:
        data,sender_address = server_socket.recvfrom(1024)
        received = ReliableTransportLayerProtocolHeader.from_bytes(data)
        if(sender_address == client_address):  #making sure we are only processing files sent by our client right now
            #if they sent a FIN message
            if(received.fin):  
                print("Client wants to end the connection")
                ack_num = received.seq_num + 1

                #send a FINACK message
                fin_ack = ReliableTransportLayerProtocolHeader(
                    SERVER_ADDRESS[1], client_address[1], current_seq,
                    ack_num, received.receiver_window,  syn=0, ack=1, fin=1,
                    app_data="It was nice being connected :)"
                )
                server_socket.sendto(fin_ack.to_bytes(), client_address)
                current_seq += 1  # Increment seq for the FIN
                print("Connection closed")
                break

            #if not requesting for the connection to be closed
            print(f"Received {received.app_data}")
            current_ACK = received.seq_num + len(received.app_data)

            #send an acknowledgement
            response = f"Acknowledgment : Received {received.app_data}"
            ack_packet = ReliableTransportLayerProtocolHeader(
                SERVER_ADDRESS[1], client_address[1], current_seq,
                current_ACK, received.receiver_window, syn=0, ack=1, fin=0, 
                app_data=response
            )
            server_socket.sendto(ack_packet.to_bytes(), client_address)

            #increment sequence number
            current_seq += len(response)
        if(sender_address != client_address):
            print("File dropped : unknown client")


custom_socket()

