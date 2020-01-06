import os
import logging
#configure your mysql database
db_host = 'localhost'
db_user = 'test'
db_pass = '123456'
db_name = 'https_test'

# DNS
resolver_nameservers = [
    '119.29.29.29', '182.254.116.116',  # DNSPod
    '180.76.76.76',  # Baidu DNS
    '223.5.5.5', '223.6.6.6',  # AliDNS
    '114.114.114.114', '114.114.115.115'  # 114DNS
    '8.8.8.8', '8.8.4.4',  # Google DNS
    '1.0.0.1', '1.1.1.1'  # CloudFlare DNS
    '208.67.222.222', '208.67.220.220'  # OpenDNS
    ] 
resolver_timeout = 5.0  
resolver_lifetime = 30.0 
limit_resolve_conn = 500  

# logger
logger = logging.getLogger('httpstester')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
LOG_FILE = True
if LOG_FILE:
    logpath = os.getcwd() + '/output/log/'
    if not os.path.exists(logpath):
        os.mkdir(logpath)
    fh = logging.FileHandler(logpath + 'httpstester.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

