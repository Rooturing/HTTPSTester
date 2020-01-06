# -*- coding: utf-8 -*-
import argparse
import os
import subprocess
import traceback
import time
import sys
from config import *
from scripts import *
from scripts.util import *
import signal
from multiprocessing import Pool
import tqdm
import pymysql
import warnings
warnings.filterwarnings("ignore")

G = '\033[92m'  # green
Y = '\033[93m'  # yellow
B = '\033[94m'  # blue
R = '\033[91m'  # red
W = '\033[0m'   # white
C = '\033[36m'  # cyan

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

class Interactive:
    def __init__(self):
        self.basedir = os.getcwd()
        args = self.parse_args()
        self.subdomain = args.subdomain
        self.domain = args.domain
        self.domains = []
        self.filename = args.filename
        self.module = args.module
        self.output = args.output
        self.process_num = os.cpu_count()
        self.banner()
        self.init_dir()
        self.main()
    def banner(self):
        print("""%s
          _   _ _____ _____ ____  ____ _____         _            
         | | | |_   _|_   _|  _ \/ ___|_   _|__  ___| |_ ___ _ __ 
         | |_| | | |   | | | |_) \___ \ | |/ _ \/ __| __/ _ \ '__|
         |  _  | | |   | | |  __/ ___) || |  __/\__ \ ||  __/ |   
         |_| |_| |_|   |_| |_|   |____/ |_|\___||___/\__\___|_| %s 
        
          A Large-scale HTTPS evaluation tool with high performance.%s
        """%(C,B,W))

    def parser_error(self, errmsg):
        self.banner()
        print("Usage: python3 " + sys.argv[0] + " [Options] use -h for help")
        print(R + "Error: " + errmsg + W)
        sys.exit()

    def str2bool(self, v):
        if isinstance(v,bool):
            return v
        if v.lower() in ('yes','true','t','y','1'):
            return True
        elif v.lower() in ('no','false','f','n','0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    def parse_args(self):
        parser = argparse.ArgumentParser(epilog='\tExample: \r\npython3 ' + sys.argv[0] + " -d google.com")
        parser.error = self.parser_error
        parser._optionals.title = 'OPTIONS'
        parser.add_argument(
            '-s',
            '--subdomain', 
            type=self.str2bool, 
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
                'full_domain',
                'test_https',
                'test_login',
                'full_report',
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

    def init_dir(self):
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
        if not os.path.exists('output/report/test_login'):
            os.makedirs('output/report/test_login')


    def init_db(self):
        conn = pymysql.connect(host=db_host,
                               port=3306,
                               user=db_user,
                               password=db_pass,
                               database=db_name,
                               charset='utf8')
        cursor = conn.cursor()
        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS `domains`(
                                `domain` VARCHAR(50) NOT NULL,
                                `time` DATETIME NOT NULL,
                                PRIMARY KEY(`domain`)
                            )CHARACTER SET utf8;""")
        except:
            pass
        finally:
            cursor.close()
            conn.close()

    def insert_db(self, domain, subdomains):
        conn = pymysql.connect(host=db_host,
                               port=3306,
                               user=db_user,
                               password=db_pass,
                               database=db_name,
                               charset='utf8')
        cursor = conn.cursor()
        cursor.execute("""REPLACE INTO domains(domain, time)
                            VALUES('%s',NOW())""" 
                            % domain)
        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS `%s`(
                                `subdomain` VARCHAR(50) NOT NULL,
                                PRIMARY KEY(`subdomain`)
                            )CHARACTER SET utf8;""" % domain)
            cursor.executemany('REPLACE INTO `' + domain + '`(subdomain) VALUES(%s)', subdomains)
            conn.commit()
            print("%s[*] %d subdomains inserted for %s.%s" % (G,cursor.rowcount,domain,W))
        except Exception as e:
            conn.rollback()
            print("%s[!] Oops! someting wrong when creating table for %s.%s" % (R,domain,W))
            print("%s[*] Error message: %s.%s" % (Y,str(e),W))
        finally:
            cursor.close()
            conn.close()

    def store_res_to_db(self, domains):
        self.init_db()
        for domain in domains:
            if os.path.exists('output/domain/resolved_domain/'+domain+'.txt'):
                f = open('output/domain/resolved_domain/'+domain+'.txt')
                subdomains = f.read().strip()
                f.close()
                if subdomains:
                    subdomains = subdomains.split('\n')
                    self.insert_db(domain, subdomains)
                else:
                    print("%s[*] Domain:%s doesn't have any subdomain to insert!%s" % (R,domain,W))
            else:
                print("%s[*] Domain:%s hasen't been tested yet!%s" % (R,domain,W))

    def worker(self, domain):
        print("%s[*] Start testing %s!%s"%(G,domain,W))
        if 'test_https' or 'test_all' in self.module:
            if not self.subdomain:
                for domain in self.domains:
                    with open(self.basedir + '/output/domain/resolved_domain/' + domain + '.txt','w') as f:
                        f.write(domain)
            test_https.TestHTTPS(domain, self.basedir).run() 
        elif self.module == 'full_report':
                test_https.TestHTTPS(domain, self.basedir).run() 
        elif self.module == 'test_login':
            pass
        print("%s[*] Testing done for %s!%s"%(G,domain,W))

    def main(self):
        startTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
        if self.filename:
            f = open(self.filename)
            self.domains = f.read().strip().split('\n')
            f.close()
        else:
            self.domains = [self.domain]
        print("%s[*] Start testing for module %s, domain number: %d.%s"%(G,self.module,len(self.domains),W))
        if 'full_domain' in self.module or 'test_all' in self.module:
            for domain in self.domains:
                fulldomain.Fulldomain(domain, self.basedir).run()
        elif self.module != 'test_none':
            with Pool(processes=self.process_num) as pool:
                try:
                    pool.map(self.worker, self.domains)
                except Exception as e:
                    print(e)
        else:
            print("%s[*] Nothing to test.%s"%(G,W))
        if self.output == 'database':
            print("%s[*] Now saving the domain info to database...%s"%(G,W))
            self.store_res_to_db(domains)
        endTime = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
        print("%s[*] All done! Start time: %s, end time: %s.%s" % (C,startTime, endTime,W))


if __name__=="__main__":
    Interactive()
