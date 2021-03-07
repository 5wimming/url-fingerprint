# -*- coding:utf-8 -*-
# @Date    : 2021/02/27
# @Author  : weinull, 5wimming

import urllib3
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from Wappalyzer import Wappalyzer, WebPage

import warnings

warnings.filterwarnings("ignore", message="""Caught 'unbalanced parenthesis at position 119' compiling regex""",
                        category=UserWarning)
urllib3.disable_warnings()

EXP_CHECK = False
url_account = '5wimming'
url_password = '5wimming'


def get_url_cookie():
    global cookie
    login_url = 'https://login.5wimming.com/test/login.do'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://login.5wimming.com/test/'
    }
    post_data = {
        'username': url_account,
        'password': url_password
    }
    try:
        result = requests.post(login_url, data=post_data, headers=headers, verify=False, timeout=100)
        tmp_cookie = ''

        for x in result.cookies:
            tmp_cookie += '{}={}; '.format(x.name, x.value)
        cookie = tmp_cookie
        print(cookie)
        return cookie
    except Exception as e:
        print(e)


def url_info(url, cookie, body_path):
    results = []
    results.append(url)
    request_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cookie': cookie
    }
    r = requests.get(url, headers=request_headers, timeout=30, verify=False)
    text_len = len(r.text)

    results.append(str(r.status_code))
    results.append(str(r.headers).replace('\t', ' '))
    results.append(str(text_len))
    results.append(str(len(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', r.text, re.I))))

    try:
        # ['url', 'status', 'headers', 'body length', 'body url nums', 'redirect url', 'title']
        redirect_list = r.history
        if redirect_list:
            redirect_url = redirect_list[-1].headers['Location']
            if not redirect_url.startswith('http'):
                redirect_url = url + '/' + redirect_url
        else:
            redirect_url = r.url
        results.append(redirect_url)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        origin_title = soup.title if soup.title else "none"
        results.append(
            str(urllib.parse.unquote(origin_title)).replace("\n", " ").replace("\r", " ").replace("\t", " ").replace(
                "<title>", " ").replace("</title>", " ").strip())
    except Exception as e:
        print('flag01', e)

    try:
        if text_len > 0:
            filename = url.replace('https://', '').replace('http://', '') \
                           .replace('/', '').replace(':', '_').replace('.', '_') + '.txt'
            with open(body_path + filename, 'w', encoding='utf-8') as fw:
                fw.write(r.text)
    except Exception as e:
        print(e)

    return results


def main(target, cookie, csv_columns, body_path='./output/'):
    url = target.strip().replace('https://', '')
    flag = False
    if not url.startswith('http'):
        flag = True
        url = 'http://{}'.format(url)
    result = [url]
    try:
        result = url_info(url, cookie, body_path)
    except Exception as e:
        try:
            if flag:
                url = url.replace('http://', 'https://')
                result = url_info(url, cookie, body_path)
        except Exception as e:
            print('error:', e)

    wappalyzer_result = my_wappalyzer(url, csv_columns)
    for i, value in enumerate(result):
        wappalyzer_result[i] = value

    return wappalyzer_result


def my_wappalyzer(url, csv_columns):
    wappalyzer_result = ''
    result = [''] * len(csv_columns)
    try:
        wappalyzer = Wappalyzer.latest()
        webpage = WebPage.new_from_url(url, timeout=50)
        # result01 = wappalyzer.analyze(webpage)
        # result02 = wappalyzer.analyze_with_categories(webpage)
        wappalyzer_result = wappalyzer.analyze_with_versions_and_categories(webpage)

    except Exception as e:
        print(e)
    if wappalyzer_result:
        for x in wappalyzer_result:
            categories = wappalyzer_result[x]['categories']
            versions = '&'.join(wappalyzer_result[x]['versions'])
            for categorie in categories:
                data_index = csv_columns.index(categorie)
                name = x + '-' + versions if versions else x
                if result[data_index]:
                    result[data_index] += '|' + name
                else:
                    result[data_index] = name
    return result


if __name__ == '__main__':
    wappalyzer = Wappalyzer.latest().categories
    csv_columns = ['url', 'status', 'headers', 'body length', 'body url nums', 'redirect url', 'title'] \
                  + list(map(lambda key: wappalyzer[key]['name'], wappalyzer))
    cookie = get_url_cookie()
    print(main('www.5wimming.com', cookie, csv_columns))