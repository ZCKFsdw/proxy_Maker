import requests
import threading
from queue import Queue

# روابط بروكسيات (GitHub)
urls = {
    "http": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "socks4": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "socks5": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/119.0.0.0 Safari/537.36"
}

test_url = "http://example.com"

def check_proxy(proto, proxy, working):
    proxies = {
        "http": f"{proto}://{proxy}",
        "https": f"{proto}://{proxy}",
    }
    try:
        r = requests.get(test_url, proxies=proxies, timeout=8, headers=headers)
        if r.status_code == 200:
            print(f"✅ {proto} شغال: {proxy}")
            working.append(proxy)
    except:
        pass

def worker(proto, q, working):
    while not q.empty():
        proxy = q.get()
        check_proxy(proto, proxy, working)
        q.task_done()

for proto, url in urls.items():
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        raw_proxies = res.text.strip().splitlines()

        working = []
        print(f"\n🔍 اختبار بروكسيات {proto} ...")

        q = Queue()
        for proxy in raw_proxies[:300]:  # نجرب 300 بروكسي
            q.put(proxy)

        threads = []
        for _ in range(80):
            t = threading.Thread(target=worker, args=(proto, q, working))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        filename = f"{proto}_proxies.txt"
        with open(filename, "w") as f:
            f.write("\n".join(working))

        print(f"📂 تم حفظ {len(working)} بروكسي شغال في {filename}")

    except Exception as e:
        print(f"❌ خطأ في {proto}: {e}")
