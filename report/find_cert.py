import re
import sys
import psycopg2
import dns.resolver
import requests
from datetime import datetime
from socket import socket
from OpenSSL.crypto import *
from OpenSSL.SSL import Connection, Context, TLSv1_METHOD, WantReadError
from collections import Counter
import time, threading
from queue import Queue
import logging
from count_cert import count_cert

SHARE_Q = Queue()
WORKER_THREAD_NUM = 30
out_text = []

def read_domains(filename):
    with open(filename) as f:
        text = f.read()        
        return re.findall('(.*)\n', text)

def write_DNSres(domain, domain_names):
    with open("dns_result/"+domain+"_DNSres.txt", "w") as f:
        for domain in domain_names:
            try:
                A = dns.resolver.query(domain, "A")
                for i in A.response.answer:
                    f.write(str(i)+'\n')
                f.write('\n')
            except Exception as e:
                print(e)
                f.write("NXDOMAIN for "+domain+'\n\n')

def write_NameServer(domain_names):
    with open("NameServer.txt", "w") as f:
        for domain in domain_names:
            try:
                NS = dns.resolver.query(domain, "NS")
                for i in NS.response.answer:
                    f.write(str(i)+'\n')
                f.write('\n')
            except Exception as e:
                print(e)
                f.write("Can't find nameserver for "+domain+'\n\n')

def find_IP(filename):
    with open(filename) as f:
        text = f.read()
        res = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",text)
        return set(res)

def domain_ssl_connect(domain):            
        try:
            sslcontext = Context(TLSv1_METHOD)
            sslcontext.set_timeout(30)
            s = socket()
            s.connect((domain, 443))
            c = Connection(sslcontext, s)
            c.set_connect_state()
            c.set_tlsext_host_name(domain.encode('utf-8'))
            logging.info("try to establish handshake with %s..." % domain)
            c.do_handshake()
            cert = c.get_peer_certificate()
            logging.info("got certificate!")
            c.shutdown()
            s.close()
            return cert
        except Exception as e:
            logging.info(e)
            logging.info("fail to connect to port 443 with %s" % domain)
            return None

def ip_ssl_connect(ipp):            
        try:
            sslcontext = Context(TLSv1_METHOD)
            sslcontext.set_timeout(30)
            s = socket()
            s.connect((ip, 443))
            c = Connection(sslcontext, s)
            c.set_connect_state()
            logging.info("try to establish handshake with %s..." % ip)
            c.do_handshake()
            cert = c.get_peer_certificate()
            logging.info("got certificate!")
            c.shutdown()
            s.close()
            return cert
        except Exception as e:
            logging.info(e)
            logging.info("fail to connect to port 443 with %s" % ip)
            return None

class MyThread(threading.Thread):
    def __init__(self,func):
        super(MyThread, self).__init__()
        self.func = func
    def run(self):
        self.func()


def domain_worker():
    global SHARE_Q
    global out_text
    while True:
        if not SHARE_Q.empty():
            item = SHARE_Q.get()
            print("processing: "+item)
            cert = domain_ssl_connect(item)
            if cert:
                out_text.append("certfrom "+item+": serial number->"+str(hex(cert.get_serial_number()))+", issuer->"+str(cert.get_issuer())+", subject->"+str(cert.get_subject())+"\n")
            time.sleep(1)
            SHARE_Q.task_done()
        else:
            break

def ip_worker():
    global SHARE_Q
    global out_text
    while True:
        if not SHARE_Q.empty():
            item = SHARE_Q.get()
            print("processing: "+item)
            cert = ip_ssl_connect(item)
            if cert:
                out_text.append("certfrom "+item+": serial number->"+str(hex(cert.get_serial_number()))+", issuer->"+str(cert.get_issuer())+", subject->"+str(cert.get_subject())+"\n")
            time.sleep(1)
            SHARE_Q.task_done()
        else:
            break

def get_cert_from_domains(domain, domain_list):
    with open("cert_from_domain/"+domain+".txt","w") as f:
        global SHARE_Q
        global out_text
        threads = []
        for domain in domain_list:
            SHARE_Q.put(domain)
        for i in range(WORKER_THREAD_NUM):
            thread = MyThread(domain_worker)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        SHARE_Q.join()
        f.write('\n'.join(out_text))

def get_cert_from_IP(domain, ip_list):
    with open("cert_from_ip/"+domain+".txt","w") as f:
        global SHARE_Q
        global out_text
        threads = []
        for ip in ip_list:
            SHARE_Q.put(ip)
        for i in range(WORKER_THREAD_NUM):
            thread = MyThread(ip_worker)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        SHARE_Q.join()
        f.write('\n'.join(out_text))

def query_cert(serial_num):
    res = 0
    try:
        conn = psycopg2.connect("dbname={} user={} host={}".format("certwatch", "guest", "crt.sh"))
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT c.ID FROM certificate c\
                        WHERE x509_serialNumber(c.CERTIFICATE) = decode('{}', 'hex')".format(serial_num))
        res = cursor.fetchall()
        return res
    except Exception as e:
        print("\nerror"+str(e)+", cert: "+serial_num)
        return res

def search_cert(cert_list,domain):
    print("total cert input: %d"%len(cert_list))
    cert_found = []
    f = open("cert_ct/"+domain+".txt","w")
    for cert in cert_list.keys():
        if len(cert)%2:
            serial_num = '0'+cert
        else:
            serial_num = cert
        res = query_cert(serial_num)
        if res:
            f.write("\nfound, cert: "+serial_num+", res: "+str(res))
            cert_found.append(cert)
        else:
            serial_num = '00'+cert
            res = query_cert(serial_num)
            if res:
                cert_found.append(cert)
                f.write("\nfound, cert: "+serial_num+", res: "+str(res))
            else:    
                f.write("\nnot found, cert: "+cert)
    print("total %d cert found in crt.sh database"%len(cert_found))
    f.close()

if __name__ == "__main__":
    domain = sys.argv[1]
    #domain = "sjtu.edu.cn"
    logging.basicConfig(filename='log/'+str(time.time())+"."+domain+'.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

    #ip_list = find_IP("fulldomain/dnsres/"+domain+"_DNSres.txt")
    #get_cert_from_IP(domain, ip_list)

    get_cert_from_domains(domain, read_domains("fulldomain/resolved_domain/"+domain+".txt"))
    
    search_cert(count_cert("cert_from_domain/"+domain+".txt"),domain)
