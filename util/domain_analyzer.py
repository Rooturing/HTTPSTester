import nmap
from logger import logger
import threading, time
from queue import Queue

SHARE_Q = Queue.Queue()

class nmapThread(threading.Thread):
    




def nmapping():
    nm = nmap.PortScannerAsync()
    nm.scan('afast.ws', arguments='-v -A -O', callback=callback_result)
    while nm.still_scanning():
        nm.wait(2)

def callback_result(host, scanresult):
    print(host, scanresult)


def count_domain():
    fd = open("../file/result/domains.txt", "r")
    fc = open("../file/result/certs.txt", "r")

    domain_list = fd.read().split('\n')
    certs = fc.read().split('\t')

    with open("../file/result/res.txt", "w") as f:
        for domain in domain_list:
            num = certs.count(domain)
            if num:
                f.write("%d cert(s) found for domain %s\n" % (num, domain))
    fd.close()
    fc.close()


if __name__ == "__main__":
    nmapping()
