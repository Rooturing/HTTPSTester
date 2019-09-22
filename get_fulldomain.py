import sys
sys.path.append("util")
import os
import re
import requests
from Sublist3r import sublist3r
from crtsh import *
from query_dns import *


def findSubdoamin(origin_domain, domains):
    out_domain = set()
    for domain in domains:
        if re.findall(r"\*\.", domain):
            domain = domain.replace("*.","")
            out_domain = out_domain | set([domain, "www."+domain])
            subdomains = sublist3r.main(domain, 40, None, ports=None, silent=False, verbose= False, enable_bruteforce= False, engines=None)
            print("find %d subdomains for %s" % (len(subdomains), domain))
            out_domain = out_domain | set(subdomains)
        else:
            out_domain.add(domain)
    with open("domain/fulldomain/"+origin_domain+".txt","w") as f:
        f.write('\n'.join(out_domain))
    print("Finished! %d domains" % len(out_domain))

def read_domains(filename):
    with open(filename) as f:
        text = f.read().strip()        
        return re.findall('(.*)\n', text)

def init_dir():
    if not os.path.exists('util/log'):
        os.mkdir('util/log')
    if not os.path.exists('domain'):
        os.mkdir('domain')
    if not os.path.exists('domain/crtsh'):
        os.mkdir('domain/crtsh')
    if not os.path.exists('domain/resolved_domain'):
        os.mkdir('domain/resolved_domain')
    if not os.path.exists('domain/dnsres'):
        os.mkdir('domain/dnsres')
    if not os.path.exists('domain/fulldomain'):
        os.mkdir('domain/fulldomain')
if __name__ == "__main__":
    init_dir()
    domains = sys.argv[1:]
    crt = crtsh_db()
    for domain in domains:
        crt.write_domain("."+domain)
        findSubdoamin(domain, read_domains("domain/crtsh/"+domain+".txt"))
        sorted_d = sort_domains(domain)
        print("Finding DNS record for domian %s" % domain)
        write_DNSres(domain, sorted_d)
        print("DNS records have been written, finding resolved domains")
        count = get_resolved_domains(domain)
        print("Done! Total %d resolved domains for %s found!"%(count,domain))

    
