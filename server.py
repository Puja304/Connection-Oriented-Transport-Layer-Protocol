import socket
from header import ReliableTransportLayerProtocolHeader
import time
import random

# Constants
HOST = '127.0.0.1'  # Localhost
SENDER_PORT = 8001
RECEIVER_PORT = 8000
WINDOW_SIZE = 4  # Size of the window in Selective Repeat
MSS = 15  # Maximum segment size

# Function to perform the 3-way handshake on the receiver's side
def handshake(server_sock):
    connection_details = {
        "Alive": False,
        "IP": 0,
        "Port": 0,
        "senderSeqNum": 0,
        "senderACKNum": 0,
        "sender_window": 0,
        "sender_mss": 0,
        "receiverSeqNum": 0,
        "receiverACKNum": 0
    }

    # Receive SYN
    data, addr = server_sock.recvfrom(1024)
    data = ReliableTransportLayerProtocolHeader.from_bytes(data)
    print("Receiver: Received SYN")
    app_data = "Received SYN, do you still want to connect?"
    syn_bit = 1
    ack_bit = 1
    ack_num = data.seq_num + 1
    seq = random.randint(0, 2000)
    message = ReliableTransportLayerProtocolHeader(
        RECEIVER_PORT, SENDER_PORT, seq, ack_num, WINDOW_SIZE, MSS, syn=syn_bit, ack=ack_bit, app_data=app_data
    )
    #print("check")
    server_sock.sendto(message.to_bytes(), addr)
    print("Receiver: Sent SYN-ACK")

    # Receive ACK
    data, addr = server_sock.recvfrom(1024)
    data = ReliableTransportLayerProtocolHeader.from_bytes(data)
    if addr == (HOST, SENDER_PORT):
        if data.syn == 0 and data.ack == 1 and data.ack_num == seq + 1:
            print("Receiver: Received ACK. 3-way handshake complete")

            connection_details["Alive"] = True
            connection_details["sender_window"] = data.sending_window
            connection_details["sender_mss"] = data.mss
            connection_details["Port"] = addr[1]
            connection_details["senderSeqNum"] = data.seq_num
            connection_details["senderACKNum"] = data.ack_num
            connection_details["receiverSeqNum"] = seq + 1
            connection_details["receiverACKNum"] = ack_num

    return connection_details

def receive_data(server_sock, connection_details):
    print("Receiver: Ready to receive data")
    # window_start = connection_details["senderSeqNum"]  # Next expected sequence number
    window_start = 0
    window_end = window_start + WINDOW_SIZE - 1  # Window end is current_seq + WINDOW_SIZE - 1
    received_data = []
    buffer = {}  # Buffer for out-of-order packets

    while True:
        data, addr = server_sock.recvfrom(1024)
        header = ReliableTransportLayerProtocolHeader.from_bytes(data)

        # Handle connection termination (FIN packet)
        if header.fin:  
            print("Receiver: FIN received, starting connection termination")
            terminate_connection(server_sock, header, addr)
            break

        # Check if the sequence number is within the current window
        if window_start <= header.seq_num <= window_end:
            if header.seq_num == window_start:
                # In-order packet, process it
                print(f"Receiver: Received packet {header.seq_num} with data: {header.app_data}")
                print(time.time())
                received_data.append(header.app_data)
                window_start += 1  # Move the window forward

                # After processing the in-order packet, check if any buffered packets can now be processed
                while window_start in buffer:
                    # If the next expected sequence number is in the buffer, process it
                    buffered_packet = buffer.pop(window_start)
                    received_data.append(buffered_packet)
                    print(f"Receiver: Buffered packet {window_start} delivered")
                    window_start += 1

                # Update window_end based on new window_start
                window_end = window_start + WINDOW_SIZE - 1
                print(f"new window size: {window_end}")
            else:
                # Out-of-order packet, buffer it
                print(f"Receiver: Out-of-order packet {header.seq_num} received. Buffering...")
                buffer[header.seq_num] = header.app_data

            # Send ACK for the next expected sequence number (window_start)
            ack_header = ReliableTransportLayerProtocolHeader(
                RECEIVER_PORT, SENDER_PORT, 0, window_start, WINDOW_SIZE, MSS, ack=True
            )
            server_sock.sendto(ack_header.to_bytes(), addr)
            print(f"Receiver: Sent ACK for {window_start - 1}")

        else:
            # If the packet's sequence number is outside the window, discard it
            print(f"Receiver: Packet {header.seq_num} out of range. Discarding.")

        print("Receiver: Data received:", "".join(received_data))


# Function to handle connection termination (4-way handshake)
def terminate_connection(server_sock, header, addr):
    print("Receiver: Sending FIN-ACK")
    fin_bit = 1
    ack_bit = 1
    fin_ack_packet = ReliableTransportLayerProtocolHeader(
        RECEIVER_PORT, SENDER_PORT, header.ack_num, header.seq_num + 1, WINDOW_SIZE, MSS, fin=fin_bit, ack=ack_bit
    )
    server_sock.sendto(fin_ack_packet.to_bytes(), addr)

    # Wait for final ACK from sender
    data, addr = server_sock.recvfrom(1024)
    ack_header = ReliableTransportLayerProtocolHeader.from_bytes(data)
    if ack_header.ack == 1 and ack_header.seq_num == header.seq_num + 1:
        print("Receiver: Received final ACK. Connection terminated.")


# Main function to start the receiver
def start_receiver():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind((HOST, RECEIVER_PORT))
    print("Receiver: Waiting for connections...")

    # Perform handshake
    connection_details = handshake(server_sock)
    if connection_details["Alive"]:
        print("Receiver: Connection established. Ready to receive data.")
        receive_data(server_sock, connection_details)


if __name__ == "__main__":
    start_receiver()
