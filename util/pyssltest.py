#!/usr/bin/env python

# Copyright (c) Mohesh Mohan (h4hacks.com).

'''
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''

# Completed standalone multi threaded script for SSL labs API - 18th June 2015, Mohesh Mohan
import re
import sys
import getopt
import argparse
import requests
import json
import csv
import linecache
import queue
import threading
import time
import random
import os


pstart = {"publish": "off", "ignoreMismatch": "on",
          "all": "done", "host": "", "startNew": "on"}
prepeat = {"publish": "off", "ignoreMismatch": "on", "all": "done", "host": ""}
pinfo = {}
mainapps = []
jobtrack = {}
apipath = "https://api.ssllabs.com/api/v2/"
clientheaders = {"User-Agent": "pyssltest 1.3"}

infocommand = apipath + "info"
analyzecommand = apipath + "analyze"
getdatacommand = apipath + "getEndpointData"


def testBit(int_type, offset):
    mask = 1 << offset
    return(int_type & mask)


def parsetodomain(url):
    # dirty fix to match our dirty apps db :P
    if "http" not in url:
        url = "http://" + url
    return (url)


def isURL(url):
    if "http" not in url:
        url = "http://" + url
    if "*" in url:
        return False
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return (regex.match(url))


def parseresults(result, mainapp, returncode):
    print("\nresult= \n")
    print(result)

    pdomain = mainapp
    print("\nParsing: " + str(mainapp))
    domain = ip = grade = sgrade = certchain = chaininc = wrongd = certexp = selfcert = commonnames = altnames = thumbp = 'not tested'
    try:
        # domain
        try:
            domain = result['host']
        except Exception:
            domain = "error"
            pass

        # IP
        try:
            ip = result['endpoints'][0]['ipAddress']
        except Exception:
            ip = "JSON err"
            pass

        # grade
        try:
            grade = result['endpoints'][0]['grade']
        except Exception:
            grade = "JSON err"
            pass

        # sgrade
        try:
            sgrade = result['endpoints'][0]['gradeTrustIgnored']
        except Exception:
            sgrade = "JSON err"
            pass

        # certchain
        try:
            certchain = "N"
            certmsg = int(result['endpoints'][0]['details']['cert']['issues'])
            chainp = testBit(certmsg, 0)
            if chainp != 0 or int(result['endpoints'][0]['details']['chain']['issues']) != 0:
                certchain = "Y"
        except Exception as e:
            # print str(e)
            certchain = "Err"
            pass

        # chainincomp
        try:
            chaininc = "N"
            certmsg1 = int(result['endpoints'][0]
                           ['details']['chain']['issues'])
            chainp1 = testBit(certmsg1, 1)
            if chainp1 != 0:
                chaininc = "Y"
        except Exception as e:
            # print str(e)
            chaininc = "Err"
            pass

        # wrong domain
        try:
            wrongd = "N"
            certmsg = int(result['endpoints'][0]['details']['cert']['issues'])
            chainp = testBit(certmsg, 3)
            if chainp != 0:
                wrongd = "Y"
        except Exception as e:
            # print str(e)
            wrongd = "Err"
            pass

        # selfcert
        try:
            selfcert = "N"
            certmsg = int(result['endpoints'][0]['details']['cert']['issues'])
            chainp = testBit(certmsg, 6)
            if chainp != 0:
                selfcert = "Y"
        except Exception as e:
            # print str(e)
            selfcert = "Err"
            pass

        # certexp
        try:
            certexp = "N"
            certmsg = int(result['endpoints'][0]['details']['cert']['issues'])
            ntbef = testBit(certmsg, 1)
            ntaf = testBit(certmsg, 2)
            if ntbef != 0 or ntaf != 0:
                certexp = "Y"
        except Exception as e:
            # print str(e)
            certexp = "Err"
            pass

        # thumb print
        try:
            thumbp = result['endpoints'][0]['details']['cert']['sha1Hash']
        except Exception as e:
            # print str(e)
            thumbp = "JSON err"
            pass

        # common names
        try:
            commonnames = ""
            for common in result['endpoints'][0]['details']['cert']['commonNames']:
                commonnames = " ".join((commonnames, common))
        except Exception as e:
            # print str(e)
            commonnames = "JSON err"
            pass

        # alternate names
        try:
            altnames = ""
            for alt in result['endpoints'][0]['details']['cert']['altNames']:
                altnames = " ".join((altnames, alt))
        except Exception as e:
            # print str(e)
            altnames = "JSON err"
            pass

        # For error values
        # No SSL
        try:
            if result['endpoints'][0]['statusMessage'] == "No secure protocols supported":
                grade = "No SSL/TLS"
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'NA'
        except Exception as e:
            pass

        # No DNS
        try:
            if result['statusMessage'] == "Unable to resolve domain name":
                grade = "No DNS"
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'NA'
        except Exception as e:
            pass
        # Unknown errors from server stupid stuff. not optimal need to work on this
        try:
            if "Unable" in result['endpoints'][0]['statusMessage']:
                grade = result['endpoints'][0]['statusMessage']
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'Error'
        except Exception as e:
            pass
        try:
            if "Failed" in result['endpoints'][0]['statusMessage']:
                grade = result['endpoints'][0]['statusMessage']
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'Error'
        except Exception as e:
            pass
        try:
            if "RFC 1918" in result['endpoints'][0]['statusMessage']:
                grade = result['endpoints'][0]['statusMessage']
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'Error'
        except Exception as e:
            pass

        try:
            if "Unexpected" in result['endpoints'][0]['statusMessage']:
                grade = result['endpoints'][0]['statusMessage']
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'Error'
        except Exception as e:
            pass
        try:
            if "Internal error" in result['endpoints'][0]['statusMessage']:
                grade = result['endpoints'][0]['statusMessage']
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'Error'
        except Exception as e:
            pass
        try:
            if "Internal Error" in result['endpoints'][0]['statusMessage']:
                grade = result['endpoints'][0]['statusMessage']
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'Error'
        except Exception as e:
            pass

        try:
            if result['status'] == "ERROR" and result['statusMessage'] != "Unable to resolve domain name":
                grade = "Error from server, need manual tests"
                sgrade = certchain = chaininc = wrongd = selfcert = certexp = thumbp = commonnames = altnames = 'Error'
        except Exception as e:
            pass

        row = ""
        row = domain, ip, grade, sgrade, wrongd, certexp, selfcert, certchain, chaininc, thumbp, commonnames, altnames
        print("Parsed: " + str(mainapp))
        print("\nrow:\n")
        print(row)
        return(row)

    except Exception as e:
        row = domain, 'Failed', grade, sgrade, wrongd, certexp, selfcert, certchain, chaininc, thumbp, commonnames, altnames
        return(row)


def status(jobtrack):
    ready = 0
    inva = 0
    errc = 0
    pend = 0
    #print('\n' * 100)
    for key in jobtrack:
        if jobtrack[key] == "Not Tested":
            pend = pend + 1
        elif jobtrack[key] == "Invalid":
            inva = inva + 1
        elif jobtrack[key] == "ERROR":
            errc = errc + 1
        elif jobtrack[key] == "READY":
            ready = ready + 1
    print("\n")
    print("There are " + str(pend) + " pending")
    print("There are " + str(inva) + " Invalid")
    print("There are " + str(errc) + " errors")
    print("There are " + str(ready) + " ready")
    print("There are " + str(threading.activeCount()) + " Threads")


def runscan(q,domain):
    while not q.empty():
        mydata = threading.local()
        mydata.scanning = True
        mydata.dom = q.get()  # get the item from the queue
        mydata.pstart = pstart
        mydata.prepeat = prepeat
        print("Now Processing " + str(mydata.dom))
        print("\n Active threads :" + str(threading.activeCount()))
        while (mydata.scanning):
            try:
                status(jobtrack)

                # if for some unknown reason a thread just don't die, lets kill it
                if jobtrack[mydata.dom] != "Scanning" and jobtrack[mydata.dom] != "Not Tested":
                    q.task_done()
                    mydata.scanning = False

                # Check if scan is initiated for this one
                if jobtrack[mydata.dom] == "Not Tested":
                    mydata.pstart['host'] = mydata.dom
                    mydata.response = requests.get(
                        analyzecommand, headers=clientheaders, params=mydata.pstart)
                    jobtrack[mydata.dom] = "Scanning"
                else:
                    mydata.prepeat['host'] = mydata.dom
                    mydata.response = requests.get(
                        analyzecommand, headers=clientheaders, params=mydata.prepeat)
                    mydata.response.body = mydata.response.json()
                    # did we get any valid response?
                    if 'status' in mydata.response.body:
                        if mydata.response.body['status'] == "READY" or mydata.response.body['status'] == "ERROR":
                            mydata.host = mydata.response.body['host']
                            print("Response is for " + mydata.host)
                            #print("Dom is " + mydata.dom)
                            if mydata.host == mydata.dom:
                                jobtrack[mydata.host] = mydata.response.body['status']
                                print("Writing response...")
                                mydata.fo = open(
                                        "report/ssllab/raw_results/"+domain+"/"+mydata.host.strip("http://")+".txt", "w")
                                # mydata.fo.write(mydata.response.raw_body);
                                json.dump(mydata.response.body, mydata.fo)
                                # Close opend file
                                mydata.fo.close()
                                q.task_done()
                                mydata.scanning = False
                                print(mydata.host + " is " +
                                      mydata.response.body['status'])
                mydata.headers1 = mydata.response.headers
                if mydata.response.status_code == 429:
                    print("\nThread: " + str(mydata.dom) +
                          " to sleep 10 secs due to 429 from server")
                    time.sleep(10)
                elif mydata.response.status_code == 503 or mydata.response.status_code == 529:
                    print("\n server overload, Response code is :" +
                          str(mydata.response.status_code))
                    randtime = random.randrange(100, 500)
                    print("\n Sleeping for :" + str(randtime))
                    time.sleep(randtime)
                time.sleep(3)  # delays for 5 seconds
                # print headers1['X-Max-Assessments']
            except Exception as e:
                print(str(e))
                try:
                    if 'errors' in mydata.response.body:
                        jobtrack[mydata.dom] = mydata.response.body['status']
                        mydata.fo = open("report/ssllab/raw_results/"+domain+"/"+mydata.dom.strip("http://")+".txt", "w")
                        json.dump(mydata.response.body, mydata.fo)
                        mydata.fo.close()
                        q.task_done()
                        mydata.scanning = False
                except Exception as e:
                    print(str(e))
                    pass
                pass


def run(domain,inputfile, outputfile):

    if not os.path.exists("report/ssllab/raw_results/"+domain):
        os.mkdir("report/ssllab/raw_results/"+domain)

    in_file = inputfile
    line_no = 1
    diter = ""
    read_line = linecache.getline(inputfile, line_no).rstrip()

    while read_line is not "":
        line_no = line_no + 1
        mainapps.append(read_line)
        diter = parsetodomain(read_line)
        if isURL(read_line):
            jobtrack[diter] = "Not Tested"
        else:
            jobtrack[diter] = "Invalid"
            print(read_line + " is invalid")
        read_line = linecache.getline(in_file, line_no).rstrip()

    total_lines = line_no - 1

    print("There are %d Urls read from the File" % (total_lines))

    # print mainapps
    print("\n Number of URLs is identified is " + str(len(mainapps)))
    # print "\n"
    # print jobtrack
    print("\n Number of domains is " + str(len(jobtrack)))

    q = queue.Queue()
    # put items to queue
    for key in jobtrack:
        if jobtrack[key] != "Invalid":
            q.put(str(key))
        else:
            print(str(key) + " is not added to queue as its invalid")

    for i in range(100):
        t1 = threading.Thread(target=runscan, args=(q,domain))
        t1.daemon = True
        t1.start()  # start the thread

    q.join()

    print("\nFinally")
    print("jobtrack: "+str(jobtrack))
    csvw = csv.writer(open(outputfile, 'w'))
    csvw.writerow(['Domain', 'IP', 'Grade', 'Secondary grade', 'wrong domain', 'cert expired', 'self signed cert',
                   'cert chain issue', 'Cert chain incomplete', 'Thumbprint', 'common names', 'alternate names'])

    for app in mainapps:
        try:
            curdom = parsetodomain(app)
            #print("\ncurdon: " +curdom)
            #print("\napp: "+app)
            resfile = open("report/ssllab/raw_results/"+domain+"/"+app+".txt", "r")
            
            jsonresults = json.load(resfile)
            resfile.close()
            row = parseresults(jsonresults, app, jobtrack[curdom])
            csvw.writerow(row)
        except Exception as e:
            print(str(e))
            csvw.writerow([app, curdom, str(e), jobtrack[curdom], 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error',
                           'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error', 'Error'])
            pass
