import socket
import time
from utils import ReliableTransportLayerProtocolHeader
import random


HOST = '127.0.0.1'  # Localhost
SENDER_PORT = 8001
RECEIVER_PORT = 8000  
WINDOW_SIZE = 4  
MAX_SEQ = (WINDOW_SIZE * 2) + 1  # Making sure there is no confusion
MSS = 15               # Maximum segment size
DATA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 3 + "1234567890"  # 90 bytes of data that will be sent 
TIMEOUT = 2  # Timeout in seconds for packet retransmission


# Function that performs the 3-way handshake and returns all necessary details of the connection in a dictionary
def handshake(client_sock):
    connection_details = {
        "Alive": False,
        "IP": 0,
        "Port": 0,
        "receiverSeqNum": 0,
        "receiverACKNum": 0,
        "receiver_window": 0,
        "receiver_mss": 0,
        "senderSeqNum": 0,
        "senderACKNum": 0
    }

    print("Sender: Sending SYN to initiate handshake...")
    app_data = "Hey! Do you want to connect?"
    synbit = 1
    seq = random.randint(0, 2000)    
    ack_num = 0
    message = ReliableTransportLayerProtocolHeader(SENDER_PORT, RECEIVER_PORT, seq, ack_num, WINDOW_SIZE, MSS, syn=synbit, app_data=app_data)
    client_sock.sendto(message.to_bytes(), (HOST, RECEIVER_PORT))

    data, addr = client_sock.recvfrom(1024)
    data = ReliableTransportLayerProtocolHeader.from_bytes(data)
    if addr == (HOST, RECEIVER_PORT):
        # We've received a message from the correct place
        if data.syn == 1 and data.ack == 1 and data.ack_num == seq + 1:
            print("Sender: Received SYN-ACK, sending ACK...")

            # Storing all details of the connection, to be used for the next stages 
            connection_details["receiver_window"] = data.sending_window
            connection_details["receiver_mss"] = data.mss
            connection_details["Port"] = addr[1]
            connection_details["receiverSeqNum"] = data.seq_num
            connection_details["receiverACKNum"] = data.ack_num
            connection_details["senderSeqNum"] = seq + 1
            connection_details["senderACKNum"] = connection_details["receiverSeqNum"] + 1

            # Sending an ACK in response to their SYNACK
            ack_bit = 1
            app_data = "Great! Let's connect"
            message = ReliableTransportLayerProtocolHeader(SENDER_PORT, RECEIVER_PORT, connection_details["senderSeqNum"], connection_details["senderACKNum"], WINDOW_SIZE, MSS, ack=ack_bit, app_data=app_data)
            client_sock.sendto(message.to_bytes(), (HOST, RECEIVER_PORT))
            print("Sender: Sent ACK in response to SYNACK. 3-way handshake complete")
    return connection_details

#function that sends packets by encapsulating them our custom protocol's header
def send_packet(data, client_sock, connection_details):
    packet_header = ReliableTransportLayerProtocolHeader(SENDER_PORT, RECEIVER_PORT, connection_details["senderSeqNum"], connection_details["senderACKNum"], WINDOW_SIZE, MSS, app_data=data)
    packet_bytes = packet_header.to_bytes()
    client_sock.sendto(packet_bytes, (HOST, RECEIVER_PORT))
    print(f"Client: Sent packet {connection_details['senderSeqNum']}.")


#packet that keeps track of which ACKs have been received, as long as they were in the window
def receive_ack(client_sock, sent_packets, connection_details):
    try:
        ack, _ = client_sock.recvfrom(1024)
        ack_header = ReliableTransportLayerProtocolHeader.from_bytes(ack)
        ack_num = ack_header.ack_num
        if ack_num in sent_packets:
            print(f"Client: Received ACK for {ack_num}.")
            connection_details["receiverSeqNum"] = ack_header.seq_num  # Receiver's current sequence number
            connection_details["receiverACKNum"] = ack_header.ack_num  # Next expected sequence number
            del sent_packets[ack_num]  # Remove from sent_packets
    except socket.timeout:
        print("Client: Timeout waiting for ACK, resending...")

#sends data to the the receivers. handles sending, acknowledging acks, retransmissions, and AIMD
def send_data(packet_data, connection_details, client_sock):
    global WINDOW_SIZE
    window_start = 0
    window_end = WINDOW_SIZE - 1

    sent_packets = {}  # This will store timestamped packets for retransmission
    expected_acks = set(range(window_start, window_end + 1))  # Set of expected ACKs for the current window
    
    while window_start < len(packet_data):
        # Send packets in the current window
        for seq_num in range(window_start, window_end + 1):
            if seq_num < len(packet_data) and seq_num not in sent_packets:
                current_time = time.time()
                connection_details["senderSeqNum"] = seq_num  # Set current sequence number for sender
                connection_details["receiverACKNum"] = connection_details["senderSeqNum"] + 1  # Expect next sequence from receiver
                
                # Send the packet
                send_packet(packet_data[seq_num], client_sock, connection_details)
                
                # Mark the packet as sent and record the timestamp
                sent_packets[seq_num] = current_time
                expected_acks.add(seq_num)  # Expect this ACK

        # Wait for ACKs and adjust the window
        receive_ack(client_sock, sent_packets, connection_details)

        # Adjust the window and retry on timeout
        acked_seq_nums = set(sent_packets.keys())  # Set of ACKed packets
        unacked_seq_nums = expected_acks - acked_seq_nums  # Set of unacknowledged sequence numbers

        if not unacked_seq_nums:  # All expected ACKs received
            print(f"All ACKs received for window {window_start}-{window_end}.")
            # Additive Increase: Increase the window size if all packets in the window are acknowledged
            WINDOW_SIZE += 1
            print(f"Window size increased to {WINDOW_SIZE}.")
        else:  # Some packets weren't acknowledged (due to timeout or reordering)
            print(f"Some ACKs are missing for window {window_start}-{window_end}. Resending...")
            # Multiplicative Decrease: Halve the window size due to packet loss (timeout)
            WINDOW_SIZE = max(WINDOW_SIZE // 2, 1)
            print(f"Window size decreased to {WINDOW_SIZE}.")

        # Move window to the next range
        window_start = window_end + 1
        window_end = min(window_start + WINDOW_SIZE - 1, len(packet_data) - 1)

        # Update expected ACKs for the new window
        expected_acks = set(range(window_start, window_end + 1))

        time.sleep(1)  # Wait a bit before sending the next batch of packets



# Function that turns the given data into separate chunks, each containing the information that will be sent in a single packet
def preparePackets():
    chunks = []
    total_data_length = len(DATA)
    
    for i in range(0, total_data_length, MSS):
        chunk = DATA[i:i + MSS]
        chunks.append(chunk)
    
    return chunks


# 4-way fin ack handshake
def end_connection(client_sock, connection_details):
    # Step 1: Sender sends a FIN (Finish) to initiate connection termination
    print("Sender: Sending FIN to terminate the connection...")
    
    seq_num = connection_details["senderSeqNum"]
    ack_num = connection_details["senderACKNum"]
    
    # Create and send the FIN message
    fin_bit = 1  # FIN bit is set to 1
    app_data = "Goodbye! Closing connection."
    fin_packet = ReliableTransportLayerProtocolHeader(
        SENDER_PORT, RECEIVER_PORT, seq_num, ack_num, WINDOW_SIZE, MSS, fin=fin_bit, app_data=app_data
    )
    client_sock.sendto(fin_packet.to_bytes(), (HOST, RECEIVER_PORT))
    
    # Wait for FIN-ACK from receiver
    attempts = 0
    while attempts < 3:
        try:
            print("Sender: Waiting for FIN-ACK from receiver...")
            data, addr = client_sock.recvfrom(1024)
            data = ReliableTransportLayerProtocolHeader.from_bytes(data)
            
            if addr == (HOST, RECEIVER_PORT) and data.fin == 1 and data.ack == 1:
                print("Sender: Received FIN-ACK, sending final ACK...")
                
                # Step 2: Sender sends ACK to finalize the termination process
                ack_bit = 1
                app_data = "Final ACK. Connection closed."
                final_ack_packet = ReliableTransportLayerProtocolHeader(
                    SENDER_PORT, RECEIVER_PORT, seq_num + 1, ack_num + 1, WINDOW_SIZE, MSS, ack=ack_bit, app_data=app_data
                )
                client_sock.sendto(final_ack_packet.to_bytes(), (HOST, RECEIVER_PORT))
                print("Sender: Sent final ACK. Connection closed.")
                break
        except socket.timeout:
            print("Sender: Timeout, retrying FIN-ACK...")
            attempts += 1
            time.sleep(1)
    return

def start_client():
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_sock.bind((HOST, SENDER_PORT))
    client_sock.settimeout(2)
    while True:
        #create a connection
        connection_details = handshake(client_sock)
        if (connection_details["Alive"]): #connection established and alive
            sending = preparePackets()   #break up the DATA into chunks
            send_data(sending, connection_details, client_sock)
            end_connection(client_sock, connection_details)


if __name__ == "__main__":
    start_client()
