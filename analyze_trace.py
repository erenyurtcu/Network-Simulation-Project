import os
from collections import defaultdict

# .last_trace_file'dan son trace dosyasını oku
try:
    with open(".last_trace_file", "r") as f:
        trace_file = f.read().strip()
except FileNotFoundError:
    print("❌ Hata: '.last_trace_file' bulunamadı. Lütfen bir .ns dosyası çalıştırın.")
    exit(1)

if not os.path.exists(trace_file):
    print(f"❌ Hata: '{trace_file}' dosyası bulunamadı.")
    exit(1)

sent = 0
recv = 0
drop = 0
packet_sizes = []
start = None
end = None

# Bekleme süresi için kuyruk takibi (sadece 0→2 için)
enqueue_times = {}
waiting_times = []

# Tüm bağlantılar için bekleme süresi (yeni eklenen kısım)
all_enqueue_times = defaultdict(dict)   # {link_key: {pkt_id: enqueue_time}}
all_waiting_times = defaultdict(list)   # {link_key: [wait_time1, wait_time2, ...]}

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

        # Gönderilen paket sayımı
        if event == "+":
            sent += 1
            if start is None:
                start = time
            packet_sizes.append(size)

        # Alınan paket sayımı
        if event == "r":
            recv += 1
            end = time

        # Düşen paket sayımı
        if event == "d":
            drop += 1

        # Ortalama bekleme süresi (sadece 0→2 için)
        if from_node == "0" and to_node == "2":
            if event == "+":
                enqueue_times[pkt_id] = time
            elif event == "-" and pkt_id in enqueue_times:
                wait = time - enqueue_times[pkt_id]
                waiting_times.append(wait)

        # 🔁 Tüm bağlantılar için bekleme süresi takibi
        link_key = f"{from_node}->{to_node}"
        if event == "+":
            all_enqueue_times[link_key][pkt_id] = time
        elif event == "-" and pkt_id in all_enqueue_times[link_key]:
            wait = time - all_enqueue_times[link_key].pop(pkt_id)
            all_waiting_times[link_key].append(wait)

# Süre & throughput
duration = (end - start) if end and start else 1
throughput = sum(packet_sizes) * 8 / duration  # bit/s

# Ortalama bekleme süresi (0→2)
avg_wait = sum(waiting_times) / len(waiting_times) if waiting_times else 0

# Drop oranı yüzdesi
drop_rate = (drop / sent * 100) if sent else 0

# ⏬ Sonuçları yazdır
print("📊 NS-2 Trace Analizi Sonuçları")
print(f"📦 Gönderilen paket sayısı:   {sent}")
print(f"📥 Alınan paket sayısı:       {recv}")
print(f"❌ Düşen paket sayısı:        {drop}")
print(f"📉 Drop Oranı:                %{drop_rate:.2f}")
print(f"⏱ Simülasyon süresi:         {duration:.2f} saniye")
print(f"📈 Throughput:                {throughput / 1000:.2f} Kbps")
print(f"🕒 Avg. Waiting Time (0→2):   {avg_wait * 1000:.3f} ms ({len(waiting_times)} paket)")

# 🔁 Tüm bağlantılar için ortalama bekleme süresi yazdır
print("🕒 Ortalama Bekleme Süreleri (Tüm Bağlantılar):")
for link, waits in sorted(all_waiting_times.items()):
    if waits:
        avg = sum(waits) / len(waits)
        print(f"   {link:<7} ➜ {avg * 1000:.3f} ms ({len(waits)} paket)")

