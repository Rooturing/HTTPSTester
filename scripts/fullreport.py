import sys
import json
import matplotlib.mlab as mlab  
import matplotlib.pyplot as plt 
from scripts.find_cert import *
from scripts.util.count_cert import *
from scripts.util.count_domain_ip import *
import pandas
import os


class FullReport:
    def __init__(self, domain, basedir):
        self.domain = domain
        self.basedir = basedir
        self.https_test = {}
        self.out_map = {}
        self.run()

    def get_report(self):
        with open(self.basedir + "/output/report/test_https/" + self.domain+".json") as f:
            self.https_test = json.load(f)
        self.out_map = {'https_overall':{'https_default':len(https_test['https_default']),"http_only":len(https_test['http_only']),"https_reachable":len(https_test['https_reachable']),"https_only":len(https_test['https_only']),"https_error":len(https_test['https_error']),"unreachable":len(https_test['unreachable'])}}


    def draw_overall_pie(self):        
        #画饼图
        del self.https_test['http_default']
        labels = self.https_test.keys()
        X = [len(v) for v in self.https_test.values()]
        fig = plt.figure(figsize=(8,8))
        plt.pie(X,labels=labels,autopct='%1.2f%%',pctdistance=0.8,labeldistance=1.1,rotatelabels=10,radius=0.8) 
        plt.legend(loc='upper left',bbox_to_anchor=(-0.15,1))
        plt.title("overall https analysis for "+self.domain)
        plt.show() 
        if not os.path.exists(self.basedir + '/output/report/pic/' + self.domain):
            os.mkdir(self.basedir + '/output/report/pic/' + domain)
        plt.savefig(self.basedir + "/output/report/pic/"+self.domain+"/"+self.domain+"https_overall_result.png")

    def init_pic_path(self):
        if not os.path.exists(self.basedir + '/output/report/pic/'+self.domain):
            os.makedirs(self.basedir + '/output/report/pic/'+self.domain)

    def run(self):
        self.init_pic_path()
        self.get_report()
        self.draw_overall_pie()

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

