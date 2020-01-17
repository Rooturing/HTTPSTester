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


def read_domains(filename):
    with open(filename) as f:
        text = f.read()        
        return re.findall('(.*)\n', text)

def find_IP(filename):
    with open(filename) as f:
        text = f.read()
        res = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",text)
        return set(res)

class MyThread(threading.Thread):
    def __init__(self,func):
        super(MyThread, self).__init__()
        self.func = func
    def run(self):
        self.func()

class GetCert:
    def __init__(self, domain, basedir):
        self.domain = domain
        self.domain_list = read_domains(basedir+'/output/domain/resolved_domain/'+domain+'.txt')
        self.basedir = basedir
        self.SHARE_Q = Queue()
        self.LEFT_Q = len(self.domain_list)
        self.WORKER_THREAD_NUM = 30
        self.out_text = []

    def domain_ssl_connect(self, domain):            
        logging.basicConfig(filename=self.basedir+'/output/log/get_cert_from_domain.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
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

    def ip_ssl_connect(self, ip):            
        logging.basicConfig(filename=self.basedir+'/output/log/get_cert_from_ip.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
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


    def domain_worker(self):
        while not self.SHARE_Q.empty():
            item = self.SHARE_Q.get()
            print("processing: "+item)
            cert = self.domain_ssl_connect(item)
            if cert:
                self.out_text.append("certfrom "+item+": serial number->"+str(hex(cert.get_serial_number()))+", issuer->"+str(cert.get_issuer())+", subject->"+str(cert.get_subject())+"\n")
            time.sleep(1)
            print("task done for: "+item)
            self.LEFT_Q = self.LEFT_Q - 1
            print("queue size: %d, %d left." % (self.SHARE_Q.qsize(), self.LEFT_Q))
            self.SHARE_Q.task_done()

    def ip_worker(self):
        while not self.SHARE_Q.empty():
            item = self.SHARE_Q.get()
            print("processing: "+item)
            ert = self.ip_ssl_connect(item)
            if cert:
                self.out_text.append("certfrom "+item+": serial number->"+str(hex(cert.get_serial_number()))+", issuer->"+str(cert.get_issuer())+", subject->"+str(cert.get_subject())+"\n")
            time.sleep(1)
            print("task done for: "+item)
            self.LEFT_Q = self.LEFT_Q - 1
            print("queue size: %d, %d left." % (self.SHARE_Q.qsize(), self.LEFT_Q))
            self.SHARE_Q.task_done()

    def get_cert_from_domains(self):
        with open(self.basedir+"/output/report/cert/cert_from_domain/"+self.domain+"_fd.txt","w") as f:
            threads = []
            for domain in self.domain_list:
                self.SHARE_Q.put(domain)
            for i in range(self.WORKER_THREAD_NUM):
                thread = MyThread(self.domain_worker)
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
            f.write('\n'.join(self.out_text))

    def get_cert_from_IP(self):
        with open(self.basedir+"/output/report/cert/cert_from_ip/"+self.domain+"_fi.txt","w") as f:
            threads = []
            for ip in self.ip_list:
                self.SHARE_Q.put(ip)
            for i in range(self.WORKER_THREAD_NUM):
                thread = MyThread(self.ip_worker)
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
            self.SHARE_Q.join()
            f.write('\n'.join(self.out_text))

    def query_cert(self, serial_num):
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

    def search_cert_in_ct(self, cert_list):
        print("total cert input: %d"%len(cert_list))
        cert_found = []
        f = open(self.basedir+"/output/report/cert/cert_ct/"+self.domain+"_ct.txt","w")
        for cert in cert_list.keys():
            if len(cert)%2:
                serial_num = '0'+cert
            else:
                serial_num = cert
            res = self.query_cert(serial_num)
            if res:
                f.write("\nfound, cert: "+serial_num+", res: "+str(res))
                cert_found.append(cert)
            else:
                serial_num = '00'+cert
                res = self.query_cert(serial_num)
                if res:
                    cert_found.append(cert)
                    f.write("\nfound, cert: "+serial_num+", res: "+str(res))
                else:    
                    f.write("\nnot found, cert: "+cert)
        print("total %d cert found in crt.sh database"%len(cert_found))
        f.close()

if __name__ == "__main__":
    domain = sys.argv[1]

    #ip_list = find_IP("fulldomain/dnsres/"+domain+"_DNSres.txt")
    #get_cert_from_IP(domain, ip_list)

    #get_cert_from_domains(domain, read_domains("fulldomain/resolved_domain/"+domain+".txt"))
    
    #search_cert_in_ct(count_cert("cert_from_domain/"+domain+".txt"),domain)
