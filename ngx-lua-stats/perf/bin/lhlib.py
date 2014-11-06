#!/usr/bin/env python
#-*- encoding:utf-8 

import socket

def get_ip_by_host(host):
    ip = None
    try:
        r = socket.getaddrinfo(host.strip(),None)
        ip = r[0][4][0]
    except socket.gaierror:
        pass
    return ip

if __name__ == '__main__':
    print get_ip_by_host("")
