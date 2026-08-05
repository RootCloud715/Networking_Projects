import socket as s
import random as r

host = '127.0.0.1'
port = 9999

def main():

    server_socket = s.socket(s.AF_INET,s.SOCK_DGRAM)
    server_socket.bind((host,port))
    last_seen = {}
    print(f'[*] Server is listening on {host}:{port}')

    while True:
        try:
            data, client_address = server_socket.recvfrom(2048)
            if r.random() <= 0.5:
                print("[!] Simulating dropped packets")
                continue
            message_seq_str, message_body = data.decode().split(":", 1)
            message_seq = int(message_seq_str)

            if client_address not in last_seen or last_seen[client_address][0] != message_seq:
                response = f"{message_seq}:echo: {message_body}"
                last_seen[client_address] = (message_seq, response)
                if r.random() <= 0.5:
                    print("[!] Simulating dropped response")
                    continue
                server_socket.sendto(response.encode('utf-8'), client_address)
            else:
                response = last_seen[client_address][1]
                server_socket.sendto(response.encode('utf-8'), client_address)

        except KeyboardInterrupt:
            print("\n key board interrupt")
            break

    server_socket.close()

if __name__ == '__main__':
    main()