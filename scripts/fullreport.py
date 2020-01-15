import sys
import json
import matplotlib.mlab as mlab  
import matplotlib.pyplot as plt 
from scripts.get_cert import *
from scripts.gen_rank import *
import pandas
import os


class FullReport:
    def __init__(self, domain, basedir, domains):
        self.domain = domain
        self.basedir = basedir
        self.domains = domains 
        self.https_test = {}
        self.out_map = {}
        self.run()

    def get_report(self):
        with open(self.basedir + "/output/report/test_https/" + self.domain+".json") as f:
            self.https_test = json.load(f)
        self.out_map = {'https_overall':{'https_default':len(self.https_test['https_default']),"http_only":len(self.https_test['http_only']),"https_reachable":len(self.https_test['https_reachable']),"https_only":len(self.https_test['https_only']),"https_error":len(self.https_test['https_error']),"unreachable":len(self.https_test['unreachable'])}}

    def count_domains_ip_from_DNS(self):
        with open(self.basedir+"/output/domain/dnsres/"+self.domain+".txt") as f:
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
        
        with open(self.basedir+"/output/report/domain_ip/"+self.domain+"_domain_ip.txt","w") as f:
            for k in domain_ip_map:
                f.write(k+":\n")
                f.write("\t"+str(domain_ip_map[k])+"\n")
        with open(self.basedir+"/output/report/domain_ip/"+self.domain+"_ip_domain.txt","w") as f:
            for k in ip_domain_map:
                f.write(str(k[0])+"\n")
                f.write("\t"+str(k[1])+"\n")
        ip_DNS_map = {'ip_domain':ip_domain_map,'domain_ip':domain_ip_map}

    def count_cert(self, filename):
        cert_list = {}
        with open(filename) as f:
            text = f.read()
            domain = re.findall(r"certfrom (.*?):", text)
            serial_num = re.findall(r"serial number->0x(.*?),", text)
            issuer = re.findall(r"issuer-><X509Name object '(.*?)'>",text)
            for i in range(len(domain)):
                if serial_num[i] not in cert_list.keys():
                    cert_list[serial_num[i]] = {'domains':set([domain[i]]),'CA':issuer[i]}
                else:
                    cert_list[serial_num[i]]['domains'].add(domain[i])
            print("get %d certs from %d domains"%(len(cert_list),len(domain)))
            return cert_list
        
    def count_cert_fd(self):
        return self.count_cert(self.basedir+"/output/report/cert/cert_from_domain/"+self.domain+"_fd.txt")

    def count_cert_fi(domain):
        return self.count_cert(self.basedir+"/output/report/cert/cert_from_ip/"+self.domain+"_fp.txt")

    def load_cert_ct(self, filename):
        with open(filename) as f:
            text = f.read()
            fnd = re.findall(r'found, cert: (.*), res: (.*)',text)
            nfnd = re.findall(r'not found, cert: (.*)\n',text)
        return (fnd, nfnd)

    def find_CA(self, cert_list, where_from):
        CA_counter = {}
        for i in cert_list.values():
            CA = re.findall(r"CN=(.*)",i['CA'])[0]
            if CA not in CA_counter:
                CA_counter[CA] = 1
            else:
                CA_counter[CA] += 1
        sorted_CA = sorted(CA_counter.items(),key=lambda item:item[1],reverse=True)
        print('total unique certs: %d'%len(cert_list))
        print('total CAs found: %d'%len(CA_counter))
        print(sorted_CA)
        

    def compare_cert_difference(self, certfd, certfi):
        #print(certfd)
        #print(certfi)
        cert1 = set(certfd.keys())
        cert2 = set(certfi.keys())
        dc1 = list(cert1 - cert2)
        dc2 = list(cert2 - cert1)
        print("cert from domain:")
        for c in dc1:
            print("\tserial number: "+str(c)+", domains: "+str(certfd[c]))
        print("cert from ip:")
        for c in dc2:
            print("\tserial number: "+str(c)+", domains: "+str(certfi[c]))

    def find_shared_cert(self, cl):
        sc = []
        for c in cl.items():
            if len(c[1]['domains'])>1:
                sc.append(c)
        print("total shared-certs found: %d"%len(sc))
        with open(self.basedir+'/output/report/cert/shared_cert/'+self.domain+"_sc.txt",'w') as f:
            f.write(str(sc)+'\n')
        return len(sc)

    def count_cert_in_ct(self, certfd):
        (fnd, nfnd) = load_cert_ct(self.basedir+"/output/report/cert/cert_ct/"+self.domain+"_ct.txt")
        cert_in_ct = {'equals2':[],'equals1':[],'equals0':[],'more_than2':[]}
        for c in fnd:
            ctr = re.findall(r'\((.*?)\)',c[1])
            if len(ctr) == 2:
                cert_in_ct['equals2'].append(c)
            if len(ctr) == 1:
                cert_in_ct['equals1'].append(c)
            if len(ctr) > 2:
                cert_in_ct['more_than2'].append(c)
        for c in nfnd:
            cert_in_ct['equals0'].append(c)
        with open(self.basedir+"/output/report/cert/cert_ct/"+self.domain+"_notInCT.txt",'w') as f:
            for i in cert_in_ct['equals0']:
                f.write("serial number: "+i+", "+str(certfd[i])+'\n')
        print('total number of cert is %d, %d not found in ct'%(len(fnd)+len(nfnd),len(nfnd)))
        print('however, %d cert(s) have over 2 results'%len(cert_in_ct['more_than2']))
        CT = {'0':len(cert_in_ct['equals0']),'1':len(cert_in_ct['equals1']),'2':len(cert_in_ct['equals2']),'>2':len(cert_in_ct['more_than2'])}
        return CT

    def run(self):
        #self.init_pic_path()
        self.get_report()
        #self.draw_overall_pie()
        #count the relationships between domain and ip
        self.count_domains_ip_from_DNS()
        #try to connect each domain's 443 port (use tls sni extension)
        #GetCert(domain, self.basedir).get_cert_from_domains()
        gc = GetCert(self.domain, self.basedir)
        certfd = self.count_cert_fd()
        #find shared cert between different domains
        self.out_map['shared_cert'] = self.find_shared_cert(certfd)
        #draw the piechar for certs' CA map
        self.out_map['CA'] = self.find_CA(certfd,'fd')
        #search if the certificate was logged in CT
        gs.search_cert_in_ct(certfd)
        #count the number of logged certs in CT, write down the not logged ones
        self.out_map['CT'] = self.count_cert_in_ct(certfd)
        
        #output the final result in json
        with open(self.basedir+'/output/report/chart/'+self.domain+".json","w") as f:
            json.dump(self.out_map,f)







'''
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
'''
