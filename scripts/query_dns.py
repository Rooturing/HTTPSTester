import re
import sys
import os
import threading
import queue
import config
from dns.resolver import Resolver

class MyThread(threading.Thread):
    def __init__(self, func):
        super(MyThread, self).__init__()
        self.func = func

    def run(self):
        self.func()

class Query_DNS:
    def __init__(self, domain, basedir):
        self.basedir = basedir
        self.domain = domain
        self.thread_num = 10
        self.names_que = queue.Queue()
        self.query_res = []
        self.resolver = Resolver()
        self.resolver.nameservers = config.resolver_nameservers
        self.resolver.timeout = config.resolver_timeout

    def sort_domains(self):
        out_domains = []

        sorting = set()
        f1 = open(self.basedir + "/output/domain/fulldomain/"+self.domain+".txt")
        ds = f1.read().split('\n')
        for d in ds:
            d = '.'.join(d.split(".")[::-1])
            out_domains.append(d)
        out_domains.sort()
        for i in range(len(out_domains)):
            out_domains[i] = '.'.join(out_domains[i].split(".")[::-1])
        f1.close()
        return out_domains

    def read_domains(self, filename):
        with open(filename) as f:
            text = f.read()
            return re.findall('(.*)\n', text)

    def gen_queue(self):
        subdomains = self.sort_domains()
        for sub in subdomains:
            self.names_que.put(sub)

    def query_DNS(self):
        self.gen_queue()
        threads = []
        for i in range(self.thread_num):
            thread = MyThread(self.worker)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    def worker(self):
        while not self.names_que.empty():
            name = self.names_que.get()
            try:
                A = self.resolver.query(name, 'A')
                for i in A.response.answer:
                    self.query_res.append(str(i))
            except Exception as e:
                print(str(e))

    def write_DNS(self):
        f_dnsres = open(self.basedir+"/output/domain/dnsres/"+self.domain+".txt", "w")
        f_resolved = open(self.basedir+"/output/domain/resolved_domain/"+self.domain+".txt", "w")
        resolved_d = set()
        for res in sorted(self.query_res):
            f_dnsres.write(res+'\n')
            if re.match(r'(.*'+self.domain+'$)', res.split('. ')[0]):
                resolved_d.add(res.split('. ')[0])
        f_resolved.write('\n'.join(resolved_d))
        f_dnsres.close()
        f_resolved.close()
        return len(resolved_d)

    def run(self):
        print("Finding DNS record for domian %s" % self.domain)
        self.query_DNS()
        count = self.write_DNS()
        return count



