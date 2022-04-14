#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/5/18 上午8:35
# @Author  : Jingshuo Liu
# @File    : craw.py
import json
import urllib.request
import urllib.error
import threading
import queue
from bs4 import BeautifulSoup
import socket
import re
import http.client





# 定义特殊数字
r_url = "http://hitgs.hit.edu.cn/"  # 从哈工大研究生院首页开始爬取 Mozilla/5.0
url_queue = queue.Queue()  # 管理器部分已爬取url队列
all_files = set()
wanted_num = 1000  # 需要的总网页数
spec_num = 100  # 带附件的网页数
gotten_num = 0  # 已获取总网页数目
spec_got = 0  # 已获取带附件的网页数
thr_lock = threading.Lock()  # 用于解决多线程并发冲突问题的锁
glo_result = []

def get_urls(root_url, wanted_num):
    urls = [root_url]
    for url in urls:
        req = urllib.request.Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            response = urllib.request.urlopen(req,timeout=1)
        except (urllib.error.URLError,socket.timeout):
            continue
        else:
            bs = BeautifulSoup(response.read(), "html.parser", from_encoding='utf-8')
            elements = bs.find_all('a')
            for elem in elements:
                if 'href' in elem.attrs:
                    new_url = elem.attrs['href']  # 获取href属性来获取url
                    if new_url.startswith('http') and new_url not in urls:
                        urls.append(new_url)
                    num_now = len(urls)
                    print(num_now)
                    if num_now > wanted_num:
                        return urls


def craw_web(url, dir_path='files/'):  # out_path为保存附件的文件夹
    global spec_got,glo_result,gotten_num

    print(url)
    try:
        res = urllib.request.urlopen(urllib.request.Request(url=url,headers={'User-Agent': 'IR-robot'}),timeout=5).read()
    except (urllib.error.URLError, socket.timeout, UnicodeEncodeError,ValueError,http.client.InvalidURL):
        return
    bs = BeautifulSoup(res,'html.parser')
    title = bs.find('body')  # 检查是否含有body部分
    if title:
        title = title.find_all(re.compile('^h[1-6]$'))  # 检查是否含有元素h1-h6
        if title:
            title = title[0].getText().strip()  # 设为标题
            paragraphs = []  # 用于正文内容
            for cont in bs.body.select('p'):
                strin = "".join(cont.text.replace('\n','').split())
                if strin != '':
                    paragraphs.append(strin)  # 存储正文
            if not paragraphs:
                return
            file_name = set()  # 保存文件名
            has_attch = False  # 是否具有附件
            attach_urls = bs.body.select('a[href]')
            for new_url in attach_urls:
                new_url = new_url.attrs['href']
                if '.xlsx' in new_url or '.doc' in new_url or '.pdf' in new_url:
                    has_attch = True
                    if not new_url.startswith('http'):
                        new_url = 'http://' + url.split('/')[2] + new_url
                    # print(new_url)
                    file_path = dir_path + str(new_url.split('/')[-1])[-200:]  # 限制文件长度
                    # print(file_path)
                    if file_path not in file_name:
                        if file_path not in all_files:
                            try:
                                socket.setdefaulttimeout(4)
                                print(3)
                                # urllib.request.urlopen(urllib.request.Request(url=url,headers={'User-Agent': 'IR-robot'}),timeout=3)
                                urllib.request.urlretrieve(new_url, file_path)
                            except (urllib.error.URLError, TimeoutError, socket.timeout, IsADirectoryError,ValueError,http.client.InvalidURL):
                                continue
                            else:
                                has_attch = True
                                file_name.add(file_path)  # 记录相关文件名
                                thr_lock.acquire()
                                all_files.add(file_path)
                                thr_lock.release()
                        else:
                            file_name.add(file_path)
                            has_attch = True

            # thr_lock.acquire()  # 统计 修改全局变量
            gotten_num += 1
            if has_attch:
                spec_got += 1
            glo_result.append({"url": url[:-1], "title": title, 'paragraphs':[x.strip() for x in paragraphs],'file_name':list(file_name)})
            # thr_lock.release()
            # print("totol:"+str(gotten_num))
            # print("spec:"+str(spec_got))

def write_res(json_path="output/js_out_std.json"):
    global glo_result
    # stream = [json.dumps(res, ensure_ascii=False,indent=4,separators=(',', ':')) for res in glo_result]
    stream = [json.dumps(res, ensure_ascii=False) for res in glo_result]
    with open(json_path, 'w',encoding='utf-8') as js_file:
        js_file.write('\n'.join(stream))
    return stream


def store_urls():
    urls = get_urls(root_url=r_url,wanted_num=4000)
    stream = ''
    for url in urls:
        stream += url + '\n'
    with open('urls.txt','w') as urls_f:
        urls_f.write(stream[:-1])


def test():
    with open('output/urls.txt', 'r') as urls_f:
        urls = urls_f.readlines()
    for url in urls:
        url_queue.put(url)
    print("已读取全部url")
    threads = [CrawThread() for i in range(15)]
    for thr in threads:
        thr.start()
    for thr in threads:
        thr.join()
    print("爬取完成")
    write_res()


def client(json_path):
    """
    客户端调用的执行完整网页url获取、正文内容爬取并保存json文件的方法
    :return: None
    """
    urls = get_urls(root_url=r_url, wanted_num=4000)
    for url in urls:
        url_queue.put(url)
    print("已读取全部url")
    threads = [CrawThread() for i in range(15)]
    for thr in threads:
        thr.start()
    for thr in threads:
        thr.join()
    print("爬取完成")
    write_res(json_path)


class CrawThread(threading.Thread):
    def run(self) -> None:
        while True:
            try:
                thr_lock.acquire()
                url = url_queue.get_nowait()  # 从url队列中取出一个进行网页的爬取
                if gotten_num >= wanted_num and spec_got >= spec_num:
                    thr_lock.release()
                    break
                craw_web(url)
                thr_lock.release()
            except (queue.Empty, ConnectionResetError):
                break


if __name__ == '__main__':
    test()
    # with open('output/urls.txt', 'r') as urls_f:
    #     urls = urls_f.readlines()
    # for url in urls:
    #     url_queue.put(url)
    # while True:
    #     try:
    #         # thr_lock.acquire()
    #         url = url_queue.get_nowait()  # 从url队列中取出一个进行网页的爬取
    #         if gotten_num >= wanted_num and spec_got >= spec_num:
    #             # thr_lock.release()
    #             break
    #         craw_web(url)
    #         thr
    #     except (queue.Empty, ConnectionResetError):
    #         break
    # client(json_path="output/js_out_std.json")  # 执行该方法