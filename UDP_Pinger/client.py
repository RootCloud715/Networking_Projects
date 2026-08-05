import socket as s
import time as t

target_host = '127.0.0.1'
target_port = 9999

def main():

    client_socket = s.socket(s.AF_INET, s.SOCK_DGRAM)
    client_socket.settimeout(1) 
    rtts = []
    lost = 0
    
    for seq in range(10): 
        success = False 
        attempts = 0
        while attempts < 3 and success == False: 

            message = f"{seq}:{t.monotonic()}"
            try:
                send_time = t.monotonic()
                client_socket.sendto(message.encode(), (target_host, target_port)) 

                _ , address = client_socket.recvfrom(2048) 
                recv_time = t.monotonic()

                rtt = recv_time - send_time
                rtts.append(rtt)
                success = True

                print(f"Reply from {address}: seq={seq} time={rtt*1000:.2f}ms")

            except TimeoutError:
                attempts += 1

        if not success: 
            lost += 1 
            print(f"Request timed out: seq={seq}")

    if rtts: 
            print(f"\n--- Summary ---")
            print(f"Packets: Sent=10, Received={len(rtts)}, Lost={lost}")
            print(f"RTT min/avg/max = {min(rtts)*1000:.2f}/{(sum(rtts)/len(rtts))*1000:.2f}/{max(rtts)*1000:.2f} ms")
    else:
            print("All packets lost.")

if __name__ == '__main__':
    main()