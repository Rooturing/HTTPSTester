import sys
sys.path.append("util")
import find_cert
import count_cert
import count_domain_ip
import parse_csv
import os

def init_dir():
    if not os.path.exists('util/log'):
        os.mkdir('util/log')
    if not os.path.exists('report/cert'):
        os.mkdir('report/cert')
        os.mkdir('report/cert/cert_ct')
        os.mkdir('report/cert/cert_from_domain')
        os.mkdir('report/cert/cert_from_ip')
        os.mkdir('report/cert/shared_cert')
    if not os.path.exists('report/pic'):
        os.mkdir('report/pic')
    if not os.path.exists('report/domain_ip'):
        os.mkdir('report/domain_ip')

if __name__=='__main__':
    init_dir()
    domains = sys.argv[1:]
    for domain in domains:
        count_domains_ip_fromDNS(domain)
        get_cert_from_domains(domain, read_domains("domain/resolved_domain/"+domain+".txt"))
        certfd = count_cert_fd(domain)
        search_cert_in_ct(certfd,domain)
        find_CA(certfd,'fd')
        find_shared_cert(certfd)
        count_cert_in_ct(domain,certfd)
        

