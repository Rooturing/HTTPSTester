# coding: utf-8
import sys
import os
from requests_html import AsyncHTMLSession
from urllib.parse import unquote
import aiofiles
import asyncio
import json
import time
import re
import logging
from  pybloom_live import ScalableBloomFilter as SBF

G = '\033[92m'  # green
Y = '\033[93m'  # yellow
B = '\033[94m'  # blue
R = '\033[91m'  # red
W = '\033[0m'   # white
C = '\033[36m'  # cyan

input_dirname = ''
output_dirname = ''
num = 1 
global domain 
global bf_ready
global bf_file

def Extractor(url):
    str = url.strip().split("?", 1)
    return str[0]

async def wrt(url, act):
    global bf_file, domain, output_dirname
    if url not in bf_file:
        bf_file.add(url)
        async with aiofiles.open(output_dirname + domain + "_login_url.txt", 'a+') as afp:
            print("Login find! Url: {}, action: {}".format(url, act))
            await afp.write("url: " + url + ", action: " + str(act) + "\n")

async def finding(url, r):
    try:
        pq = r.html.pq
        pd_ele = pq.find("input[type='password']")
        ancestor_ele = pd_ele.closest('form')
        if ancestor_ele:
            act = ""
            try:
                act = ancestor_ele.attr['action']
                if not re.match(r'http.*', act):
                    act = r.html.url + act
            except:
                pass
            await wrt(r.html.url, act)
    except Exception as e:
        #print(e)
        logging.error(e)


async def check(url, r):
    global bf_ready
    try:
        if not Extractor(r.html.url) in bf_ready:
            bf_ready.add(Extractor(r.html.url))
            await finding(url, r)
            await r.html.arender
            await finding(url, r)
    except:
        pass
    for i in r.html.absolute_links:
        if not Extractor(i) in bf_ready:
            bf_ready.add(Extractor(i))
            try:
                asession = AsyncHTMLSession()
                r_ = await  asession.get(i, timeout=5)
                # time.sleep(2)
                if Extractor(r_.html.url) not in bf_ready:
                    bf_ready.add(Extractor(r_.html.url))
                    await finding(url, r_)
                    await r_.html.arender(retries=3)
                    await finding(url, r_)
            except:
                pass

async def spider(url_s, len_):
    global num, bf_ready
    print("Start for: %d/%d:%s" % (num, len_, url_s))
    num = num + 1
    if not Extractor(url_s) in bf_ready:
        bf_ready.add(Extractor(url_s))
        try:
            asession = AsyncHTMLSession()
            r = await asession.get(url_s, timeout=5)
            # time.sleep(2)
            await check(url_s, r)
        except Exception as e:
            #print(e)
            logging.error(e)
    num = num - 1
    print("Done for: %d/%d:%s" % (num, len_, url_s))


def test_json(f_json):
    for key in f_json:
        if re.match(r'http_only', key):
            len_ = len(f_json['http_only'])
            loop = asyncio.get_event_loop()
            cor = [spider("http://" + i, len_) for i in f_json["http_only"]]
            loop.run_until_complete(asyncio.gather(*cor))
        elif re.match(r'https_only', key):
            len_ = len(f_json['https_only'])
            loop = asyncio.get_event_loop()
            cor = [spider("https://" + i, len_) for i in f_json["https_only"]]
            loop.run_until_complete(asyncio.gather(*cor))
        elif re.match(r'https_default', key):
            len_ = len(f_json['https_default'])
            loop = asyncio.get_event_loop()
            cor = [spider("https://" + i, len_) for i in f_json["https_default"]]
            loop.run_until_complete(asyncio.gather(*cor))
        elif re.match(r'https_reachable', key):
            len_ = len(f_json['https_reachable'])
            loop = asyncio.get_event_loop()
            cor = [spider("https://"+i, len_) for i in f_json["https_reachable"]]
            loop.run_until_complete(asyncio.gather(*cor))
        else:
            continue

def test_txt(urls):
    len_ = len(urls)
    i = 0
    n = 10
    for j in range(int(len_/n) + (1 if len_%n else 0)):
        loop = asyncio.get_event_loop()
        cor = [spider(url, n) for url in urls[i:i+n]]
        loop.run_until_complete(asyncio.gather(*cor))
        if i + n >= len_:
            n = len_ % n 
        else:
            i += n


def main(domain):
    global input_dirname
    global file_format
    global bf_ready
    global bf_file

    filename = input_dirname + domain+'.' + file_format
    if not os.path.isfile(filename):
        print("%s[!] File not exists for %s!%s" % (R,filename,W))
    else:
        print("%s[*]Now testing for %s.%s" % (G,domain,W))
        if file_format == 'txt':
            with open(filename, 'r') as f:
                urls = f.read().split('\n')
            for u in urls:
                if not u:
                    urls.remove(u)
            len_tmp = len(urls)

            # 初始化布隆参数
            bf_ready = SBF(initial_capacity=len_tmp*50, error_rate=0.001, mode=SBF.LARGE_SET_GROWTH)
            bf_file = SBF(initial_capacity=len_tmp*50, error_rate=0.001, mode=SBF.LARGE_SET_GROWTH)

            test_txt(urls)

        elif file_format == 'json':
            with open(filename, 'r') as f:
                f_json = json.load(f)
            len_tmp = len(f_json["http_only"]) + len(f_json["https_only"]) + len(f_json["https_default"]) + len(f_json["https_reachable"])

            # 初始化布隆参数
            bf_ready = SBF(initial_capacity=len_tmp*50, error_rate=0.001, mode=SBF.LARGE_SET_GROWTH)
            bf_file = SBF(initial_capacity=len_tmp*50, error_rate=0.001, mode=SBF.LARGE_SET_GROWTH)

            # 开始测试
            test_json(f_json)


if __name__ == '__main__':
    logging.basicConfig(filename="error.log", level=logging.WARNING)
    start_time = time.time()
    file_format = sys.argv[1]
    input_dirname = sys.argv[2]
    output_dirname = sys.argv[3]
    domains = sys.argv[4:]
    if not file_format:
        print("%s[!] Please input the file format (json or txt)!%s" % (R,W))
    if not input_dirname:
        print("%s[!] Please input the dirname that contains the urls!%s" % (R,W))
    if not output_dirname:
        print("%s[!] Please input the dirname that stores the output results!%s" % (R,W))
    if not domains:
        print("%s[!] Please input the domains to test!%s" % (R,W))
    if not re.match(r'.+/$',input_dirname):
        input_dirname += '/'
    if not re.match(r'.+/$',output_dirname):
        output_dirname += '/'
    if not os.path.exists(input_dirname):
        print("%s[!] The directory %s doses not exists!%s" % (R,dirname,W))
    for domain in domains:
        main(domain)
    print('Testing done! Use time:{:.2f}s'.format(time.time() - start_time))
