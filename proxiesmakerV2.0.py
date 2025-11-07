import requests
import threading
import time
import os
import json
import sys
from queue import Queue
from datetime import datetime
from colorama import Fore, Back, Style, init

# Enable colors on Windows
init(autoreset=True)

class ProxyChecker:
    def __init__(self):
        self.urls = {
            "http": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "socks4": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "socks5": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        }
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/119.0.0.0 Safari/537.36"
        }
        
        self.config = {
            "test_url": "http://example.com",
            "max_proxies": 300,
            "thread_count": 80,
            "timeout": 8,
            "save_logs": True,
            "export_format": "txt"  # txt, json, csv
        }
        
        self.stats = {
            "total": 0,
            "tested": 0,
            "working": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None
        }
        
        self.working_proxies = []
        self.failed_proxies = []
        self.lock = threading.Lock()
        
    def print_banner(self):
        """Print colored banner"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
{Fore.CYAN}║                                                              ║
{Fore.CYAN}║  {Fore.YELLOW}██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗                   {Fore.CYAN}║
{Fore.CYAN}║  {Fore.YELLOW}██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝                   {Fore.CYAN}║
{Fore.CYAN}║  {Fore.YELLOW}██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝                    {Fore.CYAN}║
{Fore.CYAN}║  {Fore.YELLOW}██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝                     {Fore.CYAN}║
{Fore.CYAN}║  {Fore.YELLOW}██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║                      {Fore.CYAN}║
{Fore.CYAN}║  {Fore.YELLOW}╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝                      {Fore.CYAN}║
{Fore.CYAN}║                                                              ║
{Fore.CYAN}║           {Fore.GREEN}Enhanced Proxy Checker - Version 2.0{Fore.CYAN}              ║
{Fore.CYAN}║            {Fore.MAGENTA}High Speed • Premium Quality • Beautiful UI{Fore.CYAN}       ║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def print_menu(self):
        """Print main menu"""
        menu = f"""
{Fore.CYAN}┌─────────────────────────────────────────────────┐
{Fore.CYAN}│                   {Fore.YELLOW}Main Menu{Fore.CYAN}                    │
{Fore.CYAN}├─────────────────────────────────────────────────┤
{Fore.CYAN}│  {Fore.GREEN}1.{Fore.WHITE} Check All Proxy Types                      {Fore.CYAN}│
{Fore.CYAN}│  {Fore.GREEN}2.{Fore.WHITE} Check Specific Proxy Type                  {Fore.CYAN}│
{Fore.CYAN}│  {Fore.GREEN}3.{Fore.WHITE} View Current Settings                      {Fore.CYAN}│
{Fore.CYAN}│  {Fore.GREEN}4.{Fore.WHITE} Modify Settings                           {Fore.CYAN}│
{Fore.CYAN}│  {Fore.GREEN}5.{Fore.WHITE} View Statistics                           {Fore.CYAN}│
{Fore.CYAN}│  {Fore.GREEN}6.{Fore.WHITE} Export Results                            {Fore.CYAN}│
{Fore.CYAN}│  {Fore.GREEN}7.{Fore.WHITE} Clear Memory                              {Fore.CYAN}│
{Fore.CYAN}│  {Fore.RED}0.{Fore.WHITE} Exit                                       {Fore.CYAN}│
{Fore.CYAN}└─────────────────────────────────────────────────┘
        """
        print(menu)

    def clear_screen(self):
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def check_proxy(self, proto, proxy, working_list, failed_list):
        """Check a single proxy"""
        proxies = {
            "http": f"{proto}://{proxy}",
            "https": f"{proto}://{proxy}",
        }
        
        try:
            start_time = time.time()
            response = requests.get(
                self.config["test_url"], 
                proxies=proxies, 
                timeout=self.config["timeout"], 
                headers=self.headers
            )
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            if response.status_code == 200:
                with self.lock:
                    working_list.append({
                        "proxy": proxy,
                        "protocol": proto,
                        "response_time": response_time,
                        "status": "working"
                    })
                    self.stats["working"] += 1
                    print(f"{Fore.GREEN}✅ {proto.upper():<7} {Fore.YELLOW}{proxy:<21} {Fore.GREEN}({response_time}ms)")
            else:
                with self.lock:
                    failed_list.append({"proxy": proxy, "protocol": proto, "reason": f"Status {response.status_code}"})
                    self.stats["failed"] += 1
                    
        except Exception as e:
            with self.lock:
                failed_list.append({"proxy": proxy, "protocol": proto, "reason": str(e)})
                self.stats["failed"] += 1
                
        with self.lock:
            self.stats["tested"] += 1
            
    def worker(self, proto, queue, working_list, failed_list):
        """Worker function for threads"""
        while not queue.empty():
            try:
                proxy = queue.get(timeout=1)
                self.check_proxy(proto, proxy, working_list, failed_list)
                queue.task_done()
            except:
                break

    def show_progress_bar(self, current, total, prefix="Progress", suffix="", length=40):
        """Show progress bar"""
        if total == 0:
            return
        percent = (current / total) * 100
        filled_length = int(length * current // total)
        bar = '█' * filled_length + '░' * (length - filled_length)
        print(f'\r{Fore.CYAN}{prefix} |{Fore.GREEN}{bar}{Fore.CYAN}| {percent:.1f}% {suffix}', end='', flush=True)

    def test_proxies(self, protocol=None):
        """Test proxies"""
        self.clear_screen()
        self.print_banner()
        
        protocols_to_test = [protocol] if protocol else list(self.urls.keys())
        
        print(f"{Fore.YELLOW}🚀 Starting proxy testing...")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        self.stats = {"total": 0, "tested": 0, "working": 0, "failed": 0, "start_time": time.time()}
        self.working_proxies.clear()
        self.failed_proxies.clear()
        
        for proto in protocols_to_test:
            print(f"\n{Fore.MAGENTA}📡 Fetching {proto.upper()} proxies...")
            
            try:
                response = requests.get(self.urls[proto], headers=self.headers, timeout=15)
                response.raise_for_status()
                raw_proxies = response.text.strip().splitlines()
                
                # Limit number of proxies
                proxies_to_test = raw_proxies[:self.config["max_proxies"]]
                self.stats["total"] += len(proxies_to_test)
                
                print(f"{Fore.GREEN}✅ Fetched {len(proxies_to_test)} {proto} proxies")
                print(f"{Fore.YELLOW}🔍 Testing {proto.upper()} proxies...")
                print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                
                # Create queue
                queue = Queue()
                for proxy in proxies_to_test:
                    queue.put(proxy)
                
                working_list = []
                failed_list = []
                
                # Create threads
                threads = []
                for _ in range(min(self.config["thread_count"], len(proxies_to_test))):
                    thread = threading.Thread(
                        target=self.worker, 
                        args=(proto, queue, working_list, failed_list)
                    )
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                
                # Save results
                if working_list:
                    filename = f"{proto}_working_proxies.txt"
                    with open(filename, "w", encoding="utf-8") as f:
                        for item in working_list:
                            f.write(f"{item['proxy']}\n")
                    print(f"\n{Fore.GREEN}📂 Saved {len(working_list)} working proxies to {filename}")
                
                self.working_proxies.extend(working_list)
                self.failed_proxies.extend(failed_list)
                
            except Exception as e:
                print(f"{Fore.RED}❌ Error fetching {proto} proxies: {e}")
        
        self.stats["end_time"] = time.time()
        self.show_final_results()

    def show_final_results(self):
        """Show final results"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        success_rate = (self.stats["working"] / self.stats["total"]) * 100 if self.stats["total"] > 0 else 0
        
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"{Fore.CYAN}║                        {Fore.YELLOW}Final Results{Fore.CYAN}                          ║")
        print(f"{Fore.CYAN}╠══════════════════════════════════════════════════════════════╣")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Total Proxies:{Fore.GREEN} {self.stats['total']:<15} {Fore.CYAN}                     ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Working Proxies:{Fore.GREEN} {self.stats['working']:<13} {Fore.CYAN}                   ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Failed Proxies:{Fore.RED} {self.stats['failed']:<14} {Fore.CYAN}                    ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Success Rate:{Fore.YELLOW} {success_rate:.1f}%{Fore.CYAN}                               ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Duration:{Fore.MAGENTA} {duration:.2f} seconds{Fore.CYAN}                           ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Speed:{Fore.MAGENTA} {self.stats['total']/duration:.2f} proxies/sec{Fore.CYAN}                  ║")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝")
        
        if self.stats["working"] > 0:
            print(f"\n{Fore.GREEN}🎉 Found {self.stats['working']} working proxies!")
        else:
            print(f"\n{Fore.RED}😞 No working proxies found")

    def show_settings(self):
        """Show current settings"""
        self.clear_screen()
        print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"{Fore.CYAN}║                       {Fore.YELLOW}Current Settings{Fore.CYAN}                        ║")
        print(f"{Fore.CYAN}╠══════════════════════════════════════════════════════════════╣")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Test URL:{Fore.GREEN} {self.config['test_url']:<35} {Fore.CYAN}          ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Max Proxies:{Fore.GREEN} {self.config['max_proxies']:<15} {Fore.CYAN}                    ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Thread Count:{Fore.GREEN} {self.config['thread_count']:<14} {Fore.CYAN}                   ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Timeout:{Fore.GREEN} {self.config['timeout']} seconds{Fore.CYAN}                            ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Save Logs:{Fore.GREEN} {'Yes' if self.config['save_logs'] else 'No'}{Fore.CYAN}                                ║")
        print(f"{Fore.CYAN}║  {Fore.WHITE}Export Format:{Fore.GREEN} {self.config['export_format'].upper()}{Fore.CYAN}                             ║")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝")

    def modify_settings(self):
        """Modify settings"""
        self.clear_screen()
        self.print_banner()
        print(f"{Fore.YELLOW}⚙️  Modify Settings")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        try:
            print(f"{Fore.WHITE}1. Current test URL: {Fore.GREEN}{self.config['test_url']}")
            new_url = input(f"{Fore.YELLOW}New test URL (leave empty to keep current): ").strip()
            if new_url:
                self.config['test_url'] = new_url
            
            print(f"{Fore.WHITE}2. Current max proxies: {Fore.GREEN}{self.config['max_proxies']}")
            new_max = input(f"{Fore.YELLOW}New max proxies (leave empty to keep current): ").strip()
            if new_max.isdigit():
                self.config['max_proxies'] = int(new_max)
            
            print(f"{Fore.WHITE}3. Current thread count: {Fore.GREEN}{self.config['thread_count']}")
            new_threads = input(f"{Fore.YELLOW}New thread count (leave empty to keep current): ").strip()
            if new_threads.isdigit():
                self.config['thread_count'] = int(new_threads)
            
            print(f"{Fore.WHITE}4. Current timeout: {Fore.GREEN}{self.config['timeout']} seconds")
            new_timeout = input(f"{Fore.YELLOW}New timeout in seconds (leave empty to keep current): ").strip()
            if new_timeout.replace('.','').isdigit():
                self.config['timeout'] = float(new_timeout)
            
            print(f"{Fore.GREEN}✅ Settings updated successfully!")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error updating settings: {e}")

    def export_results(self):
        """Export results"""
        if not self.working_proxies:
            print(f"{Fore.RED}❌ No results to export. Test proxies first.")
            return
        
        self.clear_screen()
        print(f"{Fore.YELLOW}📁 Export Results")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export TXT
        txt_filename = f"working_proxies_{timestamp}.txt"
        with open(txt_filename, "w", encoding="utf-8") as f:
            for proxy in self.working_proxies:
                f.write(f"{proxy['proxy']}\n")
        print(f"{Fore.GREEN}✅ Exported {len(self.working_proxies)} proxies to {txt_filename}")
        
        # Export JSON
        json_filename = f"proxy_results_{timestamp}.json"
        results = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "working_proxies": self.working_proxies,
            "failed_proxies": self.failed_proxies[:100]  # First 100 failed only to save space
        }
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"{Fore.GREEN}✅ Exported detailed report to {json_filename}")

    def clear_memory(self):
        """Clear memory"""
        self.working_proxies.clear()
        self.failed_proxies.clear()
        self.stats = {"total": 0, "tested": 0, "working": 0, "failed": 0}
        print(f"{Fore.GREEN}✅ Memory cleared successfully!")

    def run(self):
        """Run main program"""
        while True:
            self.clear_screen()
            self.print_banner()
            self.print_menu()
            
            try:
                choice = input(f"{Fore.YELLOW}Choose from menu: ").strip()
                
                if choice == "1":
                    self.test_proxies()
                    input(f"\n{Fore.CYAN}Press any key to continue...")
                    
                elif choice == "2":
                    print(f"{Fore.YELLOW}Available proxy types:")
                    print(f"{Fore.GREEN}1. HTTP")
                    print(f"{Fore.GREEN}2. SOCKS4") 
                    print(f"{Fore.GREEN}3. SOCKS5")
                    
                    proto_choice = input(f"{Fore.YELLOW}Choose proxy type (1-3): ").strip()
                    protocols = {"1": "http", "2": "socks4", "3": "socks5"}
                    
                    if proto_choice in protocols:
                        self.test_proxies(protocols[proto_choice])
                        input(f"\n{Fore.CYAN}Press any key to continue...")
                    else:
                        print(f"{Fore.RED}❌ Invalid choice!")
                        time.sleep(2)
                        
                elif choice == "3":
                    self.show_settings()
                    input(f"\n{Fore.CYAN}Press any key to continue...")
                    
                elif choice == "4":
                    self.modify_settings()
                    input(f"\n{Fore.CYAN}Press any key to continue...")
                    
                elif choice == "5":
                    if self.stats["total"] > 0:
                        self.show_final_results()
                    else:
                        print(f"{Fore.RED}❌ No statistics available. Test proxies first.")
                    input(f"\n{Fore.CYAN}Press any key to continue...")
                    
                elif choice == "6":
                    self.export_results()
                    input(f"\n{Fore.CYAN}Press any key to continue...")
                    
                elif choice == "7":
                    self.clear_memory()
                    input(f"\n{Fore.CYAN}Press any key to continue...")
                    
                elif choice == "0":
                    print(f"{Fore.YELLOW}👋 Thank you for using Enhanced Proxy Checker!")
                    print(f"{Fore.CYAN}Developed with ❤️ for the community")
                    break
                    
                else:
                    print(f"{Fore.RED}❌ Invalid choice! Choose a number from 0-7")
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}👋 Program stopped by user")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Unexpected error: {e}")
                time.sleep(3)

if __name__ == "__main__":
    # Install required libraries
    try:
        import colorama
        import requests
    except ImportError:
        print("Please install required libraries:")
        print("pip install colorama requests")
        sys.exit(1)
    
    checker = ProxyChecker()
    checker.run()