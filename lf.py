import socket
import ipaddress
import subprocess
import platform
import threading
import requests
from requests.exceptions import RequestException
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====== CONFIG: Common Ports to Scan ======
COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 554, 8000, 8080, 8888, 3306, 3389]
# Set to False for faster scan (no service/banner info)
SHOW_SERVICE_BANNER = True

# ====== Get Local IP and Calculate Scan Range ======
def get_dynamic_ip_range():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()

    ip = ipaddress.IPv4Address(local_ip)
    octets = str(ip).split('.')
    base1, base2, base3 = int(octets[0]), int(octets[1]), int(octets[2])

    start_block = max(base3 - 2, 0)
    end_block = min(base3 + 2, 255)

    start_ip = ipaddress.IPv4Address(f"{base1}.{base2}.{start_block}.0")
    end_ip = ipaddress.IPv4Address(f"{base1}.{base2}.{end_block}.255")

    return local_ip, start_ip, end_ip

# ====== Ping Checker (Improved) ======
def is_host_alive(ip, ping_timeout=1000, tcp_check_port=80):
    import time
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    timeout = '-w' if platform.system().lower() == 'windows' else '-W'
    try:
        # Increase timeout to 1000ms (1s)
        result = subprocess.run(
            ['ping', param, '1', timeout, str(ping_timeout), str(ip)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            # Double-check with TCP connect to port 80
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                if sock.connect_ex((str(ip), tcp_check_port)) == 0:
                    sock.close()
                    return True
                sock.close()
            except:
                pass
            # If TCP check fails, still return True (ping responded)
            return True
        else:
            return False
    except:
        return False

# ====== Port Scanner with Nmap (Debug Mode, Full Output, Improved Timeout) ======
def scan_ports(ip):
    import subprocess
    import re
    import sys
    open_ports = []
    try:
        port_list = ','.join(str(p) for p in COMMON_PORTS)
        nmap_cmd = [
            'nmap', '-Pn', '-p', port_list, '-T4', '--host-timeout', '180s', str(ip)
        ]
        if SHOW_SERVICE_BANNER:
            nmap_cmd.insert(5, '-sV')  # Insert -sV after port list
        print(f"[DEBUG] Running nmap command: {' '.join(nmap_cmd)}")
        if sys.platform.startswith('win'):
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print('[DEBUG] WARNING: Not running as Administrator. Nmap may not detect open ports correctly on Windows.')
        result = subprocess.run(nmap_cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout
        print(f"[DEBUG] nmap output for {ip}:\n{output}")
        # More robust regex: match lines like '80/tcp open http', with optional banner
        port_line_re = re.compile(r'^(\d+/tcp)\s+open\s+(\S+)(?:\s+(.*))?$', re.MULTILINE)
        for match in port_line_re.finditer(output):
            port_proto = match.group(1)
            service = match.group(2)
            banner = match.group(3) if match.group(3) else ''
            port = port_proto.split('/')[0]
            open_ports.append(f"{port} - {service} {banner}".strip())
        if not open_ports:
            open_ports.append("[DEBUG] No open ports parsed. See above for raw nmap output.")
    except FileNotFoundError:
        open_ports.append("nmap not found: Please install nmap and ensure it is in your PATH.")
    except Exception as e:
        open_ports.append(f"nmap error: {e}")
    return open_ports

# ====== Host Scanner (Improved with ThreadPool) ======
def scan_range(start_ip, end_ip):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    live_hosts = []
    max_threads = 50  # Limit concurrent threads

    def ping_target(ip):
        if is_host_alive(ip):
            print(f"[+] {ip} is ALIVE")
            return str(ip)
        return None

    ip_list = [ipaddress.IPv4Address(ip_int) for ip_int in range(int(start_ip), int(end_ip) + 1)]
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_ip = {executor.submit(ping_target, ip): ip for ip in ip_list}
        for future in as_completed(future_to_ip):
            result = future.result()
            if result:
                live_hosts.append(result)

    return live_hosts

# ====== Output Formatting Helpers ======
def print_banner():
    print(r"""
██╗    ██╗██╗███████╗ █████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗
██║    ██║██║╚══███╔╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔════╝
██║ █╗ ██║██║  ███╔╝ ███████║██████╔╝██║  ██║███████╗█████╗  ██║     
██║███╗██║██║ ███╔╝  ██╔══██║██╔══██╗██║  ██║╚════██║██╔══╝  ██║     
╚███╔███╔╝██║███████╗██║  ██║██║  ██║██████╔╝███████║███████╗╚██████╗
 ╚══╝╚══╝ ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝ ╚═════╝
    """)

def print_header():
    print("=" * 40)
    print("      Network Port Scanner Like A WatchDogs")
    print("=" * 40)
    print()

def print_live_hosts_table(live_hosts):
    if not live_hosts:
        print("[!] No live hosts found.")
        return
    print("+-------------------+")
    print("|   Live Hosts      |")
    print("+-------------------+")
    for ip in live_hosts:
        print(f"| {ip:<17}|")
    print("+-------------------+\n")

def print_host_report(ip, ports):
    print("=" * 40)
    print(f"Host: {ip}")
    print("-" * 40)
    if ports:
        print("Open Ports:")
        print("  PORT   | BANNER")
        print("  -------+------------------------------")
        for entry in ports:
            if ' - ' in entry:
                port, banner = entry.split(' - ', 1)
                print(f"  {int(port):<6} | {banner}")
            else:
                print(f"  {entry}")
    else:
        print("  No common ports open.")
    print("-" * 40 + "\n")

# ====== Scan Live Hosts for Open Ports (Sequential) ======
def scan_live_hosts(live_hosts):
    print("\n[*] Scanning open ports and banners (sequential)...\n")
    results = {}
    total_ports = 0
    for ip in live_hosts:
        try:
            ports = scan_ports(ip)
            results[ip] = ports
        except Exception as e:
            results[ip] = []
            print(f"[!] Error scanning {ip}: {e}")
        print_host_report(ip, results[ip])
        total_ports += len(results[ip])
    print(f"[✓] Scan complete! {len(live_hosts)} host(s) found, {total_ports} open port(s) detected.\n")

# ====== Main Runner ======
def main():
    print_banner()
    print_header()
    local_ip, start_ip, end_ip = get_dynamic_ip_range()
    print(f"[*] Detected Local IP : {local_ip}")
    print(f"[*] Scanning Range    : {start_ip} to {end_ip}\n")

    print("[*] Scanning for live hosts...\n")
    live_hosts = scan_range(start_ip, end_ip)

    print(f"\n[✓] Found {len(live_hosts)} live host(s):\n")
    print_live_hosts_table(live_hosts)

    if live_hosts:
        scan_live_hosts(live_hosts)
    else:
        print("[!] No live hosts found.")

if __name__ == "__main__":
    main()
