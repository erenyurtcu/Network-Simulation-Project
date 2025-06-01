import os

# Terminal color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Trace files to compare
trace_files = {
    "DropTail": "case3_1_tcp_delay_droptail.trace",
    "RED": "case3_2_tcp_delay_red.trace"
}

def extract_metrics(trace_file):
    sent = recv = drop = 0
    packet_sizes = []
    start = end = None
    enqueue_times = {}
    waiting_times = []

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

            if from_node == "0" and to_node == "2":
                if event == "+":
                    enqueue_times[pkt_id] = time
                elif event == "-" and pkt_id in enqueue_times:
                    wait = time - enqueue_times[pkt_id]
                    waiting_times.append(wait)

    duration = (end - start) if end and start else 1
    throughput_kbps = sum(packet_sizes) * 8 / duration / 1000  # Kbps
    avg_wait_ms = (sum(waiting_times) / len(waiting_times)) * 1000 if waiting_times else 0
    drop_rate = (drop / sent * 100) if sent else 0

    return {
        "sent": sent,
        "received": recv,
        "dropped": drop,
        "drop_rate": drop_rate,
        "throughput": throughput_kbps,
        "avg_wait": avg_wait_ms,
        "wait_samples": len(waiting_times)
    }

# Analyze both trace files
results = {name: extract_metrics(path) for name, path in trace_files.items()}

# Print comparison table
print(f"\n📊 {CYAN}Queueing Strategy Comparison{RESET}")
print(f"{'Queue Type':<10} | {'Avg. Wait (ms)':>15} | {'Drop Rate (%)':>15} | {'Throughput (Kbps)':>20}")
print("-" * 65)
for name, data in results.items():
    wait_color = GREEN if name == "RED" and data["avg_wait"] < results["DropTail"]["avg_wait"] else RESET
    drop_color = RED if data["drop_rate"] > 1 else GREEN
    tp_color = GREEN if data["throughput"] > 1000 else YELLOW
    print(f"{name:<10} | {wait_color}{data['avg_wait']:>15.3f}{RESET} | "
          f"{drop_color}{data['drop_rate']:>15.2f}{RESET} | "
          f"{tp_color}{data['throughput']:>20.2f}{RESET}")

# Analysis summary
dt = results["DropTail"]
red = results["RED"]

wait_diff = dt['avg_wait'] - red['avg_wait']
wait_pct = (wait_diff / dt['avg_wait']) * 100 if dt['avg_wait'] else 0

throughput_diff = dt['throughput'] - red['throughput']
throughput_pct = (throughput_diff / dt['throughput']) * 100 if dt['throughput'] else 0

drop_diff = red['drop_rate'] - dt['drop_rate']

print(f"\n📈 {YELLOW}Analysis:{RESET}")
print(f"- Average waiting time reduced by {GREEN}{wait_diff:.3f} ms ({wait_pct:.2f}%){RESET} with RED.")
print(f"- Throughput decreased by {RED}{throughput_diff:.2f} Kbps ({throughput_pct:.2f}%){RESET} with RED.")
print(f"- Drop rate increased by {RED}{drop_diff:.2f}%{RESET} with RED.\n")

