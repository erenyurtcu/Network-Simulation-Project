import os
import re
import matplotlib.pyplot as plt
import pandas as pd

def parse_trace_file(trace_file):
    sent = 0
    drop = 0
    packet_sizes = []
    start = None
    end = None

    with open(trace_file, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 12:
                continue

            event = parts[0]
            time = float(parts[1])
            pkt_type = parts[4]
            pkt_size = int(parts[5])

            if pkt_type != "cbr":
                continue

            if event == "+":
                sent += 1
                packet_sizes.append(pkt_size)
                if start is None:
                    start = time
            elif event == "r":
                end = time
            elif event == "d":
                drop += 1

    duration = (end - start) if (start and end) else 1
    throughput = sum(packet_sizes) * 8 / duration / 1000  # Kbps
    drop_rate = (drop / sent * 100) if sent else 0

    return sent, drop, round(throughput, 2), round(drop_rate, 2)

def get_packet_size_from_filename(filename):
    match = re.search(r"pkt(\d+)", filename)
    return int(match.group(1)) if match else None

def collect_case2_data(folder="."):
    results = {"packet_size": [], "sent_packets": [], "dropped_packets": [], "throughput_kbps": [], "drop_rate": []}
    for file in os.listdir(folder):
        if file.startswith("case2") and file.endswith(".trace"):
            pkt_size = get_packet_size_from_filename(file)
            if pkt_size is None:
                continue
            sent, dropped, throughput, drop_rate = parse_trace_file(os.path.join(folder, file))
            results["packet_size"].append(pkt_size)
            results["sent_packets"].append(sent)
            results["dropped_packets"].append(dropped)
            results["throughput_kbps"].append(throughput)
            results["drop_rate"].append(drop_rate)
    return pd.DataFrame(results).sort_values("packet_size")

def plot_metric(df, column, ylabel, title, color, marker):
    plt.figure()
    plt.plot(df["packet_size"], df[column], marker=marker, color=color, linewidth=2)
    plt.title(f"{title} vs Packet Size")
    plt.xlabel("Packet Size (Bytes)")
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    df = collect_case2_data()

    print("\n📊 CASE2 Trace Summary (Same as analyze_trace.py):\n")
    print(df.to_string(index=False))

    plot_metric(df, "sent_packets", "Sent Packets", "Sent Packets", "blue", "o")
    plot_metric(df, "dropped_packets", "Dropped Packets", "Dropped Packets", "red", "s")
    plot_metric(df, "throughput_kbps", "Throughput (Kbps)", "Throughput", "green", "^")
    plot_metric(df, "drop_rate", "Drop Rate (%)", "Drop Rate", "orange", "x")

