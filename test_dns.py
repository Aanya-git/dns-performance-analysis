import time
import dns.resolver

domain = "google.com"

# Set up resolver using Google's Public DNS (8.8.8.8)
resolver = dns.resolver.Resolver(configure=False)
resolver.nameservers = ['8.8.8.8']

start_time = time.time()
answer = resolver.resolve(domain, 'A')
end_time = time.time()

latency_ms = (end_time - start_time) * 1000

print(f"Target: {domain}")
print(f"Plain DNS IP Found: {answer[0]}")
print(f"Resolution Latency: {latency_ms:.2f} ms")