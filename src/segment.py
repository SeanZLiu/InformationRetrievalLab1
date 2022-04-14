#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/5/20 上午10:58
# @Author  : Jingshuo Liu
# @File    : segment
import json
from ltp import LTP


def get_st_words(file_path):
    with open(file_path,'r') as stp_file:
        stop_words = set(stp_file.readlines())
    return stop_words


def seg_content(stop_words_path, input_path, output_path='preprocessed.json'):
    stop_words = get_st_words(stop_words_path)
    ltp = LTP()  # 加载ltp
    result = []
    num = 0
    with open(input_path,'r',encoding='utf-8') as input_jsf:
        list = [json.loads(line) for line in input_jsf]
        for ele in list:
            if ele['title'] and ele['paragraphs']:
                seged_title,seged_paras = [], []
                for token in ltp.seg([ele['title']])[0][0]:
                    if token not in stop_words:
                        seged_title.append(token)
                for token_lst in ltp.seg(ele['paragraphs'])[0]:
                    for token in token_lst:
                        if token not in stop_words:
                            seged_paras.append(token)
                result.append({"url": ele['url'], "title": seged_title, 'paragraphs':seged_paras,'file_name':ele['file_name']})
                num += 1
            if num >= 10:  # 为获得部分结果 先读十个就退出
                break

    for res in result:
        print(res)
    stream = [json.dumps(res, ensure_ascii=False) for res in result]
    with open(output_path, 'w', encoding='utf-8') as js_file:
        js_file.write('\n'.join(stream))


if __name__ == '__main__':
    seg_content(stop_words_path='stopwords.txt',input_path='output/js_out_std.json',)
