import sys
sys.path.append("util")
import json
import numpy as np  
import matplotlib.mlab as mlab  
import matplotlib.pyplot as plt 
from find_cert import *
from count_cert import *
from count_domain_ip import *
from parse_csv import *
import os



def get_report(domain):
    with open("../output/report/test_https/"+domain+".json") as f:
        https_test = json.load(f)
    out_map = {'https_overall':{'https_default':len(https_test['https_default']),"http_only":len(https_test['http_only']),"https_reachable":len(https_test['https_reachable']),"https_only":len(https_test['https_only']),"https_error":len(https_test['https_error']),"unreachable":len(https_test['unreachable'])}}
    return (https_test,out_map)

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
    with open("../output/report/error_domain/"+domain+"_err_reason_map.txt","w") as f:
        for k in err_map:
            f.write(k+":\n")
            f.write('\t'+str(err_map[k])+'\n')
    return err_map

def draw_overall_pie(https_test,domain):        
    #画饼图
    del https_test['http_default']
    labels = https_test.keys()
    X = [len(v) for v in https_test.values()]
    fig = plt.figure(figsize=(8,8))
    plt.pie(X,labels=labels,autopct='%1.2f%%',pctdistance=0.8,labeldistance=1.1,rotatelabels=10,radius=0.8) 
    plt.legend(loc='upper left',bbox_to_anchor=(-0.15,1))
    plt.title("overall https analysis for "+domain)
    plt.show() 
    if not os.path.exists('../output/report/pic/'+domain):
        os.mkdir('../output/report/pic/'+domain)
    plt.savefig("../output/report/pic/"+domain+"/"+domain+"https_overall_result.png")
    


def init_pic_path(domain):
    if not os.path.exists('../output/report/pic/'+domain):
        os.makedirs('../output/report/pic/'+domain)

if __name__=='__main__':
    domains = sys.argv[1:]
    for domain in domains:
        #init the picture saving path for specific domain
        init_pic_path(domain)

        #draw the overall https test result
        (https_test,out_map) = get_report(domain)
        draw_overall_pie(https_test,domain)

        '''
        ##parse the report from ssllab and draw piechar
        dlist = read_csv("report/ssllab/"+domain+"_error.csv")
        ##draw the piechar of error domain's ip
        draw_ip_map(dlist,domain)
        ##draw the most common HTTPS error reasons reported
        draw_error_reason(dlist,domain)
        ##draw the common names of error certs
        draw_error_cert(dlist,domain)
        '''

        #count the relationships between domain and ip
        count_domains_ip_fromDNS(domain)
        #try to connect each domain's 443 port (use tls sni extension)
        get_cert_from_domains(domain, read_domains("../output/domain/resolved_domain/"+domain+".txt"))
        certfd = count_cert_fd(domain)
        #find shared cert between different domains
        out_map['shared_cert'] = find_shared_cert(domain,certfd)
        #draw the piechar for certs' CA map
        out_map['CA'] = find_CA(domain,certfd,'fd')
        #search if the certificate was logged in CT
        search_cert_in_ct(certfd,domain)
        #count the number of logged certs in CT, write down the not logged ones
        out_map['CT'] = count_cert_in_ct(domain,certfd)

        #output the final result in json
        with open('../output/report/chart/'+domain+".json","w") as f:
            json.dump(out_map,f)

