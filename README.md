# Empirical Latency Analysis: Encrypted vs. Unencrypted DNS Resolvers

An empirical measurement project analyzing the resolution performance overhead of Plain DNS (UDP 53) vs. Encrypted DNS (DoH/DoT) under real-world network conditions.

## Project Structure
- `test_dns.py`: Baseline plain DNS query script
- `test_doh.py`: DNS-over-HTTPS measurement script