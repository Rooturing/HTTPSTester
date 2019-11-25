from lxml import etree
import requests

def compare_ancestor(ancestors1, ancestors2):
    ancestor_tmp = list()
    for ancestor1 in ancestors1:
        for ancestor2 in ancestors2:
            if len(ancestor1) == len(ancestor2):
                # if ancestor1[len(ancestor1)-1] == ancestor2[len(ancestor2)-1]:
                ancestor_tmp.append(ancestor2)
            else:
                continue
    return ancestor_tmp

def get_ancestors_from_id(ele_ids, ele_type, page):
    ele_ancestors = list()
    for ele_id in ele_ids:
        str_t = "//"+ele_type+"[@id='"+ele_id+"']/ancestor::*"
        ele_ancestor = page.xpath(str_t)
        ele_ancestors.append(ele_ancestor)
    return ele_ancestors
    

def test_if_doamin(domain):
    if "http" not in domain:    
        url = "http://" + domain
    else:
        url = domain
    headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36' }

    re = requests.get(url, headers = headers)
    page = etree.HTML(re.text)
    
    # to find passwd
    pd_ele_id = page.xpath("//input[@type='password']/@id")
    if not (len(pd_ele_id)):
        return False
    pd_ele_ancestors = get_ancestors_from_id(pd_ele_id, "input", page)
    

    # to find submit
    sm_ele_id = page.xpath("//input[@type='submit']/@id")
    if not (len(sm_ele_id)):
        return False
    sm_ele_ancestors = get_ancestors_from_id(sm_ele_id, "input", page)

    ancestors_tmp = compare_ancestor(pd_ele_ancestors, sm_ele_ancestors)
    

    # to find text
    text_ele_id = page.xpath("//input[@type='text']/@id")
    if not (len(text_ele_id)):
        return False
    text_ele_ancestors = get_ancestors_from_id(text_ele_id, "input", page)
    ancestors_tmp = compare_ancestor(text_ele_ancestors, ancestors_tmp)
    if(len(ancestors_tmp)):
        print(ancestors_tmp)
        return True
    else:
        return False
    

if __name__ == '__main__':
    while True:
        try:
            domain = input("input a domain:")
            if test_if_doamin(domain):
                print("ok!")
        except:
            break
