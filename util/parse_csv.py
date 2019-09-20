import csv
import sys 
import re
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

def read_csv(filename):
    with open(filename) as f:
        domain_list = []
        f_csv = csv.reader(f)
        headers = next(f_csv)
        for row in f_csv:
            dmap = {}
            dmap['domain'] = row[0].strip('http://')
            dmap['ip'] = row[1] 
            dmap['grade'] = row[2]
            dmap['wrong_domain'] = 1 if row[4] == 'Y' else 0
            dmap['cert_expired'] = 1 if row[5] == 'Y' else 0
            dmap['self_signed'] = 1 if row[6] == 'Y' else 0
            dmap['cert_chain_issue'] = 1 if row[7] == 'Y' else 0
            dmap['cert_chain_incomplete'] = 1 if row[8] == 'Y' else 0
            dmap['thumbprint'] = row[9]
            dmap['common_name'] = row[10]
            domain_list.append(dmap)
    return domain_list

def draw_ip_map(domain_list,domain):
    ip = {}
    for d in domain_list:
        k = d['ip']
        if not re.findall('http',k):
            if k not in ip:
                ip[k] = 1
            else:
                ip[k] += 1
    sorted_ip = sorted(ip.items(),key=lambda item:item[1],reverse=True)
    labels = []
    fracs = []
    others = 0
    for i in sorted_ip:
        if i[1] > 2:
            labels.append(i[0])
            fracs.append(i[1])
        else:
            others += i[1]
    labels.append('others')
    fracs.append(others)

    fig = plt.figure(figsize=(12,10))
    plt.pie(x=fracs,labels=labels,autopct='%3.1f%%',startangle=90,pctdistance=0.8,labeldistance=1.1,rotatelabels=10,radius=0.68)
    plt.legend(loc='upper left',bbox_to_anchor=(-0.3,1),fontsize=15)
    plt.title('error IPs',fontsize=15)
    plt.show()
    plt.savefig("pic/"+domain+"_error_ip.png")

def draw_error_reason(domain_list,domain):
    addups = []
    for d in domain_list:
        toadd = list(d.items())[3:8]
        if len(addups) == 0:
            addups = toadd
        else:
            addups = [(i[0],i[1]+j[1]) for i,j in zip(addups,toadd)]
    labels = [i[0] for i in addups]
    count = [i[1] for i in addups]
    fig = plt.figure(figsize=(11,8))
    plt.barh(range(5),count,height=0.7,alpha=0.8)
    plt.yticks(range(5),labels)
    plt.xlim(0,max(count)+15)
    plt.xlabel("occurrence of error")
    plt.title("error reasons")
    for x,y in enumerate(count):
        plt.text(y+0.2,x-0.1,'%s'%y)
    plt.show()
    plt.savefig("pic/"+domain+"_error_reason.png",bbox_inches='tight')

def draw_error_cert(domain_list,domain):
    addups = {}
    for d in domain_list:
        cn = list(d.items())[-1][1].strip()
        if cn not in addups:
            addups[cn] = 1
        else:
            addups[cn] += 1
    del addups['Error']
    sorted_cn = sorted(addups.items(),key=lambda item:item[1],reverse=True)
    labels = []
    fracs = []
    others = 0
    for i in sorted_cn:
        if i[1] > 1:
            labels.append(i[0])
            fracs.append(i[1])
        else:
            others += 1
    labels.append('others')
    fracs.append(others)
    fig = plt.figure(figsize=(12,10))
    plt.pie(x=fracs,labels=labels,autopct='%3.1f%%',startangle=90,pctdistance=0.8,labeldistance=1.1,rotatelabels=10,radius=0.68)
    plt.legend(loc='upper left',bbox_to_anchor=(-0.3,1),fontsize=15)
    plt.title('common name of error cert',fontsize=15)
    plt.show()
    plt.savefig("pic/"+domain+"_error_cn.png")

if __name__ == "__main__":
    domain = sys.argv[1]
    dlist = read_csv(domain+"error.csv")
    draw_ip_map(dlist,domain)
    draw_error_reason(dlist,domain)
    draw_error_cert(dlist,domain)
