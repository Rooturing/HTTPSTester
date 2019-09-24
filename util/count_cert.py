import re
import sys
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

def count_cert(filename):
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

def count_cert_fd(domain):
    return count_cert("report/cert/cert_from_domain/"+domain+"_fd.txt")

def count_cert_fi(domain):
    return count_cert("report/cert/cert_from_ip/"+domain+"_fp.txt")

def load_cert_ct(filename):
    with open(filename) as f:
        text = f.read()
        fnd = re.findall(r'found, cert: (.*), res: (.*)',text)
        nfnd = re.findall(r'not found, cert: (.*)\n',text)
    return (fnd, nfnd)

def find_CA(domain,cert_list,where_from):
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
    
    labels = []
    fracs = []
    others = 0
    for i in sorted_CA:
        if i[1] > 1:
            labels.append(' '.join(i[0].split(' ')[:2]).split('/')[0] if len(i[0])>30 else i[0])
            fracs.append(i[1])
        else:
            others += 1
    #if len(labels) == 1:
    #    for i in sorted_CA:
    #        if i[1] == 1:
    #            labels.append(' '.join(i[0].split(' ')[:2]).split('/')[0] if len(i[0])>30 else i[0])
    #            fracs.append(i[1])
    #else:
    labels.append('others')
    fracs.append(others)
    fig = plt.figure(figsize=(12,10))
    plt.pie(x=fracs,labels=labels,autopct='%3.1f%%',startangle=90,pctdistance=0.8,labeldistance=1.1,rotatelabels=10,radius=0.68)
    plt.legend(loc='upper left',bbox_to_anchor=(-0.3,1),fontsize=10)
    plt.title('CA used by '+domain.split('.')[0],fontsize=15)
    plt.savefig("report/pic/"+domain+"/"+domain+"cert_CA_"+where_from+".png")
    return sorted_CA


def compare_cert_difference(certfd,certfi):
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

def find_shared_cert(domain,cl):
    sc = []
    for c in cl.items():
        if len(c[1]['domains'])>1:
            #print("serial number: %s, domain numbers: %d, CA: %s"%(c[0],len(c[1]['domains']),c[1]['CA']))
            sc.append(c)
    print("total shared-certs found: %d"%len(sc))
    with open('report/cert/shared_cert/'+domain+"_sc.txt",'w') as f:
        f.write(str(sc)+'\n')
    return sc

def count_cert_in_ct(domain,certfd):
    (fnd, nfnd) = load_cert_ct("report/cert/cert_ct/"+domain+"_ct.txt")
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
    with open("report/cert/cert_ct/"+domain+"_notInCT.txt",'w') as f:
        for i in cert_in_ct['equals0']:
            f.write("serial number: "+i+", "+str(certfd[i])+'\n')
    print('total number of cert is %d, %d not found in ct'%(len(fnd)+len(nfnd),len(nfnd)))
    ct_map = {'cert_found':fnd,'cert_not_found':nfnd}
    return ct_map


if __name__ == "__main__":
    domain = sys.argv[1] 
    certfd = count_cert("cert_from_domain/"+domain+".txt")
    #certfi = count_cert("cert_from_ip/"+domain+".txt")
    #count_cert_from_ip(certfi)
    #compare_cert_difference(certfd,certfi)
    find_shared_cert(certfd)
    count_cert_in_ct(domain,certfd)
