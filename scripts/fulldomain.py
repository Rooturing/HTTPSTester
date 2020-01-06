import sys
import os
import re
import requests
from scripts.Sublist3r import sublist3r
from scripts.crtsh import *
from scripts.query_dns import *
from time import time
os.path.join(os.getcwd(), "..")

class Fulldomain: 
    def __init__(self, domain, basedir):
        self.domain = domain
        self.basedir = basedir

    def findSubdoamin(self, origin_domain, domains):
        out_domain = set()
        
        #首先测试原域名的子域名
        subdomains = sublist3r.main(origin_domain, 40, None, ports=None, silent=False, verbose= False, enable_bruteforce= False, engines=None)
        out_domain = out_domain | set(subdomains)

        #再测试证书公开日志中搜集到的*.通配符域名的子域
        for domain in domains:
            if re.findall(r"\*\.", domain):
                domain = domain.replace("*.","")
                out_domain = out_domain | set([domain, "www."+domain])
                subdomains = sublist3r.main(domain, 40, None, ports=None, silent=False, verbose= False, enable_bruteforce= False, engines=None)
                print("find %d subdomains for %s" % (len(subdomains), domain))
                out_domain = out_domain | set(subdomains)
            else:
                out_domain.add(domain)
        with open(self.basedir+"/output/domain/fulldomain/"+origin_domain+".txt","w") as f:
            f.write('\n'.join(out_domain))
        print("Finished! %d domains" % len(out_domain))

    def read_domains(self, filename):
        with open(filename) as f:
            text = f.read().strip()        
            return re.findall('(.*)\n', text)

    def run(self):
        start = time()
        print("Querying crt.sh for subdomains")
        crt = crtsh_db(self.basedir)
        crt.write_domain("."+self.domain)
        subdomains = self.read_domains(self.basedir+"/output/domain/crtsh/."+self.domain+".txt")
        print("Found %d domains in crt.sh" % len(subdomains))
        self.findSubdoamin(self.domain, subdomains)
        count = Query_DNS(self.domain, self.basedir).run()
        print("Done! Total %d resolved domains for %s found!"%(count, self.domain))
        print("Total time: %ds" % (time()-start))
        del crt


