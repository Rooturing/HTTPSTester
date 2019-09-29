import sys
import json

if __name__=='__main__':
    domains = sys.argv[1:]
    cmp_map = {}
    for domain in domains:
        out = json.load(open('chart/'+domain+'.json'))
        cmp_map[domain.split('.')[0]] = out['https_overall']
    with open('data.json','w') as f:
        json.dump(cmp_map,f)
