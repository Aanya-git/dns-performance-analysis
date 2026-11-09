import time
import csv
import socket
import ssl
import requests
import dns.resolver

# --- 1. Target Domain Dataset (20 popular websites) ---
DOMAINS = [
    "google.com", "youtube.com", "wikipedia.org", "amazon.in",
    "flipkart.com", "irctc.co.in", "github.com", "microsoft.com",
    "instagram.com", "linkedin.com", "reddit.com", "netflix.com",
    "hotstar.com", "sbi.co.in", "ndtv.com", "thehindu.com",
    "zoom.us", "cloudflare.com", "speedtest.net", "quora.com"
]

# Number of iterations per website to measure delay spread/variance
NUM_RUNS = 5
OUTPUT_CSV = "results_wifi.csv"


# --- 2. Benchmark Helper Functions ---

def measure_plain_dns(domain, resolver_ip):
    """Measures Plain DNS lookup time over UDP Port 53."""
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [resolver_ip]
    resolver.timeout = 2.0
    resolver.lifetime = 2.0
    
    start = time.time()
    try:
        resolver.resolve(domain, 'A')
        return round((time.time() - start) * 1000, 2)
    except Exception:
        return None


def measure_doh(domain, doh_url):
    """Measures DNS-over-HTTPS lookup time over TCP Port 443."""
    params = {"name": domain, "type": "A"}
    headers = {"accept": "application/dns-json"}
    
    start = time.time()
    try:
        response = requests.get(doh_url, params=params, headers=headers, timeout=2.0)
        if response.status_code == 200:
            return round((time.time() - start) * 1000, 2)
        return None
    except Exception:
        return None


def measure_dot(domain, dot_ip):
    """Measures DNS-over-TLS lookup time over TCP Port 853."""
    port = 853
    # Build raw wire-format DNS query packet for A record
    raw_query = (
        b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        + b''.join(bytes([len(part)]) + part.encode() for part in domain.split('.'))
        + b'\x00\x00\x01\x00\x01'
    )
    query_with_len = len(raw_query).to_bytes(2, byteorder='big') + raw_query

    # Disable SSL cert check specifically for latency timing tests
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    start = time.time()
    try:
        with socket.create_connection((dot_ip, port), timeout=2.0) as raw_sock:
            with context.wrap_socket(raw_sock, server_hostname=dot_ip) as tls_sock:
                tls_sock.sendall(query_with_len)
                _ = tls_sock.recv(1024)
        return round((time.time() - start) * 1000, 2)
    except Exception:
        return None


# --- 3. Main Benchmark Execution ---

def run_benchmark():
    print("==================================================")
    print(" Starting DNS Latency Benchmark across 20 Domains")
    print("==================================================\n")

    results = []

    for domain in DOMAINS:
        print(f"[*] Benchmarking: {domain}")

        for i in range(1, NUM_RUNS + 1):
            # Test Plain DNS (UDP 53)
            lat = measure_plain_dns(domain, "8.8.8.8")
            if lat: results.append([domain, i, "Plain_DNS", "Google", lat])
            lat = measure_plain_dns(domain, "1.1.1.1")
            if lat: results.append([domain, i, "Plain_DNS", "Cloudflare", lat])

            # Test DoH (TCP 443)
            lat = measure_doh(domain, "https://dns.google/resolve")
            if lat: results.append([domain, i, "DoH", "Google", lat])
            lat = measure_doh(domain, "https://1.1.1.1/dns-query")
            if lat: results.append([domain, i, "DoH", "Cloudflare", lat])

            # Test DoT (TCP 853)
            lat = measure_dot(domain, "8.8.8.8")
            if lat: results.append([domain, i, "DoT", "Google", lat])
            lat = measure_dot(domain, "1.1.1.1")
            if lat: results.append([domain, i, "DoT", "Cloudflare", lat])

    # Save to CSV
    with open(OUTPUT_CSV, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Domain", "Iteration", "Protocol", "Provider", "Latency_ms"])
        writer.writerows(results)

    print(f"\n[✓] Finished! Saved {len(results)} timing records to '{OUTPUT_CSV}'.")


if __name__ == "__main__":
    run_benchmark()