import sys
import re
import requests
from lxml import etree

def get_domain(url):
    pattern = re.compile("(.*?://)(.*)")
    domain = re.match(pattern, url)
    if "/" in domain.group(2):
        pattern2 = re.compile("(.*)?/.*")
        domain_t = re.match(pattern2, domain.group(2))
    domain = domain.group(1) + domain_t.group(1)
    return domain

def get_hrefs(domain, html):

    base_domain = '.'.join(domain.split['.'][-3])

    page = etree.HTML(html)
    href_s = page.xpath("//a[@href]/@href")

    for href in href_s:
        print(href)
        if base_domain in href:
            print(href)

