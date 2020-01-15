import sys
import os
import json
from queue import Queue
import re
import time, threading
import warnings

def read_domains(filename):
    with open(filename) as f:
        text = f.read().strip()
        return re.findall('(.*)\n', text)

class MyThread(threading.Thread):
    def __init__(self,func):
        super(MyThread,self).__init__()
        self.func = func
    def run(self):
        self.func()


class HTTPObservatory:
    def __init__(self, domain, basedir):
        self.basedir = basedir
        self.domain = domain
        self.domains = read_domains(basedir+"/output/domain/resolved_domain/"+domain+".txt")
        self.SHARE_Q = Queue()
        self.LEFT_Q = len(self.domains)
        self.WORKER_THREAD_NUM = 30 
        self.scan_result = {}

    def worker(self):
        sys.path.append(self.basedir+'/scripts/util/http_observatory')
        os.chdir(self.basedir+"/scripts/util/http_observatory/")
        from httpobs.scanner.local import scan
        while not self.SHARE_Q.empty():
            item  = self.SHARE_Q.get()
            self.scan_result = scan(item)
            print("task done for domain: "+item)
            self.LEFT_Q = self.LEFT_Q - 1
            print("queue size: %d, %d left" % (self.SHARE_Q.qsize(), self.LEFT_Q))
            self.SHARE_Q.task_done()

    def run(self):
        warnings.filterwarnings('ignore')
        j = open(self.basedir+'/output/report/http_observatory/'+self.domain+'.json','w')
        threads = []
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
        json.dump(self.scan_result,j)
        os.chdir(self.basedir)



