import time
import requests

# Cloudflare DNS-over-HTTPS Endpoint
url = "https://1.1.1.1/dns-query"
params = {"name": "google.com", "type": "A"}
headers = {"accept": "application/dns-json"}

start_time = time.time()
response = requests.get(url, params=params, headers=headers)
end_time = time.time()

latency_ms = (end_time - start_time) * 1000
data = response.json()

print(f"Target: google.com")
print(f"Encrypted DoH IP Found: {data['Answer'][0]['data']}")
print(f"DoH Resolution Latency: {latency_ms:.2f} ms")