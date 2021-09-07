# -*- coding: utf-8 -*-
# 利用爬虫获取需要的数据
import requests

from lxml import etree


def get_ts_attr_name(url):
    # url = 'https://www.waditu.com/document/2?doc_id=79'
    html = requests.get(url)
    dom_tree = etree.HTML(html.content)
    tds = dom_tree.xpath("//tr/td/text()")
    # attr_names = map(lambda x: x.text, tds)
    tds = tds[35:]
    attr = []
    attr_info = []
    counter = 4
    for i in range(len(tds)):
        if i % counter == 0:
            attr_info.append(tds[i])
        if i % counter == 1:
            attr.append(tds[i])
    print(attr)
    print(attr_info)


if __name__ == '__main__':
    get_ts_attr_name(url='https://www.waditu.com/document/2?doc_id=79')