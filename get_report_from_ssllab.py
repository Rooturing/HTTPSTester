#coding=utf-8
import sys
sys.path.append('util')
import os
import re
import numpy as np  
import matplotlib.mlab as mlab  
import matplotlib.pyplot as plt 
import requests
from bs4 import BeautifulSoup
from pyssltest import run
import logging
import pdb



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

def get_report(domain):
    with open("report/test_https/"+domain+".txt") as f:
        lines = f.read().split('\n')
        http_default = lines[1].strip().split(', ').remove('')
        http_only = lines[3].strip().split(', ').remove('')
        https_reachable = lines[5].strip().split(', ').remove('')
        https_default = lines[7].strip().split(', ').remove('')
        https_only = lines[9].strip().split(', ').remove('')
        https_error = lines[11].strip().split(', ').remove('')
        unreachable = lines[13].strip().split(', ').remove('')
        len_http_default = len(http_default) if http_default else 0
        len_http_only = len(http_only) if http_only else 0
        len_https_reachable = len(https_reachable) if https_reachable else 0
        len_https_default = len(https_default) if https_default else 0
        len_https_only = len(https_only) if https_only else 0
        len_https_error = len(https_error) if https_error else 0
        len_unreachable = len(unreachable) if unreachable else 0
        print("http_default: %d"%len_http_default)
        print("http_only: %d"%len_http_only)
        print("https_reachable: %d"%len_https_reachable)
        print("https_default: %d"%len_https_default)
        print("https_only: %d"%len_https_only)
        print("https_error: %d"%len_https_error)
        print("unreachable: %d"%len_unreachable)
        all_length = len_http_default+len_http_only+len_https_reachable+len_https_default+len_https_only+len_https_error+len_unreachable
        if all_length:
            print("total: %d"%(all_length))
        else:
            print("no domain tested")
            sys.exit()
        all_domains = http_default + http_only + https_reachable + https_default + https_only + del_error_message(https_error) + del_error_message(unreachable)
        domain_set = set(all_domains)
        return (https_default,https_reachable,https_error,https_only,http_only,unreachable)



def draw_overall_pie(https_default,https_reachable,https_error,https_only,http_only,unreachable,domain):        
    #画饼图
    labels = ['https_default','https_reachable','https_error','https_only','http_only','unreachable']
    X = [len(https_default),len(https_reachable),len(https_error),len(https_only),len(http_only),len(unreachable)]
    fig = plt.figure(figsize=(8,8))
    plt.pie(X,labels=labels,autopct='%1.2f%%',pctdistance=0.8,labeldistance=1.1,rotatelabels=10,radius=0.8) 
    plt.legend(loc='upper left',bbox_to_anchor=(-0.15,1))
    plt.title("overall https analysis for "+domain)
    plt.show() 
    if not os.path.exists('report/pic/'+domain):
        os.mkdir('report/pic/'+domain)
    plt.savefig("report/pic/"+domain+"/https_overall_result.png")
    

def get_error_map(https_error):
    err_map = {}
    labels = []

    for i in https_error:
        item = i.split(' (')
        d = item[0]
        error = item[1].strip(')')
        if error not in err_map:
            err_map[error] = set([d])
            labels.append(error)
        else:
            err_map[error].add(d)
    with open("report/error_domain/"+domain+"_err_reason_map.txt","w") as f:
        for k in err_map:
            f.write(k+":\n")
            f.write('\t'+str(err_map[k])+'\n')
    return err_map

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

if __name__ == "__main__":
    init_dir()
    domains = sys.argv[1:]
    for domain in domains: 
        (https_default,https_reachable,https_error,https_only,http_only,unreachable) = get_report(domain)
        draw_overall_pie(https_default,https_reachable,https_error,https_only,http_only,unreachable,domain)
        write_error_domains(domain, del_error_message(https_error))
        run(domain,"report/error_domain/"+domain+"_https_error.txt","report/ssllab/"+domain+"_error.csv")
    
