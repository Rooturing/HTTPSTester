import requests
import os
import re
import logging
import time
import sys
import time, threading
from queue import Queue

SHARE_Q = Queue()
WORKER_THREAD_NUM = 20

headers = {
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection':'close'}
http_default = []
http_only = []
https_reachable = []  
https_default = []
https_only = []
https_error = []
unreachable = [] 

def read_domains(filename):
    with open(filename) as f:
        text = f.read().strip()
    return re.findall('(.*)\n', text)

def get_https_error(domain, e):
    global http_default,http_only,https_reachable,https_default,https_only,https_error,unreachable 
    
    if re.findall(r"hostname .* doesn't match", e):
        https_error.append(domain+" (host doesn't match)")
    elif re.findall(r"certificate verify failed", e):
        https_error.append(domain+" (certificate verify failed)")
    elif re.findall(r"tlsv1 unrecognized name", e):
        https_error.append(domain+" (tlsv1 unrecognized name)")
    elif re.findall(r"ECONNRESET", e):
        unreachable.append(domain+ " (connection reset)")
    else:
        https_error.append(domain+" (?)")

def run_test(domain):
    global http_default,http_only,https_reachable,https_default,https_only,https_error,unreachable
    if True:
        try:
            res1 = requests.get("http://"+domain, allow_redirects=True, headers=headers)
            http_status = str(res1.status_code)
            url = res1.url
            if re.match(r"^2",http_status):
                if re.findall("https", url):
                    https_default.append(domain)
                    logging.info(domain+" use default https.")
                else:
                    http_default.append(domain)
                    logging.info(domain+" use default http.")
                    try:
                        res2 = requests.get("https://"+domain, allow_redirects=True, verify=True, headers=headers)
                        http_status = str(res2.status_code)
                        logging.info("testing if https is available..")
                        if re.match(r"^2",http_status):
                            https_reachable.append(domain)
                            logging.info(domain+" is https reachable.")
                        else:
                            logging.info("return error status code, http status code: "+http_status)
                            http_only.append(domain)
                    except Exception as e:                   
                        logging.info(e)
                        if re.findall("SSLError",str(e)):
                            get_https_error(domain, str(e))
                        else:
                            logging.info("domain is http only")
                            http_only.append(domain)             
            else:
                logging.info(domain+" status code: "+http_status+", domain unreachable.")
                unreachable.append(domain)
        except Exception as e:
            logging.info(e)
            if re.findall(r"SSLError", str(e)):
                get_https_error(domain, str(e))
            else:
                try:
                    res2 = requests.get("https://"+domain, allow_redirects=True, verify=True, headers=headers)
                    http_status = str(res2.status_code)
                    logging.info("testing if https is available..")
                    if re.match(r"^2",http_status):
                        https_only.append(domain)
                        logging.info(domain+" is https only.")
                    else:
                        logging.info("return error status code, http status code: "+http_status)
                        unreachable.append(domain)
                except Exception as e:                   
                    logging.info(e)
                    if re.findall("SSLError",str(e)):
                        get_https_error(domain, str(e))
                    else:
                        unreachable.append(domain)
        logging.info("\n")

class MyThread(threading.Thread):
    def __init__(self,func):
        super(MyThread,self).__init__()
        self.func = func
    def run(self):
        self.func()

def worker():
    global SHARE_Q
    while True:
        if not SHARE_Q.empty():
            item = SHARE_Q.get()
            print("processing: "+item)
            run_test(item)
            time.sleep(1)
            SHARE_Q.task_done()
        else:
            break

def test_https(domain, domains): 
    
    
    f = open("report/test_https/"+domain+".txt","w")
    
    global SHARE_Q
    global http_default,http_only,https_reachable,https_default,https_only,https_error,unreachable

    threads = []

    for domain in domains:
        SHARE_Q.put(domain)
    for i in range(WORKER_THREAD_NUM):
        thread = MyThread(worker)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    SHARE_Q.join()

    
    f.write('http_default:\n'+'\t'+', '.join(http_default)+'\n')
    f.write('http_only:\n'+'\t'+', '.join(http_only)+'\n')
    f.write('https_reachable:\n'+'\t'+', '.join(https_reachable)+'\n')
    f.write('https_default:\n'+'\t'+', '.join(https_default)+'\n')
    f.write('https_only:\n'+'\t'+', '.join(https_only)+'\n')
    f.write('https_error:\n'+'\t'+', '.join(https_error)+'\n') 
    f.write('unreachable:\n'+'\t'+', '.join(unreachable))
    

    f.close()

def init_dir():
    if not os.path.exists('report'):
        os.mkdir('report')
    if not os.path.exists('report/test_https'):
        os.mkdir('report/test_https')
        os.mkdir('report/test_https/log')

if __name__ == "__main__":
    init_dir()
    domain_list = sys.argv[1:]
    for domain in domain_list:
        logging.basicConfig(filename='report/test_https/log/'+str(time.time())+"."+domain+'.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
        test_https(domain, read_domains("domain/resolved_domain/"+domain+".txt"))
