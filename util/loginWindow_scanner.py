#coding:utf-8
from requests_html import HTMLSession
import re
import sys

session = HTMLSession()

def check_login(url):
    r = session.get(url)
    print("now checking " + url)
    print(r)
    r.html.render(retries=3,timeout=15.0,wait=0.5) #js render
    forms = r.html.find('input')
    for form in forms:
        #print(form)
        if(re.findall(r'password',str(form))):
            #print(form)
            print("[+]: login form found ! url : " + url + "\n")
    return r

def crawl(r):
    _links = set()
    links = r.html.absolute_links
    for link in links:
        link = link.split('#')[0]
        if link[0:4] == "http":
            _links.add(link)
    return list(_links)

if __name__ == "__main__":
    targets_list = sys.argv[1:]
    #targets_list = ["http://127.0.0.1/1.html"]
    for target in targets_list:
        r = check_login(target)
        links = crawl(r)
        diff_links = [link for link in links if not link in targets_list]
        print(diff_links)
        for new_link in diff_links:
            try:
                check_login(new_link)
            except:
                continue
