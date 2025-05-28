import os
import re
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")

def extract_case1_params(ns_filename):
    interval = None
    bandwidth = None
    tracefile = None
    with open(ns_filename, "r") as file:
        for line in file:
            if "set tracefileName" in line:
                match = re.search(r"\"(.+\.trace)\"", line)
                if match:
                    tracefile = match.group(1)
            elif "$cbr set interval_" in line:
                match = re.search(r"interval_\s+([\d\.]+)", line)
                if match:
                    interval = float(match.group(1))
            elif "duplex-link" in line and "$n1" in line:
                match = re.search(r"duplex-link\s+\$n1\s+\$r1\s+([\d\.]+)Mb", line)
                if match:
                    bandwidth = float(match.group(1))
    return tracefile, interval, bandwidth

def analyze_trace(trace_file):
    sent = recv = drop = 0
    start = end = None
    packet_sizes = []
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
            elif event == "r":
                recv += 1
                end = time
            elif event == "d":
                drop += 1

            if from_node == "0" and to_node == "2":
                if event == "+":
                    enqueue_times[pkt_id] = time
                elif event == "-" and pkt_id in enqueue_times:
                    waiting_times.append(time - enqueue_times[pkt_id])

    duration = (end - start) if start and end else 1
    throughput = sum(packet_sizes) * 8 / duration / 1000  # kbps
    drop_rate = drop / sent * 100 if sent else 0
    avg_wait = sum(waiting_times) / len(waiting_times) * 1000 if waiting_times else 0

    return sent, recv, drop, duration, throughput, drop_rate, avg_wait

# 🔁 Sadece case1_*.ns dosyalarını analiz et
data = []
for file in os.listdir():
    if file.startswith("case1_") and file.endswith(".ns"):
        tracefile, interval, bandwidth = extract_case1_params(file)
        if not tracefile or not os.path.exists(tracefile):
            print(f"[!] Atlandı: {file} (tracefile yok)")
            continue
        sent, recv, drop, dur, tp, dr, wait = analyze_trace(tracefile)
        data.append({
            "name": file,
            "interval": interval,
            "bandwidth": bandwidth,
            "throughput": tp,
            "drop_rate": dr,
            "avg_wait": wait
        })

# ✅ Grafik 1: Drop Rate vs Avg. Waiting Time
plt.figure(figsize=(8, 6))
x = [d["drop_rate"] for d in data]
y = [d["avg_wait"] for d in data]
labels = [d["name"] for d in data]
plt.scatter(x, y, s=100, color="red")
for i, label in enumerate(labels):
    plt.annotate(label, (x[i], y[i]))
plt.xlabel("Drop Oranı (%)")
plt.ylabel("Ortalama Bekleme Süresi (ms)")
plt.title("Drop Rate vs Avg. Waiting Time")
plt.grid(True)
plt.tight_layout()
plt.show()

# ✅ Grafik 2: Interval vs Throughput
plt.figure(figsize=(8, 6))
x = [d["interval"] for d in data]
y = [d["throughput"] for d in data]
plt.scatter(x, y, s=100, color="blue")
for i, label in enumerate(labels):
    plt.annotate(label, (x[i], y[i]))
plt.xlabel("Interval (s)")
plt.ylabel("Throughput (Kbps)")
plt.title("Interval vs Throughput")
plt.grid(True)
plt.tight_layout()
plt.show()

# ✅ Grafik 3: Bandwidth vs Throughput
plt.figure(figsize=(8, 6))
x = [d["bandwidth"] for d in data]
y = [d["throughput"] for d in data]
plt.scatter(x, y, s=100, color="green")
for i, label in enumerate(labels):
    plt.annotate(label, (x[i], y[i]))
plt.xlabel("Bandwidth (Mb)")
plt.ylabel("Throughput (Kbps)")
plt.title("Bandwidth vs Throughput")
plt.grid(True)
plt.tight_layout()
plt.show()

