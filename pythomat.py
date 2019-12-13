#!/usr/bin python3
import configparser
import glob
import os
import subprocess
import time
from argparse import ArgumentParser

from mechanize import Browser


# Downloads a single file form url to path and names it filename
def download(url: str, createdirs: bool, overwrite: int = 1, filename: str = "", saveto: str = "", checklastmodified: bool = True):
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

            if createdirs and not os.path.exists(saveto):
                os.makedirs(saveto)

            os.chdir(saveto)
            print("Downloading {} as \"{}\" ...".format(url, filename))
            br.retrieve(url, filename)
        else:
            print("[Ignored] {} exists already".format(url))
    except Exception as ex:
        print("[Failed] {}, Error: {}".format(url, ex))


# Downloads all files with links containing pattern on path to saveto
def downloadAll(url: str, createdirs: bool, overwrite: int = 1, pattern: str = "", saveto: str = ""):
    br = Browser()
    br.open(url)
    for link in br.links(url_regex=pattern):
        if link.url.startswith("http://") or link.url.startswith("https://"):
            download(link.url, createdirs, overwrite, "", saveto)
        elif link.url.startswith("/"):
            download(link.base_url[:link.base_url.find("/", 8)] + link.url, createdirs, overwrite, "", saveto)
        else:
            download(link.base_url[:link.base_url.rfind("/") + 1] + link.url, createdirs, overwrite, "", saveto)


# Downloads YouTuve-Video with id to saveto and overwrites (or not)
def downloadYoutube(id, overwrite=True, saveto=""):
    output = "-o \"{}%(title)s-%(id)s.%(ext)s\"".format(saveto)
    if overwrite or len(glob.glob("{}*{}*".format(saveto, id))) == 0:
        url = "https://www.youtube.com/watch?v={}".format(id)
        subprocess.call("youtube-dl {} \"{}\"".format(output, url), shell=True)


# Parses .ini file and executes the given Downloads
def downloadFromIni(inipath: str, createdirs: bool):
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
            download(uri, createdirs, overwrite, name, saveto)
        elif mode == "batch":
            pattern = ini.get(section, "pattern")
            overwrite = ini.get(section, "overwrite", fallback=1)
            downloadAll(uri, createdirs, overwrite, pattern, saveto)
        elif mode == "youtube":
            overwrite = ini.get(section, "overwrite", fallback=1)
            downloadYoutube(uri, overwrite, saveto)
        elif mode == "cms" or mode == "module":
            name = "cms" if mode == "cms" else ini.get(section, "module")
            module = __import__(name, globals=globals())

            items = dict(ini.items(section))
            items["createdirs"] = createdirs
            module.start(section, items)
        else:
            print("Mode '{}' unsupported".format(mode))


def main():
    parser = ArgumentParser()
    parser.add_argument("inipath", nargs="?")
    parser.add_argument("--createdirs", help="Automatically create directories", action="store_true")
    args = parser.parse_args()

    downloadFromIni(args.inipath if args.inipath else "pythomat.ini", args.createdirs)


if __name__ == "__main__":
    main()
