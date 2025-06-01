import os
from collections import defaultdict

# .last_trace_file'dan trace dosyasını al
try:
    with open(".last_trace_file", "r") as f:
        trace_file = f.read().strip()
except FileNotFoundError:
    print("❌ Error: '.last_trace_file' not found. Please run a .ns file first.")
    exit(1)

if not os.path.exists(trace_file):
    print(f"❌ Error: Trace file '{trace_file}' not found.")
    exit(1)

sent = 0
recv = 0
drop = 0
packet_sizes = []
start = None
end = None

# Kuyruk verileri
all_enqueue_times = defaultdict(dict)   # {from->to: {pkt_id: enqueue_time}}
all_waiting_times = defaultdict(list)   # {from->to: [waits]}

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

# Metirk hesaplamaları
duration = (end - start) if end and start else 1
throughput = sum(packet_sizes) * 8 / duration  # bit/s
drop_rate = (drop / sent * 100) if sent else 0

# Renkler
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

drop_color = RED if drop_rate > 5 else (YELLOW if drop_rate > 1 else GREEN)
throughput_color = GREEN if throughput > 1000 else YELLOW
duration_color = CYAN if duration < 60 else RESET

# Genel başlık
trace_name = os.path.splitext(os.path.basename(trace_file))[0]
print(f"\n📊 NS-2 Trace Analysis Results — {RED}{trace_name}{RESET}")
print(f"📦 Sent packets:              {CYAN}{sent}{RESET}")
print(f"📥 Received packets:          {CYAN}{recv}{RESET}")
print(f"❌ Dropped packets:           {drop_color}{drop}{RESET}")
print(f"📉 Drop Rate:                 {drop_color}%{drop_rate:.2f}{RESET}")
print(f"⏱ Simulation duration:       {duration_color}{duration:.2f} seconds{RESET}")
print(f"📈 Throughput:                {throughput_color}{throughput / 1000:.2f} Kbps{RESET}")

# Her bağlantı için ortalama bekleme süresi
print(f"\n🕒 Avg. Waiting Times per Link:")
for link, waits in sorted(all_waiting_times.items()):
    if waits:
        avg = sum(waits) / len(waits)
        print(f"   {link:<7} ➜ {YELLOW}{avg * 1000:.3f} ms{RESET} ({len(waits)} packets)")

# Genel ortalama bekleme süresi
total_waits = sum(len(waits) for waits in all_waiting_times.values())
total_wait_time = sum(sum(waits) for waits in all_waiting_times.values())
overall_avg_wait = (total_wait_time / total_waits) * 1000 if total_waits else 0

wait_color = RED if overall_avg_wait > 500 else (YELLOW if overall_avg_wait > 200 else GREEN)
print(f"\n🕒 Overall Avg. Waiting Time: {wait_color}{overall_avg_wait:.3f} ms{RESET} ({total_waits} total packets)\n")

