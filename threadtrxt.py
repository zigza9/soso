import requests
from lxml import etree
from queue import Queue
import threading
import json


crawl_list, parse_list = [], []


class CrawlThread(threading.Thread):
    def __init__(self, name, page_queue, data_queue):
        super().__init__()
        self.name = name
        self.page_queue = page_queue
        self.data_queue = data_queue
        self.url = 'http://www.yikexun.cn/lizhi/qianming/list_50_{}.html'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                          '70.0.3538.110 Safari/537.36'
        }

    def run(self):
        print('%s线程启动' % self.name)
        while True:
            if self.page_queue.empty():
                break
            page = self.page_queue.get()
            url = self.url.format(page)
            r = requests.get(url, headers=self.headers).content.decode('utf8')
            self.data_queue.put(r)


class ParseThread(threading.Thread):
    def __init__(self, name, data_queue, f, lock):
        super().__init__()
        self.name = name
        self.data_queue = data_queue
        self.f = f
        self.lock = lock

    def run(self):
        data = self.data_queue.get()
        self.parse_content(data)

    def parse_content(self, data):
        tree = etree.HTML(data)
        div_list = tree.xpath('//div[@class="art-t"]')
        items = []
        for i in div_list:
            title = i.xpath('.//h3/a/text()|//div[@class="art-t"]/h3/a/b/text()')
            text = i.xpath('./p/text()')
            item = {
                'title': title,
                'text': text,
            }
            items.append(item)
            
        self.lock.acquire()
        self.f.write(json.dumps(items,ensure_ascii=False))
        self.lock.release()


def create_queue():
    # 创建队列对象
    page_queue = Queue()
    for page in range(1, 5):
        page_queue.put(page)
    # 创建data队列
    data_queue = Queue()
    
    return page_queue, data_queue


def create_crawl_thread(page_queue, data_queue):
    craw_name = ['采集线程1', '采集线程2', '采集线程3', ]
    # 以craw_name创建3个线程
    for name in craw_name:
        tcraw = CrawlThread(name, page_queue, data_queue)
        crawl_list.append(tcraw)


def create_parse_thread(data_queue, f, lock):
    parse_name = ['解析线程1', '解析线程2', '解析线程3', ]
    # 以parse_name创建3个线程
    for name in parse_name:
        tparse = ParseThread(name, data_queue, f, lock)
        parse_list.append(tparse)


def main():
    # 创建page队列,data队列
    page_queue, data_queue = create_queue()
    
    f = open('text.json', 'w', encoding='utf8')
    lock = threading.Lock()
    
    create_crawl_thread(page_queue, data_queue)
    create_parse_thread(data_queue, f, lock)
    
    for tcrawl in crawl_list:
        tcrawl.start()
    for tparse in parse_list:
        tparse.start()
    for tcrawl in crawl_list:
        tcrawl.join()
    for tparse in parse_list:
        tparse.join()
    f.close()
    print('主线程结束')


if __name__ == '__main__':
    main()
