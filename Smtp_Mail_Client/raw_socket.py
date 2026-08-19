import socket
import ssl
import base64
import os

Host = 'smtp.gmail.com'
Port = 465


def send_command(sock, command):
    sock.send(command.encode())
    receive = sock.recv(1024)
    return receive.decode()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.create_default_context()
    secure_socket = context.wrap_socket(server_socket, server_hostname=Host)
    secure_socket.connect((Host, Port))

    response = secure_socket.recv(1024)
    print(response.decode())

    sender_email = os.environ["GMAIL_ADDRESS"]
    recipient_email = os.environ["Recpt_GMAIL_ADDRESS"]
    encoded_email = base64.b64encode(sender_email.encode()).decode()
    encoded_password = base64.b64encode(os.environ["GMAIL_APP_PASSWORD"].encode()).decode()

    result = send_command(secure_socket, "EHLO test.com\r\n")
    print(result)

    auth = send_command(secure_socket, "AUTH LOGIN\r\n")
    print(auth)

    encode_email = send_command(secure_socket, encoded_email + "\r\n")
    print(encode_email)

    encode_password = send_command(secure_socket, encoded_password + "\r\n")
    print(encode_password)

    mail_from = send_command(secure_socket, f"MAIL FROM:<{sender_email}>\r\n")
    print(mail_from)

    mail_to = send_command(secure_socket, f"RCPT TO:<{recipient_email}>\r\n")
    print(mail_to)

    data = send_command(secure_socket, "DATA\r\n")
    print(data)

    message_lines = [
        f"From: {sender_email}",
        f"To: {recipient_email}",
        "Subject: Manual SMTP test",
        "",
        "Hello from my Python client.",
        "."
    ]
    message = "\r\n".join(message_lines) + "\r\n"
    msg = send_command(secure_socket, message)
    print(msg)

    qu = send_command(secure_socket, "QUIT\r\n")
    print(qu)


if __name__ == "__main__":
    main()