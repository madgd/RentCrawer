# coding=utf-8
__author__ = 'rxread'

import sqlite3
import re
import sys
import datetime

import requests
from bs4 import BeautifulSoup


class getoutofloop(Exception): pass


def isInBalckList(blacklist, toSearch):
    for item in blacklist:
        if toSearch.find(item) != -1:
            return True;
    return False


def getTimeFromStr(timeStr):
    # 13:47:32或者2015-05-12或者2015-05-12 13:47:32
    if '-' in timeStr and ':' in timeStr:
        return datetime.datetime.strptime(timeStr, "%Y-%m-%d %H:%M:%S")
    elif '-' in timeStr:
        return datetime.datetime.strptime(timeStr, "%Y-%m-%d")
    elif ':' in timeStr:
        date_today = datetime.date.today();
        date = datetime.datetime.strptime(timeStr, "%H:%M:%S")
        return date.replace(year=date_today.year, month=date_today.month, day=date_today.day)
    else:
        return datetime.date.today()



'''
May 25 ,2015
Beijing, China
'''

# set encoding
reload(sys)
sys.setdefaultencoding('utf8')
prog_info = "Rent Crawler 1.0\nBy RxRead\nhttp://blog.zanlabs.com\n"
print prog_info


#######################################
#You can modify configurations below
key_search_word = ('三元桥', '北京西站', '国贸')
custom_black_list = ('隔断', '单间','一居室')

start_time_str = '2015-03-12'
#You can modify configurations above
######################################

smth_black_list = ('黑名单', 'Re', '警告', '发布', '关于', '通知', '审核', '求助', '规定', '求租')

newsmth_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.65 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,en-GB;q=0.2,zh-TW;q=0.2',
    'Connection': 'keep-alive',
    'X-Requested-With': 'XMLHttpRequest'  #important parameter,can not ignore
}

smth_switch=True;
douban_siwtch=True;


try:
    print "Crawler is running now."
    # creat database
    conn = sqlite3.connect('rentdata.db')
    conn.text_factory=str
    cursor = conn.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS rent(id INTEGER PRIMARY KEY, title TEXT, url TEXT UNIQUE,itemtime timestamp, crawtime timestamp ,author TEXT, source TEXT,note TEXT)')
    cursor.close()
    start_time = getTimeFromStr(start_time_str)
    print "searching data after date ", start_time

    cursor = conn.cursor()
    #New SMTH
    if smth_switch:
        newsmth_main_url = 'http://www.newsmth.net'
        newsmth_regex = r'<table class="board-list tiz"(?:\s|\S)*</td></tr></table>'
        for keyword in key_search_word:
            print '>>>>>>>>>>Search newsmth %s ...' % keyword
            url = 'http://www.newsmth.net/nForum/s/article?ajax&au&b=HouseRent&t1=' + keyword
            r = requests.get(url, headers=newsmth_headers)
            if r.status_code == 200:
                #print r.text
                match = re.search(newsmth_regex, r.text)
                if match:
                    try:
                        text = match.group(0)
                        soup = BeautifulSoup(text)
                        for tr in soup.find_all('tr')[1:]:
                            title_element = tr.find_all(attrs={'class': 'title_9'})[0]
                            title_text = title_element.text

                            #exclude what in blacklist
                            if isInBalckList(custom_black_list, title_text):
                                continue
                            if isInBalckList(smth_black_list, title_text):
                                continue
                            time_text = tr.find_all(attrs={'class': 'title_10'})[0].text  #13:47:32或者2015-05-12

                            #data ahead of the specific date
                            if getTimeFromStr(time_text) < start_time:
                                continue
                            link_text = newsmth_main_url + title_element.find_all('a')[0].get('href').replace(
                                '/nForum/article/', '/nForum/#!article/')
                            author_text = tr.find_all(attrs={'class': 'title_12'})[0].find_all('a')[0].text
                            try:
                                cursor.execute(
                                    'INSERT INTO rent(id,title,url,itemtime,crawtime,author,source,note) VALUES(NULL,?,?,?,?,?,?,?)',
                                    [title_text, link_text, getTimeFromStr(time_text), datetime.datetime.now(), author_text,
                                     'newsmth', ''])
                                print 'add new data:', title_text, time_text, author_text, link_text
                                #/nForum/article/HouseRent/225839 /nForum/#!article/HouseRent/225839
                            except sqlite3.Error, e:
                                print 'data exists:',title_text,link_text,e
                                pass
                    except Exception, e:
                        print "error match table", e
                else:
                    print "no data"
            else:
                print 'request url error:' + url
    #end newsmth

    #Douban: Beijing Rent,Beijing Rent Douban
    if douban_siwtch:
        douban_url = ('http://www.douban.com/group/search?group=35417&cat=1013&q=',
                      'http://www.douban.com/group/search?group=26926&cat=1013&q=')
        douban_url_name=('Douban-北京租房','Douban-北京租房豆瓣')
        douban_url_index=0
        for url in douban_url:
            for keyword in key_search_word:
                print '>>>>>>>>>>Search %s  %s ...' % (douban_url_name[douban_url_index],keyword)
                url = url + keyword
                r = requests.get(url, headers=newsmth_headers)
                if r.status_code == 200:
                    try:
                        soup = BeautifulSoup(r.text)
                        table = soup.find_all(attrs={'class': 'olt'})[0]
                        for tr in table.find_all('tr'):
                            td = tr.find_all('td')

                            title_element=td[0].find_all('a')[0]
                            title_text = title_element.get('title')

                            #exclude what in blacklist
                            if isInBalckList(custom_black_list, title_text):
                                continue
                            if isInBalckList(smth_black_list, title_text):
                                continue
                            time_text = td[1].get('title')

                            #data ahead of the specific date
                            if getTimeFromStr(time_text) < start_time:
                                continue
                            link_text = title_element.get('href');

                            reply_count=td[2].find_all('span')[0].text
                            try:
                                cursor.execute(
                                    'INSERT INTO rent(id,title,url,itemtime,crawtime,author,source,note) VALUES(NULL,?,?,?,?,?,?,?)',
                                    [title_text, link_text, getTimeFromStr(time_text), datetime.datetime.now(), '',
                                     douban_url_name[douban_url_index], reply_count])
                                print 'add new data:',title_text, time_text, reply_count,link_text
                            except sqlite3.Error, e:
                                print 'data exists:',title_text,link_text,e
                                pass
                    except Exception, e:
                        print "error match table", e
                else:
                    print 'request url error:' + url
            douban_url_index+=1
    #end douban

    cursor.close()

    # conn.commit()
    # cursor.close()
    # export database data to txt file
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rent ORDER BY itemtime DESC ,crawtime DESC')
    values = cursor.fetchall()

    #export to html file
    file = open('result.html', 'w')
    with file:
        file.writelines('<html><head>')
        file.writelines('<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>')
        file.writelines('<title>Rent Crawer Result</title></head><body>')
        file.writelines('<table rules=all>')
        file.writelines('<h1>' + prog_info + '</h1>')
        file.writelines('<tr><td>索引Index</td><td>标题Title</td><td>链接Link</td><td>发帖时间Page Time</td><td>抓取时间Craw Time</td><td>作者Author</td><td>来源Source</td></tr>')
        for row in values:
            file.write('<tr>')
            for member in row:
                file.write('<td>')
                member = str(member)
                if 'http' in member:
                    file.write('<a href="' + member + '" target="_black">' + member + '</a>')
                else:
                    file.write(member)
                file.write('</td>')
            file.writelines('</tr>')
        file.writelines('</table>')
        file.writelines('</body></html>')
    cursor.close()

except Exception, e:
    print "Error:", e
finally:
    conn.commit()
    conn.close()
    print "Search Finish，Please open result.html to view result"