import os
from collections import defaultdict

# 📁 İki senaryo dosyasını karşılaştır
trace_files = {
    "64Kb Bottleneck": "case4_1_udp_64kb.trace",
    "256Kb Optimized": "case4_2_udp_256kb.trace"
}

def extract_metrics(trace_file):
    sent = recv = drop = 0
    packet_sizes = []
    start = end = None
    all_enqueue_times = defaultdict(dict)
    all_waiting_times = defaultdict(list)

    with open(trace_file, "r") as f:
        for line in f:
            fields = line.strip().split()
            if len(fields) < 12:
                continue

            event = fields[0]
            time = float(fields[1])
            from_node = fields[2]
            to_node = fields[3]
            size = int(fields[5])
            pkt_id = fields[11]

            if event == "+":
                sent += 1
                if start is None:
                    start = time
                packet_sizes.append(size)

            if event == "r":
                recv += 1
                end = time

            if event == "d":
                drop += 1

            link_key = f"{from_node}->{to_node}"
            if event == "+":
                all_enqueue_times[link_key][pkt_id] = time
            elif event == "-" and pkt_id in all_enqueue_times[link_key]:
                wait = time - all_enqueue_times[link_key].pop(pkt_id)
                all_waiting_times[link_key].append(wait)

    duration = (end - start) if end and start else 1
    throughput_kbps = sum(packet_sizes) * 8 / duration / 1000
    total_waits = sum(len(waits) for waits in all_waiting_times.values())
    total_wait_time = sum(sum(waits) for waits in all_waiting_times.values())
    avg_wait_ms = (total_wait_time / total_waits) * 1000 if total_waits else 0
    drop_rate = (drop / sent * 100) if sent else 0

    return {
        "sent": sent,
        "received": recv,
        "dropped": drop,
        "drop_rate": drop_rate,
        "throughput": throughput_kbps,
        "avg_wait": avg_wait_ms
    }

# 🎨 Renkler
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# 📊 Tablolu çıktı
results = {name: extract_metrics(path) for name, path in trace_files.items()}

print(f"\n📊 {CYAN}Bandwidth Strategy Comparison{RESET}")
print(f"{'Scenario':<18} | {'Avg. Wait (ms)':>15} | {'Drop Rate (%)':>15} | {'Throughput (Kbps)':>20}")
print("-" * 75)

for name, data in results.items():
    print(f"{name:<18} | {data['avg_wait']:>15.3f} | {data['drop_rate']:>15.2f} | {data['throughput']:>20.2f}")

# 📈 Karşılaştırmalı analiz
base = results["64Kb Bottleneck"]
opt = results["256Kb Optimized"]

wait_diff = base['avg_wait'] - opt['avg_wait']
wait_pct = (wait_diff / base['avg_wait']) * 100

throughput_diff = opt['throughput'] - base['throughput']
throughput_pct = (throughput_diff / base['throughput']) * 100

drop_diff = base['drop_rate'] - opt['drop_rate']

print(f"\n📈 {YELLOW}Analysis:{RESET}")
print(f"- Average waiting time reduced by {GREEN}{wait_diff:.3f} ms ({wait_pct:.2f}%){RESET} with optimized bandwidth.")
print(f"- Throughput increased by {GREEN}{throughput_diff:.2f} Kbps ({throughput_pct:.2f}%){RESET} with optimized bandwidth.")
print(f"- Drop rate decreased by {GREEN}{drop_diff:.2f}%{RESET} with optimized bandwidth.")

