import argparse
import os
import subprocess
import traceback
import sys
sys.path.append('scripts')
import config
import pymysql

G = '\033[92m'  # green
Y = '\033[93m'  # yellow
B = '\033[94m'  # blue
R = '\033[91m'  # red
W = '\033[0m'   # white
C = '\033[36m'  # cyan

def banner():
    print("""%s
      _   _ _____ _____ ____  ____ _____         _            
     | | | |_   _|_   _|  _ \/ ___|_   _|__  ___| |_ ___ _ __ 
     | |_| | | |   | | | |_) \___ \ | |/ _ \/ __| __/ _ \ '__|
     |  _  | | |   | | |  __/ ___) || |  __/\__ \ ||  __/ |   
     |_| |_| |_|   |_| |_|   |____/ |_|\___||___/\__\___|_| %s 
    
      A Large-scale HTTPS evaluation tool with high performance.%s
    """%(C,B,W))

def parser_error(errmsg):
    banner()
    print("Usage: python3 " + sys.argv[0] + " [Options] use -h for help")
    print(R + "Error: " + errmsg + W)
    sys.exit()

def str2bool(v):
    if isinstance(v,bool):
        return v
    if v.lower() in ('yes','true','t','y','1'):
        return True
    elif v.lower() in ('no','false','f','n','0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def parse_args():
    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython3 ' + sys.argv[0] + " -d google.com")
    parser.error = parser_error
    parser._optionals.title = 'OPTIONS'
    parser.add_argument(
        '-s',
        '--subdomain', 
        type=str2bool, 
        default=True, 
        nargs='?',
        help="Test all the subdomains as well"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', 
        '--domain', 
        help="Domian to be tested"
    )
    group.add_argument(
        '-f', 
        '--filename', 
        help="Filename that contains a list of domains to be tested"
    )
    parser.add_argument(
        '-m', 
        '--module', 
        choices=[
            'test_all',
            'get_fulldomain',
            'get_https_test',
            'get_report_from_ssllab',
            'generate_full_report',
            'test_none'
        ], 
        default='test_all', 
        required=True,
        help="What test module would you like to perform?"
    )
    parser.add_argument(
        '-o', 
        '--output', 
        choices=['file','database'], 
        default='file', 
        required=True,
        help="Choose the form of output of test results (file by default)"
    )
    return parser.parse_args()

def init_dir():
    if not os.path.exists('scripts/util/log'):
        os.makedirs('scripts/util/log')
    if not os.path.exists('output/domain/crtsh'):
        os.makedirs('output/domain/crtsh')
    if not os.path.exists('output/domain/resolved_domain'):
        os.makedirs('output/domain/resolved_domain')
    if not os.path.exists('output/domain/dnsres'):
        os.makedirs('output/domain/dnsres')
    if not os.path.exists('output/domain/fulldomain'):
        os.makedirs('output/domain/fulldomain')
    if not os.path.exists('output/report/test_https/log'):
        os.makedirs('output/report/test_https/log')
    if not os.path.exists('output/report/error_domain'):
        os.makedirs('output/report/error_domain')
    if not os.path.exists('output/report/pic'):
        os.makedirs('output/report/pic')
    if not os.path.exists('output/report/ssllab/raw_results'):
        os.makedirs('output/report/ssllab/raw_results')
    if not os.path.exists('output/report/chart'):
        os.makedirs('output/report/chart')
    if not os.path.exists('output/report/domain_ip'):
        os.makedirs('output/report/domain_ip')
    if not os.path.exists('output/report/cert/cert_ct'):
        os.makedirs('output/report/cert/cert_ct')
    if not os.path.exists('output/report/cert/cert_from_domain'):
        os.makedirs('output/report/cert/cert_from_domain')
    if not os.path.exists('output/report/cert/cert_from_ip'):
        os.makedirs('output/report/cert/cert_from_ip')
    if not os.path.exists('output/report/cert/shared_cert'):
        os.makedirs('output/report/cert/shared_cert')

def run_module(cmd):
    try:
        subprocess.call(cmd, shell=True)
    except Exception as e:
        print(traceback.format_exc())

def test_all(subdomain, domains):
    if subdomain:
        run_module('python3 get_fulldomain.py ' + domains)
    else:
        d = domains.split(' ')
        for domain in d:
            with open('../output/domain/resolved_domain/' + domain + '.txt','w') as f:
                f.write(domain)
    run_module('python3 get_https_test.py ' + domains)
    run_module('python3 get_report_from_ssllab.py ' + domains)
    run_module('python3 generate_full_report.py ' + domains)

def init_db():
    conn = pymysql.connect(host=db_host,
                           port=3306,
                           user=db_user,
                           password=db_pass,
                           charset='utf8')
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS '+db_name+' CHARACTER SET utf8;')
    cursor.execute('USE '+db_name+';')
    cursor.execute("""CREATE TABLE IF NOT EXISTS `domains`(
                        `domain` VARCHAR(50) NOT NULL,
                        `time` TIME NOT NULL,
                        PRIMARY KEY(`domain`)
                    )CHARACTER SET utf8;""")
    conn.close()

def insert_db(domain, subdomains):
    conn = pymysql.connect(host=db_host,
                           port=3306,
                           user=db_user,
                           password=db_pass,
                           dataabse=db_name,
                           charset='utf8')
    cursor = conn.cursor()
    #在总的domains表中更新域名最新测试时间
    cursor.execute("""REPLACE INTO domains(domain, time)
                        VALUES('%s',NOW())""" 
                        % domain)
    #创建单个域名的表，存放测试结果
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS `%s`(
                            `subdomain` VARCHAR(50) NOT NULL,
                            PRIMARY KEY(`subdomain`)
                        )CHARACTER SET utf8;""" % domain)
        cursor.executemany("""REPLACE INTO `%s`(subdomain)
                                VALUES(%s)
                        """ % subdomains)
    except:
        conn.rollback()
        print("%s[!] Oops! someting wrong when creating table for %s.%s" % (R,domain,W))
    finally:
        db.close()

def store_res_to_db(domains):
    init_db()
    domains = domains.split(' ')
    for domain in domains:
        if os.file.exists('output/domain/resolves_domain/'+domain+'.txt'):
            f = open('output/domain/resolves_domain/'+domain+'.txt','r')
            subdomains = f.readall().split('\n')
            f.close()
            #insert into db 
            insert_db(domain, subdomains)

        else:
            print("%s[*] Domain:%s hasen't been tested yet!%s" % (R,domain,W))

def main(subdomain, domain, filename, module, output):
    if filename:
        f = open(filename)
        domains = ' '.join(f.readall().split('\n'))
        f.close()
    else:
        domains = domain
    os.chdir('scripts')
    if module == 'test_all':
        test_all(subdomain, domains)
        print("%s[*] Testing done!%s"%(G,W))
    elif module != 'test_none':
        run_module('python3 ' + module + '.py ' + domains)
        print("%s[*] Testing done!%s"%(G,W))
    else:
        print("%s[*] Nothing to test.%s"%(G,W))
    os.chdir('..')
    if output == 'database':
        print("%s[*] Now saving the domain info to database...%s"%(G,W))
        store_res_to_db(domains)

def interactive():
    args = parse_args()
    subdomain = args.subdomain
    domain = args.domain
    filename = args.filename
    module = args.module
    output = args.output
    banner()
    init_dir()
    res = main(subdomain, domain, filename, module, output)
if __name__=="__main__":
    interactive()
