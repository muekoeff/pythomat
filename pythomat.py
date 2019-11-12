#!/usr/bin python3
import configparser
import glob
import os
import subprocess
import sys
import time

from mechanize import Browser


# Downloads a single file form url to path and names it filename
def download(url: str, filename: str = "", saveto: str = "", overwrite: int = 1, checklastmodified: bool = True):
    try:
        if filename == "":
            filename = url.split("/")[-1]
            filename = filename.split("?")[0]
        if not saveto.endswith("/"):
            saveto = saveto + "/"

        if overwrite == 1 and os.path.isfile(saveto + filename) and checklastmodified:
            br = Browser()
            br.set_handle_robots(False)
            br.open(url)
            remote_time = time.strptime(br.response().info()["last-modified"], "%a, %d %b %Y %H:%M:%S GMT")
            local_time = time.gmtime(os.stat(saveto + filename).st_mtime)
            do_download = (remote_time > local_time)
        elif overwrite == 0 and os.path.isfile(saveto + filename):
            do_download = False
        else:
            do_download = True

        if do_download:
            br = Browser()
            br.set_handle_robots(False)
            os.chdir(saveto)
            br.retrieve(url, saveto + filename)
            print("Downloaded {} succesfully".format(url))
        else:
            print("[Ignored] {} exists already".format(url))
    except Exception as ex:
        print("[Failed] {}, Error: {}".format(url, ex))


# Downloads all files with links containing pattern on path to saveto
def downloadAll(url: str, pattern: str = "", saveto: str = "", overwrite: int = 1):
    br = Browser()
    br.open(url)
    for link in br.links(url_regex=pattern):
        if link.url.startswith("http://") or link.url.startswith("https://"):
            download(link.url, "", saveto, overwrite)
            download(link.url, "", saveto, overwrite)
        elif link.url.startswith("/"):
            download(link.base_url[:link.base_url.find("/", 8)] + link.url, "", saveto, overwrite)
        else:
            download(link.base_url[:link.base_url.rfind("/") + 1] + link.url, "", saveto, overwrite)


# Downloads YouTuve-Video with id to saveto and overwrites (or not)
def downloadYoutube(id, saveto="", overwrite=True):
    output = "-o \"{}%(title)s-%(id)s.%(ext)s\"".format(saveto)
    if overwrite or len(glob.glob("{}*{}*".format(saveto, id))) == 0:
        url = "https://www.youtube.com/watch?v={}".format(id)
        subprocess.call("youtube-dl {} \"{}\"".format(output, url), shell=True)


# Parses .ini file and executes the given Downloads
def downloadFromIni(inipath: str = "pythomat.ini"):
    ini = configparser.ConfigParser()
    ini.read(inipath)
    for section in ini.sections():
        print("### Processing {} ###".format(section))

        uri = ini.get(section, "uri")
        saveto = ini.get(section, "saveto")
        mode = ini.get(section, "mode")
        if mode == "single":
            name = ini.get(section, "filename", fallback="")
            overwrite = ini.get(section, "overwrite", fallback=1)
            download(uri, name, saveto, overwrite)
        elif mode == "batch":
            pattern = ini.get(section, "pattern")
            overwrite = ini.get(section, "overwrite", fallback=1)
            downloadAll(uri, pattern, saveto, overwrite)
        elif mode == "youtube":
            overwrite = ini.get(section, "overwrite", fallback=1)
            downloadYoutube(uri, saveto, overwrite)
        elif mode == "cms":
            module = __import__("cms", globals=globals())
            module.start(section, ini.items(section))
        elif mode == "module":
            name = ini.get(section, "module")
            module = __import__(name, globals=globals())
            module.start(section, ini.items(section))
        else:
            print("Mode '{}' unsupported".format(mode))


# Main
for arg in sys.argv[1:]:
    if not arg.endswith(".ini"):
        arg += ".ini"
    downloadFromIni(arg)
if len(sys.argv[1:]) < 1:
    downloadFromIni()
