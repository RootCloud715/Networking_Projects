import socket 

Host = '127.0.0.1'
Port = 9999

def main():

    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((Host,Port))
    server_socket.listen(5)

    print(f'[*] server is listening on {Port}:{Host}')

    while True:

        connection_socket , client_address = server_socket.accept()
        print(f'[*] Connection from {client_address}')
        request = connection_socket.recv(4096).decode()
        tokens = request.split()
        if len(tokens) < 2:
            connection_socket.close()
            continue
        if tokens[0] != 'GET':
            header = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
            connection_socket.send(header.encode())
            connection_socket.close()
            continue
        filename = tokens[1].lstrip('/')
        try:
            with open(filename, 'rb') as f:
                file_content = f.read()          
                header = "HTTP/1.1 200 OK\r\n\r\n"    
                connection_socket.send(header.encode() + file_content)
                
        except FileNotFoundError:
            header = "HTTP/1.1 404 Not Found\r\n\r\n"
            connection_socket.send(header.encode())
        connection_socket.close()

if __name__ == "__main__":
    main()