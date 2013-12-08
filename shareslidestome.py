#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import sys
from bs4 import BeautifulSoup
import re
import os
import time, sys


# update_progress() : Displays or updates a console progress bar
## Accepts a float between 0 and 1. Any int will be converted to a float.
## A value under 0 represents a 'halt'.
## A value at 1 or bigger represents 100%
def update_progress(progress):
    bar_length = 20 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(bar_length*progress))
    text = "\rPercent: [{0}] {1}% {2}".format("#"*block + "-"*(bar_length-block), int(progress*100), status)
    sys.stdout.write(text)
    sys.stdout.flush()

def ungzip(souce_code):
    from StringIO import StringIO
    import gzip
    zippedbuffer = StringIO(souce_code)
    unzipped_buffer = gzip.GzipFile(fileobj=zippedbuffer)
    return unzipped_buffer.read()

def undeflate(souce_code):
    import zlib
    return zlib.decompress(souce_code, -zlib.MAX_WBITS)

def get_response(url):
    response = urllib2.urlopen(url)
    data = response.read()
    if response.info().get('Content-Encoding') == 'gzip':
        data = ungzip(data)
    elif response.info().get('Content-Encoding') == 'deflate':
        data = undeflate(data)
    response.data = data
    return response

def get_title(html_source):
    return BeautifulSoup(html_source).title.getText()

def get_html(url, encoding=None):
    content = get_response(url).data
    if encoding:
        content = content.decode(encoding)
    return content

def url_save(url, filepath, refer=None):
    headers = {}
    if refer:
        headers['Referer'] = refer
    request = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(request)
    with open(filepath, 'wb') as output:
        received = 0
        while True:
            content_buffer = response.read(1024*256)
            if not content_buffer:
                break
            received += len(content_buffer)
            output.write(content_buffer)

def get_links(html_source):
    parsed_html = BeautifulSoup(html_source)
    links = {}
    for i in parsed_html.findAll('div', {'data-index': re.compile('\d'), 
                                        'class': re.compile('^slide[\W|\w]*')}):
        page_number = i.attrs['data-index']
        page_link = i.findChild().attrs['data-full']
        links[page_number] = page_link
    return links

def download_pages(links, page_title):
    keys = [int(i) for i in links.keys()]
    actions_count = len(keys) + 2
    keys.sort()
    for i in keys:
        url_save(links[str(i)], '%s.%04d.jpg' % (page_title, i))
        update_progress(i * 1.0 / actions_count)
    os.popen('convert "%s.*.jpg" "%s.pdf"' % (page_title, page_title))
    update_progress(i+1 * 100.0 / actions_count)
    for i in keys:
        os.remove('%s.%04d.jpg' % (page_title, i))
    update_progress(100)


if __name__ == '__main__':
    # if you hit the GFW, uncomment this and set to your proxy ===========
    # proxy_info = { 'host' : '127.0.0.1',
    #                'port' : 32123
    #              }
    # # proxy_support = urllib2.ProxyHandler({"http" : "http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info})
    # proxy_support = urllib2.ProxyHandler({"http" : "http://%(host)s:%(port)d" % proxy_info})
    # opener = urllib2.build_opener(proxy_support)
    # urllib2.install_opener(opener)
    # ================================================

    PAGE = get_html(sys.argv[1])
    download_pages(get_links(PAGE), get_title(PAGE))
