#coding=utf-8
import sys
sys.path.append('util')
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from pyssltest import run
import logging


def del_error_message(https_error):
    ds = []
    for d in https_error:
        dd = re.findall(r'(.*?) \(',d)
        if dd:
            ds.append(dd[0])
    return ds

def write_error_domains(domain, domains):
    with open("../output/report/error_domain/"+domain+"_https_error.txt","w") as f:
        for d in domains:
            f.write(d+'\n')

if __name__ == "__main__":
    domains = sys.argv[1:]
    for domain in domains: 
        with open('../output/report/test_https/'+domain+".json") as f:
            https_test = json.load(f)
        #write_error_domains(domain, del_error_message(https_test['https_error']))
        #if you only want to further test the error domains
        #run(domain,"report/error_domain/"+domain+"_https_error.txt","report/ssllab/"+domain+"_error.csv")
        #else you can test all domains
        run(domain,"../output/domain/resolved_domain/"+domain+".txt","../output/report/ssllab/"+domain+".csv")
    
