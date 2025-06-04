import os
import re
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")  # GUI destekli grafik

# --- NS dosyasından interval, bandwidth, trace file ismini çek
def extract_ns_parameters(ns_filename):
    interval = None
    bandwidth = None
    tracefile = None
    with open(ns_filename, "r") as file:
        for line in file:
            if "set tracefileName" in line:
                match = re.search(r"\"(.+\.trace)\"", line)
                if match:
                    tracefile = match.group(1)

            # Tüm "interval_" içeren satırları yakala (cbr1, cbr4 fark etmez)
            elif "interval_" in line:
                match = re.search(r"interval_[^0-9]*([\d\.]+)", line)
                if match:
                    interval = float(match.group(1))

            # Sadece n1–r1 bağlantısından bandwidth çekiyoruz (diğerleri istenirse eklenebilir)
            elif "duplex-link" in line and "$n1" in line:
                match = re.search(r"duplex-link\s+\$n1\s+\$r1\s+([\d\.]+)Mb", line)
                if match:
                    bandwidth = float(match.group(1))

    return tracefile, interval, bandwidth

# --- Trace dosyasını analiz et
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

            if event == "+":
                enqueue_times[pkt_id] = time
            elif event == "-" and pkt_id in enqueue_times:
                waiting_times.append(time - enqueue_times[pkt_id])

    duration = (end - start) if start and end else 1
    throughput = sum(packet_sizes) * 8 / duration / 1000  # kbps
    drop_rate = drop / sent * 100 if sent else 0
    avg_wait = sum(waiting_times) / len(waiting_times) * 1000 if waiting_times else 0

    return sent, recv, drop, duration, throughput, drop_rate, avg_wait

# --- Tüm case1_*.ns dosyalarını analiz et
results = []
for file in os.listdir():
    if file.startswith("case1_") and file.endswith(".ns"):
        tracefile, interval, bandwidth = extract_ns_parameters(file)
        if not tracefile or not os.path.exists(tracefile):
            print(f"[Skipped] {file} (trace file not found)")
            continue
        sent, recv, drop, dur, tp, dr, wait = analyze_trace(tracefile)
        results.append({
            "name": file,
            "interval": interval,
            "bandwidth": bandwidth,
            "throughput": tp,
            "drop_rate": dr,
            "avg_wait": wait
        })

# --- Grafik fonksiyonu
def plot_metric(xkey, ykey, xlabel, ylabel, title, color):
    x, y, labels = [], [], []
    for d in results:
        if d[xkey] is not None and d[ykey] is not None:
            x.append(d[xkey])
            y.append(d[ykey])
            labels.append(d["name"])
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, s=100, color=color)
    for i, label in enumerate(labels):
        plt.annotate(label, (x[i], y[i]), fontsize=8, xytext=(5, 5), textcoords="offset points")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# --- 6 Grafik Üretimi ---
plot_metric("interval", "throughput", "Interval (s)", "Throughput (Kbps)", "Interval vs Throughput", "blue")
plot_metric("interval", "drop_rate", "Interval (s)", "Drop Rate (%)", "Interval vs Drop Rate", "red")
plot_metric("interval", "avg_wait", "Interval (s)", "Average Waiting Time (ms)", "Interval vs Avg. Waiting Time", "green")

plot_metric("bandwidth", "throughput", "Bandwidth (Mb)", "Throughput (Kbps)", "Bandwidth vs Throughput", "blue")
plot_metric("bandwidth", "drop_rate", "Bandwidth (Mb)", "Drop Rate (%)", "Bandwidth vs Drop Rate", "red")
plot_metric("bandwidth", "avg_wait", "Bandwidth (Mb)", "Average Waiting Time (ms)", "Bandwidth vs Avg. Waiting Time", "green")

