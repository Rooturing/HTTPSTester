import pymysql
import sys,os
import datetime

root_path = os.path.abspath(".")
sys.path.append(root_path)

from config import DB_NAME, DB_PASSWD, DB_USER

db_user = DB_USER
db_passwd = DB_PASSWD
db_name = DB_NAME

def dump_raw_cert():
    cert_list = list()

    with open('./file/result/certs.txt', 'w') as f:
        conn = pymysql.connect(host="127.0.0.1", user=db_user, passwd=db_passwd, db=db_name)
        cursor = conn.cursor()
        cursor.execute("select * from raw_cert")
        res = cursor.fetchall()
        for i in range(len(res)):
            t = '\t'.join(res[i])
            cert_list.append(t)
        f.write('\n'.join(cert_list))
        cursor.close()
        conn.close()
    print("%d raw certs dumped" % len(res))

def dump_domains():
    domain_list = list()
    
    with open('./file/result/domains.txt', 'w') as f:
        conn = pymysql.connect(host="127.0.0.1", user=db_user, passwd=db_passwd, db=db_name)
        cursor = conn.cursor()
        cursor.execute("select * from domains")
        res = cursor.fetchall()
        for i in range(len(res)):
            domain_list.append(res[i][0])
        f.write('\n'.join(domain_list))
        cursor.close()
        conn.close()
    print("%d domains dumped" % len(res))

def dump_cert_info():
    cert_info = list()
    
    with open('./file/result/cert_info.txt', 'w') as f:
        conn = pymysql.connect(host="127.0.0.1", user=db_user, passwd=db_passwd, db=db_name)
        cursor = conn.cursor()
        cursor.execute("select * from cert_info")
        res = cursor.fetchall()
        
        for i in range(len(res)):
            serial_num = res[i][0]
            issuer = res[i][1]  # eval()
            not_before = res[i][2].strftime("%Y-%m-%d %H:%M:%S")
            not_after = res[i][3].strftime("%Y-%m-%d %H:%M:%S")
            subject = res[i][4]
            SAN = res[i][5]
            t = serial_num+'\t'+issuer+'\t'+not_before+'\t'+not_after+'\t'+subject+'\t'+SAN
            cert_info.append(t)
        f.write('\n'.join(cert_info))
        
        cursor.close()
        conn.close()
    print("%d cert info dumped" % len(res))

dump_cert_info()















