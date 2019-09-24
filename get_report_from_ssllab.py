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
    with open("report/error_domain/"+domain+"_https_error.txt","w") as f:
        for d in domains:
            f.write(d+'\n')

def init_dir():
    if not os.path.exists('report'):
        os.mkdir('report')
    if not os.path.exists('report/error_domain'):
        os.mkdir('report/error_domain')
    if not os.path.exists('report/pic'):
        os.mkdir('report/pic')
    if not os.path.exists('report/ssllab'):
        os.mkdir('report/ssllab')
    if not os.path.exists('report/ssllab/raw_results'):
        os.mkdir('report/ssllab/raw_results')
    if not os.path.exists('report/chart'):
        os.mkdir('report/chart')

if __name__ == "__main__":
    init_dir()
    domains = sys.argv[1:]
    for domain in domains: 
        with open('report/test_https/'+domain+".json") as f:
            https_test = json.dump(f)
        write_error_domains(domain, del_error_message(https_test['https_error']))
        run(domain,"report/error_domain/"+domain+"_https_error.txt","report/ssllab/"+domain+"_error.csv")
    
