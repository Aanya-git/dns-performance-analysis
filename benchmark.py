import time
import socket
import ssl
import requests
import dns.resolver
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- 1. Configuration (Sirf yahan network ka naam change karna hai) ---
NETWORK_NAME = "Campus WiFi"   # Wi-Fi ke liye "WiFi" aur Hotspot ke liye "Hotspot" likhein
NUM_RUNS = 5               # Har website ko kitni baar test karna hai

# 20 Target Websites (Indian + Global mix)
DOMAINS = [
    "google.com", "youtube.com", "wikipedia.org", "amazon.in",
    "flipkart.com", "irctc.co.in", "github.com", "microsoft.com",
    "instagram.com", "linkedin.com", "reddit.com", "netflix.com",
    "hotstar.com", "sbi.co.in", "ndtv.com", "thehindu.com",
    "zoom.us", "cloudflare.com", "speedtest.net", "quora.com"
]


# --- 2. Protocol Measurement Functions ---

def measure_plain_dns(domain, resolver_ip):
    """Plain DNS (UDP Port 53) ka response time ms mein nikalta hai."""
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
    """DNS-over-HTTPS (TCP Port 443) ka response time ms mein nikalta hai."""
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
    """DNS-over-TLS (TCP Port 853) ka response time ms mein nikalta hai."""
    port = 853
    # Raw DNS query packet banana
    raw_query = (
        b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        + b''.join(bytes([len(part)]) + part.encode() for part in domain.split('.'))
        + b'\x00\x00\x01\x00\x01'
    )
    query_with_len = len(raw_query).to_bytes(2, byteorder='big') + raw_query

    # Latency test ke liye SSL certificate verification skip karna
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


# --- 3. Clean Excel Report Generator ---

def save_formatted_excel(df, excel_filename):
    """Raw results ko clean aur formatted Excel sheets mein convert karta hai."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # Styling setup
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    zebra_fill = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # SHEET 1: Overall Summary Table
    ws_sum = wb.create_sheet(title="Summary")
    ws_sum['A1'] = f"DNS Latency Benchmark - {NETWORK_NAME} Network"
    ws_sum['A1'].font = Font(name="Calibri", size=15, bold=True, color="1F4E78")

    summary_df = df.groupby(['Protocol', 'Provider'])['Latency_ms'].agg(
        Mean='mean', Median='median', Min='min', Max='max', Std_Dev='std'
    ).reset_index().sort_values(by='Mean')

    headers = ["Protocol", "Provider", "Mean (ms)", "Median (ms)", "Min (ms)", "Max (ms)", "Std Dev"]
    ws_sum.append([])
    ws_sum.append(headers)

    for col_idx in range(1, len(headers) + 1):
        cell = ws_sum.cell(row=3, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for _, row in summary_df.iterrows():
        row_vals = [
            row['Protocol'], row['Provider'], round(row['Mean'], 2),
            round(row['Median'], 2), round(row['Min'], 2),
            round(row['Max'], 2), round(row['Std_Dev'], 2)
        ]
        ws_sum.append(row_vals)
        curr_r = ws_sum.max_row
        for c_idx in range(1, len(row_vals) + 1):
            cell = ws_sum.cell(row=curr_r, column=c_idx)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left" if c_idx <= 2 else "right")
            if curr_r % 2 == 0:
                cell.fill = zebra_fill

    # SHEET 2: Website-wise Average Matrix
    ws_mat = wb.create_sheet(title="Domain_Matrix")
    ws_mat['A1'] = f"Website-wise Latency Comparison ({NETWORK_NAME})"
    ws_mat['A1'].font = Font(name="Calibri", size=14, bold=True, color="1F4E78")

    pivot = df.pivot_table(index='Domain', columns=['Protocol', 'Provider'], values='Latency_ms', aggfunc='mean').round(2)
    pivot.columns = [f"{prot} ({prov})" for prot, prov in pivot.columns]
    pivot = pivot.reset_index()

    ws_mat.append([])
    mat_headers = ["Domain"] + list(pivot.columns[1:])
    ws_mat.append(mat_headers)

    for col_idx in range(1, len(mat_headers) + 1):
        cell = ws_mat.cell(row=3, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for _, row in pivot.iterrows():
        row_vals = [row['Domain']] + [round(v, 2) for v in row[1:]]
        ws_mat.append(row_vals)
        curr_r = ws_mat.max_row
        for c_idx in range(1, len(row_vals) + 1):
            cell = ws_mat.cell(row=curr_r, column=c_idx)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left" if c_idx == 1 else "right")
            if curr_r % 2 == 0:
                cell.fill = zebra_fill

    # SHEET 3: Raw Logs (All 600 readings cleanly formatted)
    ws_raw = wb.create_sheet(title="Raw_Data")
    ws_raw.append(["Domain", "Iteration", "Protocol", "Provider", "Latency_ms"])
    for col_idx in range(1, 6):
        cell = ws_raw.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font

    for row in df.itertuples(index=False):
        ws_raw.append(list(row))

    # Auto-fit columns across all sheets
    for ws in [ws_sum, ws_mat, ws_raw]:
        for col in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col)
            ws.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + 4, 12)

    wb.save(excel_filename)


# --- 4. Main Execution ---

def run_benchmark():
    print(f"==================================================")
    print(f" Starting DNS Benchmark on [{NETWORK_NAME}] Network")
    print(f"==================================================\n")

    results = []

    for domain in DOMAINS:
        print(f"[*] Testing: {domain}")
        for i in range(1, NUM_RUNS + 1):
            # Plain DNS
            lat = measure_plain_dns(domain, "8.8.8.8")
            if lat: results.append([domain, i, "Plain_DNS", "Google", lat])
            lat = measure_plain_dns(domain, "1.1.1.1")
            if lat: results.append([domain, i, "Plain_DNS", "Cloudflare", lat])

            # DoH
            lat = measure_doh(domain, "https://dns.google/resolve")
            if lat: results.append([domain, i, "DoH", "Google", lat])
            lat = measure_doh(domain, "https://1.1.1.1/dns-query")
            if lat: results.append([domain, i, "DoH", "Cloudflare", lat])

            # DoT
            lat = measure_dot(domain, "8.8.8.8")
            if lat: results.append([domain, i, "DoT", "Google", lat])
            lat = measure_dot(domain, "1.1.1.1")
            if lat: results.append([domain, i, "DoT", "Cloudflare", lat])

    df = pd.DataFrame(results, columns=["Domain", "Iteration", "Protocol", "Provider", "Latency_ms"])
    
    # Save CSV (graphs ke liye) aur Excel (faculty ko dikhane ke liye)
    csv_file = f"results_{NETWORK_NAME.lower()}.csv"
    excel_file = f"DNS_Report_{NETWORK_NAME}.xlsx"

    df.to_csv(csv_file, index=False)
    save_formatted_excel(df, excel_file)

    print(f"\n[✓] Done! Saved '{csv_file}' and formatted '{excel_file}'.")


if __name__ == "__main__":
    run_benchmark()