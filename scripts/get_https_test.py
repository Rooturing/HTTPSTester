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


SHARE_Q = Queue()
WORKER_THREAD_NUM = 30 

headers = {
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection':'close'}

https_test = {'https_default':[],'http_default':[],'https_reachable':[],'http_only':[],'https_only':[],'https_error':[],'unreachable':[]}

def read_domains(filename):
    with open(filename) as f:
        text = f.read().strip()
    return re.findall('(.*)\n', text)

def get_https_error(domain, e):
    global https_test  
    
    if re.findall(r"hostname .* doesn't match", e):
        https_test['https_error'].append(domain+" (host doesn't match)")
    elif re.findall(r"certificate verify failed", e):
        https_test['https_error'].append(domain+" (certificate verify failed)")
    elif re.findall(r"tlsv1 unrecognized name", e):
        https_test['https_error'].append(domain+" (tlsv1 unrecognized name)")
    elif re.findall(r"ECONNRESET", e):
        https_test['unreachable'].append(domain+ " (connection reset)")
    else:
        https_test['https_error'].append(domain+" (?)")

def run_test(domain):
    global https_test
    if True:
        try:
            res1 = requests.get("http://"+domain, allow_redirects=True, headers=headers, timeout=60)
            http_status = str(res1.status_code)
            url = res1.url
            if re.match(r"^2",http_status):
                if re.findall("https", url):
                    https_test['https_default'].append(domain)
                    logging.info(domain+" use default https.")
                else:
                    https_test['http_default'].append(domain)
                    logging.info(domain+" use default http.")
                    try:
                        res2 = requests.get("https://"+domain, allow_redirects=True, verify=True, headers=headers, timeout=60)
                        http_status = str(res2.status_code)
                        logging.info("testing if https is available..")
                        if re.match(r"^2",http_status):
                            https_test['https_reachable'].append(domain)
                            logging.info(domain+" is https reachable.")
                        else:
                            logging.info("return error status code, http status code: "+http_status)
                            https_test['http_only'].append(domain)
                    except Exception as e:                   
                        logging.info(e)
                        if re.findall("SSLError",str(e)):
                            get_https_error(domain, str(e))
                        else:
                            logging.info("domain is http only")
                            https_test['http_only'].append(domain)             
            else:
                logging.info(domain+" status code: "+http_status+", domain unreachable.")
                https_test['unreachable'].append(domain)
        except Exception as e:
            logging.info(e)
            if re.findall(r"SSLError", str(e)):
                get_https_error(domain, str(e))
            else:
                try:
                    res2 = requests.get("https://"+domain, allow_redirects=True, verify=True, headers=headers, timeout=60)
                    http_status = str(res2.status_code)
                    logging.info("testing if https is available..")
                    if re.match(r"^2",http_status):
                        https_test['https_only'].append(domain)
                        logging.info(domain+" is https only.")
                    else:
                        logging.info("return error status code, http status code: "+http_status)
                        https_test['unreachable'].append(domain)
                except Exception as e:                   
                    logging.info(e)
                    if re.findall("SSLError",str(e)):
                        get_https_error(domain, str(e))
                    else:
                        https_test['unreachable'].append(domain)
        logging.info("\n")

class MyThread(threading.Thread):
    def __init__(self,func):
        super(MyThread,self).__init__()
        self.func = func
    def run(self):
        self.func()

def worker():
    global SHARE_Q
    while not SHARE_Q.empty():
        item = SHARE_Q.get()
        run_test(item)
        time.sleep(1)
        print("task done for domain: "+item)
        print("queue size: "+str(SHARE_Q.qsize()))
        SHARE_Q.task_done()

def test_https(domain, domains): 
    
    
    f = open("../output/report/test_https/"+domain+".json","w")
    
    global SHARE_Q
    global https_test 

    threads = []

    random.shuffle(domains)
    for domain in domains:
        SHARE_Q.put(domain)
    for i in range(WORKER_THREAD_NUM):
        thread = MyThread(worker)
        thread.start()
        threads.append(thread)
    startTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for thread in threads:
        thread.join()
    endTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print('all done! start: '+startTime+', end:'+endTime)
    
    json.dump(https_test,f)

    f.close()


if __name__ == "__main__":
    domain_list = sys.argv[1:]
    for domain in domain_list:
        logging.basicConfig(filename='../output/report/test_https/log/'+str(time.time())+"."+domain+'.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        test_https(domain, read_domains("../output/domain/resolved_domain/"+domain+".txt"))
