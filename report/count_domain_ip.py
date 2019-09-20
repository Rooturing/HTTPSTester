import re
import sys

def count_domains_ip_fromDNS(domain):
    with open("fulldomain/dnsres/"+domain+"_DNSres.txt") as f:
        records = f.read().split('\n\n')
    domain_ip_map = {}
    ip_domain_map = {}
    for r in records:
        if r:
            ip = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", r)
            do = r.split(". ")[0]
            if len(ip)>1:
                domain_ip_map[do] = ip
            for i in ip:
                if i not in ip_domain_map:
                    ip_domain_map[i] = set([do])
                else:
                    ip_domain_map[i].add(do)

    ip_domain_map = sorted(ip_domain_map.items(),key=lambda item:item[0])
    
    with open("domain_ip/"+domain+"_domain_ip.txt","w") as f:
        for k in domain_ip_map:
            f.write(k+":\n")
            f.write("\t"+str(domain_ip_map[k])+"\n")
    with open("domain_ip/"+domain+"_ip_domain.txt","w") as f:
        for k in ip_domain_map:
            f.write(str(k[0])+"\n")
            f.write("\t"+str(k[1])+"\n")

def read_file(filename):
    with open(filename) as f:
        for line in f:
            if not re.findall('\t',line):
                key = line.strip('\n')
            else:
                res_map[key] = line.strip('\t').strip('\n')
    return res_map


if __name__ == "__main__":
    domain = sys.argv[1]
    #domain = 'sjtu.edu.cn'
    count_domains_ip_fromDNS(domain)
