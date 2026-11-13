import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Clean, readable styling using standard seaborn + matplotlib
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["font.family"] = "sans-serif"

# Load House and Campus Wi-Fi datasets
df_house = pd.read_csv("results_house wifi.csv")
df_house["Network"] = "House Wi-Fi"

df_campus = pd.read_csv("results_campus wifi.csv")
df_campus["Network"] = "Campus Wi-Fi"

df = pd.concat([df_house, df_campus], ignore_index=True)

# -------------------------------------------------------------------------
# CHART 1: Dumbbell Plot (House Wi-Fi vs Campus Wi-Fi Latency Shift)
# -------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10.5, 5.5))
agg = df.groupby(["Protocol", "Provider", "Network"])["Latency_ms"].mean().unstack()
agg["Label"] = [f"{p} ({pr})" for p, pr in agg.index]
agg = agg.sort_values("House Wi-Fi")

y_pos = np.arange(len(agg))
ax.hlines(y=y_pos, xmin=agg["House Wi-Fi"], xmax=agg["Campus Wi-Fi"], color="#94a3b8", linewidth=2.5, zorder=1)
ax.scatter(agg["House Wi-Fi"], y_pos, color="#2563eb", s=110, label="House Wi-Fi", zorder=2)
ax.scatter(agg["Campus Wi-Fi"], y_pos, color="#ea580c", s=110, label="Campus Wi-Fi", zorder=2)

for idx, (_, row) in enumerate(agg.iterrows()):
    diff = row["Campus Wi-Fi"] - row["House Wi-Fi"]
    sign = "+" if diff >= 0 else ""
    ax.text(max(row["House Wi-Fi"], row["Campus Wi-Fi"]) + 15, idx,
            f"{row['House Wi-Fi']:.1f} → {row['Campus Wi-Fi']:.1f} ms ({sign}{diff:.1f} ms)",
            va="center", fontsize=10, color="#1e293b", fontweight="bold")

ax.set_yticks(y_pos)
ax.set_yticklabels(agg["Label"], fontsize=11, fontweight="bold")
ax.set_xlabel("Mean Resolution Latency (ms)", fontsize=11, fontweight="bold")
ax.set_title("Network Shift Impact: House Wi-Fi vs. Campus Wi-Fi", fontsize=13.5, fontweight="bold", pad=12)
ax.set_xlim(0, 880)
ax.legend(loc="lower right", frameon=True, fontsize=10.5)
sns.despine(left=True)
plt.tight_layout()
plt.savefig("chart1_network_shift_dumbbell.png", dpi=300)
plt.close()

# -------------------------------------------------------------------------
# CHART 2: Box + Strip Plot (All 1,200 Queries & Congestion Outliers)
# -------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.8))
df["Protocol_Label"] = df["Protocol"].replace({
    "Plain_DNS": "Plain DNS\n(UDP 53)",
    "DoT": "DoT\n(TLS 853)",
    "DoH": "DoH\n(HTTPS 443)"
})
prot_order = ["Plain DNS\n(UDP 53)", "DoT\n(TLS 853)", "DoH\n(HTTPS 443)"]

sns.boxplot(
    data=df, x="Protocol_Label", y="Latency_ms", hue="Network",
    order=prot_order, palette={"House Wi-Fi": "#3b82f6", "Campus Wi-Fi": "#f97316"},
    width=0.45, fliersize=0, boxprops=dict(alpha=0.85), ax=ax
)
sns.stripplot(
    data=df, x="Protocol_Label", y="Latency_ms", hue="Network",
    order=prot_order, palette={"House Wi-Fi": "#1e3a8a", "Campus Wi-Fi": "#9a3412"},
    dodge=True, jitter=0.18, alpha=0.45, size=4.5, legend=False, ax=ax
)

ax.set_yscale("log")
ax.set_yticks([5, 10, 25, 50, 100, 250, 500, 1000, 2000])
ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
ax.set_ylabel("Resolution Latency (ms) — Log Scale", fontsize=11, fontweight="bold")
ax.set_xlabel("")
ax.set_title("Latency Spread & Congestion Spikes Across All 1,200 Queries", fontsize=13.5, fontweight="bold", pad=12)
ax.annotate("Campus DoH spike: 1,682 ms", xy=(2.18, 1681.75), xytext=(1.35, 1450),
            arrowprops=dict(arrowstyle="->", color="#9a3412", lw=1.5),
            fontsize=10, fontweight="bold", color="#9a3412")
ax.legend(title="Network", loc="upper left", frameon=True, fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig("chart2_distribution_boxplot.png", dpi=300)
plt.close()

# -------------------------------------------------------------------------
# CHART 3: Cumulative Distribution Function (CDF Tail Latency)
# -------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), sharey=True)
palette_cdf = {
    ("Plain_DNS", "Cloudflare"): "#059669",
    ("Plain_DNS", "Google"): "#65a30d",
    ("DoT", "Google"): "#2563eb",
    ("DoT", "Cloudflare"): "#7c3aed",
    ("DoH", "Google"): "#d97706",
    ("DoH", "Cloudflare"): "#dc2626",
}

for idx, net in enumerate(["House Wi-Fi", "Campus Wi-Fi"]):
    ax = axes[idx]
    sub = df[df["Network"] == net]
    for (prot, prov), col in palette_cdf.items():
        vals = np.sort(sub[(sub["Protocol"] == prot) & (sub["Provider"] == prov)]["Latency_ms"])
        cdf = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, cdf * 100, label=f"{prot} ({prov})", color=col, linewidth=2.3)

    ax.axhline(95, color="#475569", linestyle="--", linewidth=1.1)
    ax.text(240, 96.5, "95th Percentile", fontsize=9, color="#475569", fontweight="bold")
    ax.set_title(f"{net}", fontsize=12.5, fontweight="bold")
    ax.set_xlabel("Resolution Latency (ms)", fontsize=11)
    ax.set_xlim(0, 760)
    if idx == 0:
        ax.set_ylabel("Cumulative % of Queries", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8.8, frameon=True)
    sns.despine(ax=ax)

fig.suptitle("Cumulative Distribution Function (CDF): Consistency & Tail Latency", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("chart3_cdf_stability.png", dpi=300, bbox_inches="tight")
plt.close()

# -------------------------------------------------------------------------
# CHART 4: Indian vs. Global Domains Routing Breakdown (Campus Wi-Fi)
# -------------------------------------------------------------------------
indian_domains = {"amazon.in", "flipkart.com", "irctc.co.in", "hotstar.com", "sbi.co.in", "ndtv.com", "thehindu.com"}
df_campus["Category"] = df_campus["Domain"].apply(
    lambda d: "Indian Domains (.in / Local)" if d in indian_domains else "Global Domains (.com / .org)"
)

fig, ax = plt.subplots(figsize=(9.5, 5.2))
cat_summary = df_campus.groupby(["Protocol", "Category"])["Latency_ms"].mean().reset_index()
sns.barplot(
    data=cat_summary, x="Protocol", y="Latency_ms", hue="Category",
    order=["Plain_DNS", "DoT", "DoH"], palette=["#0d9488", "#6366f1"], edgecolor="black", ax=ax
)

for container in ax.containers:
    ax.bar_label(container, fmt="%.1f ms", padding=3, fontsize=9.5, fontweight="bold")

ax.set_title("Indian vs. Global Websites: Anycast Routing Efficiency (Campus Wi-Fi)", fontsize=12.5, fontweight="bold", pad=12)
ax.set_ylabel("Mean Resolution Latency (ms)", fontsize=11, fontweight="bold")
ax.set_xlabel("DNS Protocol", fontsize=11, fontweight="bold")
ax.set_ylim(0, 720)
ax.legend(title="Domain Region", frameon=True, fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig("chart4_indian_vs_global.png", dpi=300)
plt.close()

print("All 4 charts saved successfully!")