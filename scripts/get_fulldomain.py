import sys
sys.path.append("util")
import os
import re
import requests
from Sublist3r import sublist3r
from crtsh import *
from query_dns import *
from time import time
os.path.join(os.getcwd(), "..")


def findSubdoamin(origin_domain, domains):
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
    with open("../output/domain/fulldomain/"+origin_domain+".txt","w") as f:
        f.write('\n'.join(out_domain))
    print("Finished! %d domains" % len(out_domain))

def read_domains(filename):
    with open(filename) as f:
        text = f.read().strip()        
        return re.findall('(.*)\n', text)

if __name__ == "__main__":
    domains = sys.argv[1:]
    for domain in domains:
        start = time()
        crt = crtsh_db()
        crt.write_domain("."+domain)
        subdomains = read_domains("../output/domain/crtsh/."+domain+".txt")
        findSubdoamin(domain, subdomains)
        sorted_d = sort_domains(domain)
        print("Finding DNS record for domian %s" % domain)
        write_DNSres(domain, sorted_d)
        print("DNS records have been written, finding resolved domains")
        count = get_resolved_domains(domain)
        print("Done! Total %d resolved domains for %s found!"%(count,domain))
        print("Total time: %ds" % (time()-start))
        del crt

    
