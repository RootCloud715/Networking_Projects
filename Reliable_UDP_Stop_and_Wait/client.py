import socket as s
import time as t 

target_host = "127.1.1.1"
target_port = 9998

def main():

    client = s.socket(s.AF_INET,s.SOCK_DGRAM)
    seq_num = 0
    message = "hello_server!"
    max_retries = 5
    attempts = 0
    while attempts <= max_retries:
        try:
            client.sendto(f"{seq_num}:{message}".encode("utf-8"), (target_host, target_port))
            got_match = False
            start = t.monotonic()
            timeout_budget = 5
            while not got_match:
                remaining = timeout_budget - (t.monotonic() - start)
                if remaining <= 0:
                    raise TimeoutError("no matching response with the budget")
                client.settimeout(remaining)
                data, addr = client.recvfrom(4096)   # keep draining until timeout or match
                response_seq_str, response_body = data.decode().split(":", 1)
                response_seq = int(response_seq_str)
                if response_seq == seq_num:
                    print(response_body)
                    seq_num += 1
                    got_match = True
            break
        except TimeoutError:
            attempts += 1
            print(f"[!] Timeout, retry {attempts}/{max_retries}")
    else:
        print("Server not reachable")
    client.close()

if __name__ == "__main__":
    main()