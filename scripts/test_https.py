import requests
import random
import os
import re
import logging
import time
import sys
import time, threading
from queue import Queue
import json
import aiohttp
import asyncio
from urllib.parse import urlparse
import certifi


headers = {
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection':'close'}



class MyThread(threading.Thread):
    def __init__(self,func):
        super(MyThread,self).__init__()
        self.func = func
    def run(self):
        self.func()

def read_domains(filename):
    with open(filename) as f:
        text = f.read().strip()
    return re.findall('(.*)\n', text)

class TestHTTPS:

    def __init__(self, domain, basedir):
        self.domain = domain
        self.basedir = basedir
        self.https_test = {'https_default':[],'http_default':[],'https_reachable':[],'http_only':[],'https_only':[],'https_error':[],'https_bad_code':[],'http_bad_code':[],'redirected':[],'unreachable':[]}
        self.WORKER_THREAD_NUM = 50 
        self.SHARE_Q = Queue()
        self.LEFT_Q = 0 

    def get_https_error(self, domain, e):
        #print(e)
        if re.findall(r"hostname .* doesn't match", e):
            self.https_test['https_error'].append(domain+" (host doesn't match)")
        elif re.findall(r"certificate verify failed", e):
            self.https_test['https_error'].append(domain+" (certificate verify failed)")
        elif re.findall(r"tlsv1 unrecognized name", e):
            self.https_test['https_error'].append(domain+" (tlsv1 unrecognized name)")
        elif re.findall(r"ECONNRESET", e):
            self.https_test['unreachable'].append(domain+ " (connection reset)")
        elif re.findall(r"bad handshake", e):
            self.https_test['https_error'].append(domain+ " (bad handshake)")
        else:
            self.https_test['https_error'].append(domain+" (?)")

    def compare_hostname(self, url, domain):
        hostname = urlparse(url).hostname
        if hostname != domain:
            if domain+'->'+hostname not in self.https_test['redirected']:
                self.https_test['redirected'].append(domain+'->'+hostname)
            if re.findall('.'.join(hostname.split('.')[1:]), domain):
                if hostname not in self.domains:
                    self.domains.append(hostname)
                    return 2 # different subdomain, new 
                else:
                    return 2 # different subdomain, already in list
            else:
                return 0 # not a subdomain
        else:
            return 1 # same subdomain

    def req_https_reachable(self, domain, url):
        try:
            logging.info("testing if https is available..")
            path = urlparse(url).path
            res = requests.get("https://"+domain+path, allow_redirects=True, headers=headers, timeout=120, verify=self.basedir+'/scripts/util/trust_store/trust.pem')
            redirect_url = self.find_redirect(res.text)
            if redirect_url:
                if not self.compare_hostname(redirect_url[0], domain):
                    return
                res = requests.get(redirect_url[0], allow_redirects=True, headers=headers, timeout=120, verify=self.basedir+'/scripts/util/trust_store/trust.pem')
            http_status = str(res.status_code)
            url = res.url
            condition = self.compare_hostname(url, domain)
            if condition != 1: # jump to other domains
                return
            if re.match(r"^https://",url):
                if re.match(r"^2",http_status):
                    self.https_test['https_reachable'].append(domain)
                    logging.info(domain+" is https reachable.")
                else:
                    self.https_test['https_bad_code'].append(domain)
                    logging.info("return error status code, http status code: "+http_status)
            else:
                self.https_test['http_only'].append(domain)
        except Exception as e:                   
            logging.info(e)
            if re.findall("SSLError",str(e)):
                self.get_https_error(domain, str(e))
            else:
                logging.info("domain is http only")
                self.https_test['http_only'].append(domain)             

    def req_https_only(self, domain):
        try:
            logging.info("testing if https is available..")
            res = requests.get("https://"+domain, allow_redirects=True, headers=headers, timeout=120, verify=self.basedir+'/scripts/util/trust_store/trust.pem')
            redirect_url = self.find_redirect(res.text)
            if redirect_url:
                if not self.compare_hostname(redirect_url[0], domain):
                    return
                res = requests.get(redirect_url[0], allow_redirects=True, headers=headers, timeout=120, verify=self.basedir+'/scripts/util/trust_store/trust.pem')
            http_status = str(res.status_code)
            url = res.url
            condition = self.compare_hostname(url, domain)
            if condition != 1:
                return
            if re.match(r"^https://",url):
                if re.match(r"^2",http_status):
                    self.https_test['https_only'].append(domain)
                    logging.info(domain+" is https only.")
                else:
                    logging.info("return error status code, http status code: "+http_status)
                    self.https_test['https_bad_code'].append(domain)
        except Exception as e:                   
            logging.info(e)
            if re.findall("SSLError",str(e)):
                self.get_https_error(domain, str(e))
            else:
                self.https_test['unreachable'].append(domain)

    def find_redirect(self, html):

        r = re.findall('<meta.*?url=(.*?)[\"\']>', html, re.IGNORECASE)
        if r:
            if urlparse(r[0]).hostname:
                return r
            else:
                return 0
        r = re.findall('window\.location\.href.*=.*[\'\"](.*?)[\'\"]', html, re.IGNORECASE)
        if r:
            if urlparse(r[0]).hostname:
                return r
            else:
                return 0

    def run_test(self, domain):
        try:
            res1 = requests.get("http://"+domain, allow_redirects=True, headers=headers, timeout=120, verify=self.basedir+'/scripts/util/trust_store/trust.pem')
            redirect_url = self.find_redirect(res1.text)
            if redirect_url:
                if not self.compare_hostname(redirect_url[0], domain):
                    return
                res1 = requests.get(redirect_url[0], allow_redirects=True, headers=headers, timeout=120, verify=self.basedir+'/scripts/util/trust_store/trust.pem')
            http_status = str(res1.status_code)
            url = res1.url
            condition = self.compare_hostname(url, domain)
            if condition == 0:   # jump to another domain, out of testing scope
                return
            elif condition == 1: # same subdomain
                if re.match(r"^https://", url): # use default HTTPS
                    if re.match(r"^2",http_status):
                        self.https_test['https_default'].append(domain)
                        logging.info(domain+" use default https.")
                    else:                           # use default HTTP, try test HTTPS connectivity
                        self.https_test['https_bad_code'].append(domain)
                else:
                    if re.match(r"^2",http_status):
                        self.https_test['http_default'].append(domain) 
                        logging.info(domain+" use default http.")
                        self.req_https_reachable(domain, url)
                    else:
                        self.https_test['http_bad_code'].append(domain)
                        self.req_https_only(domain)
            elif condition == 2: # http:// jump to different subdomain, testing if https:// might not jump to different subdomains
                self.req_https_reachable(domain, url)
        except Exception as e:
            #print(str(e))
            logging.info(e)
            if re.findall(r"SSLError", str(e)):
                self.get_https_error(domain, str(e))
            else:
                self.req_https_only(domain)
    logging.info("\n")


    def worker(self):
        while not self.SHARE_Q.empty():
            item = self.SHARE_Q.get()
            self.run_test(item)
            print("task done for domain: "+item)
            self.LEFT_Q = self.LEFT_Q - 1
            print("queue size: %d, %d left" % (self.SHARE_Q.qsize(), self.LEFT_Q))
            self.SHARE_Q.task_done()

    def test_https(self): 
        
        self.domains = read_domains(self.basedir+"/output/domain/resolved_domain/"+self.domain+".txt")
        
        f_json = open(self.basedir+"/output/report/test_https/"+self.domain+".json","w")
        
        threads = []

        self.LEFT_Q = len(self.domains)
        random.shuffle(self.domains)
        for d in self.domains:
            self.SHARE_Q.put(d)
        for i in range(self.WORKER_THREAD_NUM):
            thread = MyThread(self.worker)
            thread.start()
            threads.append(thread)
        startTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for thread in threads:
            thread.join()



        endTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print('all done! start: '+startTime+', end: '+endTime)
        print('%d domains tested' % (len(self.domains)))
        
        json.dump(self.https_test,f_json)

        f_json.close()

        #同时输出txt格式
        f_txt = open(self.basedir+"/output/report/test_https/"+self.domain+".txt","w")
        for key in self.https_test:
            if re.match(r'https_default',key) or re.match(r'https_only',key) or re.match(r'https_reachable',key) or re.match(r'https_error',key):
                for d in self.https_test[key]:
                    f_txt.write('https://' + d.split('(')[0] + '\n')
            elif re.match(r'http_only',key):
                for d in self.https_test[key]:
                    f_txt.write('http://' + d + '\n')
        f_txt.close()

    def run(self):
        logging.basicConfig(filename=self.basedir+'/output/report/test_https/log/'+str(time.time())+"."+self.domain+'.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        self.test_https()

if __name__ == "__main__":
    domain = sys.argv[1]
    h = TestHTTPS(domain, os.getcwd()+'/../')
    h.domains = [domain]
    h.run_test(domain)
    print(h.https_test)

