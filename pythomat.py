#!/usr/bin python3
import configparser
import glob
import os
import subprocess
import sys
import time

from mechanize import Browser


# Downloads a single file form url to path and names it filename
def download(url, filename="", saveto="", overwrite=2, suffix=""):
    try:
        if filename == "":
            filename = url.split("/")[-1]
            filename = filename.split("?")[0]
        do_download = True
        if not saveto.endswith("/"):
            saveto = saveto + "/"
        if overwrite == 2 and os.path.isfile(saveto + filename):
            br = Browser()
            br.open(url)
            remote_time = time.strptime(br.response().info()["last-modified"], "%a, %d %b %Y %H:%M:%S GMT")
            local_time = time.gmtime(os.stat(saveto + filename + suffix).st_mtime)
            do_download = (remote_time > local_time)
        elif overwrite == 0 and os.path.isfile(saveto + filename):
            do_download = False

        if do_download:
            br = Browser()
            os.chdir(saveto)
            br.retrieve(url, filename + suffix)
            print("Downloaded " + url + " succesfully")
        else:
            print(url + " exists already")
    except:
        print("Failed: " + url)


# Downloads all given urls via download(...)
def batchDownload(urls, overw=2):
    for url in urls:
        download(url, overwrite=overw)


# Downloads all files with links containing pattern on path to destpath
def downloadAll(url, pattern="", saveto="", overwrite=2, suffix=""):
    br = Browser()
    br.open(url)
    for link in br.links(url_regex=pattern):
        if link.url.startswith("http://"):
            download(link.url, "", saveto, overwrite, suffix)
        elif link.url.startswith("/"):
            download(link.base_url[:link.base_url.find("/", 8)] + link.url, "", saveto, overwrite, suffix)
        else:
            download(link.base_url[:link.base_url.rfind("/") + 1] + link.url, "", saveto, overwrite, suffix)


# Downloads YouTuve-Video with id to saveto and overwrites (or not)
def downloadYoutube(id, saveto="", overwrite=True):
    output = "-o \"" + saveto + "%(title)s-%(id)s.%(ext)s\""
    if overwrite or len(glob.glob(saveto + "*" + id + "*")) == 0:
        url = "http://www.youtube.com/watch?v=" + id
        subprocess.call("youtube-dl " + output + " \"" + url + " \"", shell=True)


# Parses .ini file and executes the given Downloads
def downloadFromIni(inipath="pythomat.ini"):
    ini = configparser.ConfigParser()
    ini.read(inipath)
    for section in ini.sections():
        uri = ini.get(section, "uri")
        saveto = ini.get(section, "saveto")
        overwrite = ini.get(section, "overwrite", fallback=2)
        mode = ini.get(section, "mode")
        if mode == "single":
            name = ini.get(section, "filename", fallback="")
            download(uri, name, saveto, overwrite)
        elif mode == "batch":
            pattern = ini.get(section, "pattern")
            suff = ini.get(section, "suffix", fallback="")
            downloadAll(uri, pattern, saveto, overwrite, suffix=suff)
        elif mode == "youtube":
            downloadYoutube(uri, saveto, not overwrite == 1)
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
