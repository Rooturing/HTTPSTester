import json
import re
import sys

class GenRank:
    def __init__(self, basedir, domains):
        self.basedir = basedir
        self.domains = domains
        self.https_count = {}
        self.https_rank = {}
        self.error_rank = {}

    def count(self):
        for c in self.domains:
            j = json.load(open(self.basedir+'/output/report/test_https/'+c+'.json','r'))
            self.https_count[c] = {'https':len(j['https_default'])+len(j['https_only']),'http':len(j['http_default']),'error':len(j['https_error']),'total':len(j['https_default'])+len(j['https_only'])+len(j['http_default'])+len(j['https_error'])}

    def rank(self):
        self.count()
        for item in self.https_count.items():
            if item[1]['total']:
                self.https_rank[item[0]] = round(item[1]['https'] / item[1]['total'],2)
                self.error_rank[item[0]] = round(item[1]['error'] / item[1]['total'],2)
        self.https_rank = sorted(self.https_rank.items(), key=lambda item:item[1], reverse=True)
        self.error_rank = sorted(self.error_rank.items(), key=lambda item:item[1], reverse=True)
        print('https rank:')
        print(self.https_rank)
        print(len(self.https_rank))
        print('error rank:')
        print(self.error_rank)
        print(len(self.error_rank))
    
    def output(self):
        with open(self.basedir+'/output/report/rank/https_count.json','w') as f:
            json.dump(self.https_count,f)
        with open(self.basedir+'/output/report/rank/https_rank.json','w') as f:
            json.dump(self.https_rank,f)
        with open(self.basedir+'/output/report/rank/error_rank.json','w') as f:
            json.dump(self.error_rank,f)

    def run(self):
        self.rank()
        self.output()
        return self

class FindErrorReason:
    def __init__(self, rank):
        self.basedir = rank.basedir
        self.rank = rank.error_rank
        self.error_report = {}

    def error_ip(self):
        for d in self.rank:
            j = json.load(open(self.basedir+'/output/report/test_https/'+d[0]+'.json','r'))
            dns = open(self.basedir+'/output/domain/dnsres/'+d[0]+'.txt','r').read()
            error_reasons = {}
            for i in j['https_error']:
                reason = re.findall('\((.*)\)',i)[0]
                if reason not in error_reasons:
                    error_reasons[reason] = [i.split(' (')[0]] 
                else:
                    error_reasons[reason].append(i.split(' (')[0])
            error_map = {}
            for r in error_reasons:
                error_map[r] = {}
                error_map[r]['multi_ip'] = []
                for d in error_reasons[r]:
                    ip = re.findall('\n'+d+'.*? IN A (.*)',dns)
                    if len(ip) == 1:
                        if ip[0] not in error_map[r]:
                            error_map[r][ip[0]] = [d]
                        else:
                            error_map[r][ip[0]].append(d)
                    else:
                        error_map[r]['multi_ip'].append(d)
            #print(error_map)
            with open(self.basedir+'/output/report/chart/error_reason.json','w') as j:
                json.dump(error_map,j)

    def run(self):
        self.error_ip()

if __name__ == '__main__':
    filename = sys.argv[1]
    rank = GenRank(filename).rank()
    Find_Error_Reason(rank).error_ip()
