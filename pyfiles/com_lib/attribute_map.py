from .variables import *
from .tools import *
from typing import List
import json


class AttributeDict(object):
    attribute_list = None
    attribute_dict = {}
    name_dict = {}

    def __init__(self):
        with open(PRO_PATH + '/data/attr_dict.json') as f:
            self.attribute_list = json.load(f)
        for category in self.attribute_list:
            attributes = self.attribute_list[category]
            for attribute in attributes:
                attr_name = attributes[attribute]['name'].split(',')
                self.attribute_dict[attribute] = {'category': category, 'name': attr_name[0]}
                for name in attr_name:
                    # 注意编码问题
                    # name_code = name.encode('utf-8').decode('utf-8')
                    if name not in self.name_dict:
                        self.name_dict[name] = attribute

    def echo_dict(self):
        print(json.dumps(self.name_dict, indent=1, ensure_ascii=False))

    def classify(self, attributes: List[str]):
        res = {}
        for attribute in attributes:
            if attribute in self.attribute_dict:
                category = self.attribute_dict[attribute]['category']
                if category in res:
                    res[category].append(attribute)
                else:
                    res[category] = [attribute]
            else:
                print('attributeDict: ' + attribute + ' 尚未支持')
        return res

    def columns_attr(self, columns: str, return_old=True):
        """
        将汉字属性转换为统一的英文属性，将存在于属性库中的属性与不存在的分开两个列表
        :param columns:
        :param return_old: 是否返回旧属性
        :return:
        """
        new_columns = []
        old_columns = []
        for column in columns:
            ecolumn = del_bracket(column)
            if ecolumn in self.name_dict:
                new_columns.append(self.name_dict[ecolumn])
            else:
                old_columns.append(column)
        if return_old:
            return new_columns, old_columns
        return new_columns
