#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @Date    : 2021/2/27
# @Author  : weinull, 5wimming

import os
import time
import queue
import logging
import requests
import threading
import pandas as pd
import datetime
import csv
from Wappalyzer import Wappalyzer


# 引入需调用的脚本
import task


# log配置
log_format = '[%(asctime)s]-[%(levelname)s] - %(message)s'
time_format = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=time_format,
    filename=time.strftime('task.log'),
    filemode='a'
)
# 配置log输出到console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(log_format, time_format))
logging.getLogger('').addHandler(console)

# 线程锁
thread_mutex = threading.Lock()
# 线程数
thread_max = 5
# 数据文件
input_file = 'input_url.txt'
# 登录账号密码
url_account = '5wimming'
url_password = '5wimmning'
# 自动刷新登录Cookie次数
auto_refresh_cookie = 5000
body_save_path = './output/'

wappalyzer = Wappalyzer.latest().categories
csv_columns = ['url', 'status', 'headers', 'body length', 'body url nums', 'redirect url', 'title'] \
              + list(map(lambda key: wappalyzer[key]['name'], wappalyzer))


def get_url_cookie():
    global cookie
    cookie = 'RememberMe=5wimming;'
    return cookie


def output_mkdir(path):
    path = path.strip()
    if not os.path.exists(path):
        os.makedirs(path)


def thread_process_func(task_queue, result_queue):
    global cookie
    output_mkdir(body_save_path)
    while True:
        try:
            try:
                target = task_queue.get_nowait()
            except queue.Empty:
                logging.info('{} Task done'.format(threading.current_thread().name))
                result_queue.put_nowait('Task done')
                break
            logging.info('[{}] - {}'.format(task_queue.qsize(), target))
            # 调用任务处理函数并取处理结果到result_queue
            result = task.main(target, cookie, csv_columns)
            result_queue.put_nowait(result)
        except Exception as e:
            logging.error('{} - {}'.format(threading.current_thread().name, e))


def save_csv(result):
    result = list(map(list, zip(*result)))
    columns = ['url', 'headers', 'body length', 'body url nums', 'redirect url', 'title']
    db = pd.DataFrame([], columns=columns)
    for i, value in enumerate(result):
        db[columns[i]] = value
    db.to_csv('urlInfo_' + datetime.datetime.now().strftime('%Y%m%d%H%M') + '.csv', na_rep='NA', index=0)


def thread_result_func(result_queue, output_file):

    thread_done_total = 0
    result_total = 0
    try:
        fw = open(output_file, 'w', encoding='utf-8', newline="")
        # with open(output_file, 'w', encoding='UTF-8') as fw:
        csv_writer = csv.writer(fw)
        csv_writer.writerow(csv_columns)
        while True:
            try:
                result = result_queue.get()
                result_total += 1
                if not result_total % auto_refresh_cookie:
                    get_url_cookie()
                if result == 'Task done':
                    thread_done_total += 1
                    if thread_done_total == thread_max:
                        break
                    else:
                        continue
                csv_writer.writerow(result)
            except Exception as e:
                logging.error('{} - {}'.format(threading.current_thread().name, e))
    except Exception as e:
        logging.error('{} - {}'.format(threading.current_thread().name, e))
    finally:
        fw.close()


def main():
    logging.info('-' * 50)
    if not os.path.exists(input_file):
        logging.error('Not found input file: {}'.format(input_file))
        logging.info('-' * 50)
        exit(0)

    logging.info('Read data')
    with open(input_file, encoding='UTF-8') as fr:
        input_data = fr.readlines()

    logging.info('Create queue')
    task_queue = queue.Queue()
    for data in input_data:
        task_queue.put_nowait(data.strip())

    result_queue = queue.Queue()
    thread_list = list()

    # 获取登录Cookie
    get_url_cookie()

    # 任务处理线程
    logging.info('Create thread')
    for x in range(thread_max):
        thread = threading.Thread(target=thread_process_func, args=(task_queue, result_queue))
        thread.start()
        thread_list.append(thread)
    # 结果输出线程
    output_file = time.strftime('result_data_%Y%m%d%H%M%S.csv')
    result_thread = threading.Thread(target=thread_result_func, args=(result_queue, output_file), name='Result Thread')
    result_thread.start()
    for thread in thread_list:
        thread.join()
    result_thread.join()

    logging.info('All Task Done')
    logging.info('Output output: {}'.format(output_file))
    logging.info('-' * 50)
    exit(0)


if __name__ == '__main__':
    main()
    # start_time = '2020-03-24 20:00'
    # logging.info('Start time: {}'.format(start_time))
    # while True:
    #     if time.strftime('%Y-%m-%d %H:%M') == start_time:
    #         main()
    #         break
    #     time.sleep(1)
