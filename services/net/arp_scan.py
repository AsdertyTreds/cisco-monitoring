import scapy.all as scapy
import socket


def arp(ip, iface, mac: str = 'ff:ff:ff:ff:ff:ff'):
    ret = {}

    arp_r = scapy.ARP(pdst=ip)
    br = scapy.Ether(dst=mac)
    request = br/arp_r
    answered, unanswered = scapy.srp(request, timeout=15, iface=iface, verbose=0)
    name = None
    for i in answered:
        ip, mac = i[1].psrc, i[1].hwsrc
        if ip:
            try:
                name = socket.gethostbyaddr(ip)
            except socket.herror as e:
                name = (e.strerror, [], [ip])
        ret[mac] = name

    return ret

# intf = get_windows_if_list()
# for i in intf:
#     print(i.get('name'))
