# from https://github.com/rnbguy/subscene-dl

import pprint
import requests
import bs4
import zipfile
import io
import os
import sys
import re

from ntpath import basename
from utils import mkdir

server_addr = "https://subscene.com"

def search_keywords(filename):
    filename = os.path.splitext(basename(filename))[0]
    l = ["720p", "1080p", "hdtv", "web-*dl", "x264", "x265", "hevc", "2ch"]
    k = re.search("(^.*?)((?:"+"|".join(l)+").*)", filename)
    n = k.group(1)
    # a = k.group(2)
    # if re.search("s\d\de\d\d", n, flags=re.IGNORECASE):
    #     print("tv series")
    # else:
    #     print("movies")
    n = n.lower().replace(".", " ").split()
    return n

def search_with_filename(video_filename, language):
    lang = language.lower()
    q = search_keywords(re.sub(r":|'|&", "", video_filename))
    print("keyword: {}".format(" ".join(q)))
    query = {"q": " ".join(q), "r": True}
    path = "/subtitles/release"
    r = requests.get(server_addr + path, params=query)
    soup = bs4.BeautifulSoup(r.content, "lxml")
    results = soup.select(".box > .content tr")[1:]
    for e in results:
        sub_url = e.find("a")["href"]
        if lang in sub_url:
            nr = requests.get(server_addr + sub_url)
            sub_soup = bs4.BeautifulSoup(nr.content, "lxml")
            download_link = sub_soup.find("div", class_="download").find("a", class_="button")["href"]
            
            download_link = server_addr + download_link
            print('subtitle link:', sub_url)

            r = requests.get(download_link)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                for infofile in z.infolist()[:1]:
                    z.extract(infofile)
                    sub_ext = os.path.splitext(infofile.filename)[1]
                    vid_name = os.path.splitext(video_filename)[0]
                    print(infofile.filename, vid_name+sub_ext)
                    
                    out_dir = "temp/"

                    mkdir(out_dir)

                    out_path = out_dir + basename(vid_name) + sub_ext
                    
                    os.rename(infofile.filename, out_path)

                    common_encodings = ['utf-8', 'utf-16', 'cp1252']

                    for encoding in common_encodings:
                        try:
                            srt_file = codecs.open(srt_path, 'r', encoding=encoding)
                            srt_string = srt_file.read()
                            srt_file.close()

                            subs = list(srt.parse(srt_string))

                            return out_path, encoding
                        except:
                            pass

    sys.exit("no subs found")

                        



