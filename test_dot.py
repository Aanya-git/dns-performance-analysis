import socket
import ssl
import time

# Target domain to look up
domain = "google.com"

# Cloudflare DNS-over-TLS (DoT) server and standard port
dot_server = "1.1.1.1"
port = 853

# Build raw wire-format DNS query for 'google.com' (A Record)
raw_query = (
    b'\x12\x34'  # Transaction ID
    b'\x01\x00'  # Standard query flags
    b'\x00\x01'  # Question count: 1
    b'\x00\x00\x00\x00\x00\x00' # Answer/Auth/Add RRs: 0
    b'\x06google\x03com\x00'    # Domain: google.com
    b'\x00\x01'  # QTYPE: A Record
    b'\x00\x01'  # QCLASS: IN
)

# DoT protocol requires a 2-byte prefix specifying query length
query_with_len = len(raw_query).to_bytes(2, byteorder='big') + raw_query

# Create SSL/TLS encryption context
# Create SSL/TLS context and disable certificate verification for latency benchmarking
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

start_time = time.time()

# Establish encrypted TCP+TLS socket connection to port 853
with socket.create_connection((dot_server, port), timeout=3.0) as raw_sock:
    with context.wrap_socket(raw_sock, server_hostname=dot_server) as tls_sock:
        tls_sock.sendall(query_with_len)
        response = tls_sock.recv(1024)

end_time = time.time()
latency_ms = (end_time - start_time) * 1000

print(f"Target: {domain}")
print(f"DoT Provider: Cloudflare ({dot_server}:{port})")
print(f"Resolution Latency: {latency_ms:.2f} ms")