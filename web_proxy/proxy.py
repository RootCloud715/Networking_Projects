import socket

Proxy_host = ''
Proxy_port = 9999


def parse_request(message):

    lines = message.split('\r\n')

    if not lines or not lines[0]:
        raise ValueError("Empty HTTP Request")

    parts = lines[0].split()

    if len(parts) != 3:
        raise ValueError("Malformed request line") 
                               
    method, url, version = parts

    if version not in ("HTTP/1.0", "HTTP/1.1"):
        raise ValueError("Unsupported HTTP version")
    
    if url.startswith('http://'):
        url = url[len('http://'):]
    
    if '/' in url:
        host_port, path = url.split('/', 1)
        path = '/' + path
    else:
        host_port = url
        path = '/'

    if ':' in host_port:
        hostname, port = host_port.split(':')
        port = int(port)
    else:
        hostname = host_port
        port = 80

    return method, hostname, port, path

def run_proxy():
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind((Proxy_host, Proxy_port))
    proxy_socket.listen(5)

    while True:

            client_socket, _ = proxy_socket.accept()
            proxy_client_socket = None
            try:
                message = client_socket.recv(4096).decode() # How to validate here  
                method, hostname, port, path = parse_request(message)
                if method != "GET":
                    raise ValueError("Only supports GET request")
                
                request = (
                    f"{method} {path} HTTP/1.1\r\n"
                    f"Host: {hostname}\r\n"
                    f"\r\n"
                )
                proxy_client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                
                proxy_client_socket.settimeout(5)
                proxy_client_socket.connect((hostname,port))
                proxy_client_socket.sendall(request.encode())
                while True:
                    response = proxy_client_socket.recv(4096)
                    if response == b'':
                        print("complete response received.")
                        break
                    client_socket.sendall(response)

            except Exception as e:
                print(f'malformed request or connection error: {e}')
                
            finally:
                client_socket.close()

                if proxy_client_socket:
                    proxy_client_socket.close()



if __name__ == '__main__':
    run_proxy()