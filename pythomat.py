#!/usr/bin python3
import configparser
import glob
import os
import pathlib
import subprocess
import time
from argparse import ArgumentParser
from datetime import datetime
from typing import List, Tuple, TextIO

from mechanize import Browser


# noinspection PyPep8Naming
class Pythomat:
    downloaded: List[Tuple[str, str]] = []
    failed: List[Tuple[str, str]] = []
    logFile: TextIO = None

    @staticmethod
    def getConfigFromIni(inipath: str):
        ini = configparser.ConfigParser()
        ini.read(inipath)
        return ini

    @staticmethod
    def setupBrowser(br: Browser, url: str, httpUsername: str, httpPassword: str):
        if httpUsername is not None and httpPassword is not None:
            br.set_handle_robots(False)
            br.add_password(url, httpUsername, httpPassword)

    def closeLog(self):
        if self.logFile is not None:
            self.logFile.close()

    # Downloads a single file form url to path and names it filename
    def download(self, section: str, url: str, createdirs: bool, overwrite: int = 1, filename: str = "", saveto: str = "",
                 checklastmodified: bool = True, httpUsername: str = None, httpPassword: str = None, logMessage: str = None) -> bool:
        uptodate: bool = False

        try:
            if filename == "":
                filename = url.split("/")[-1]
                filename = filename.split("?")[0]
            if not saveto.endswith("/"):
                saveto = saveto + "/"

            if overwrite == 1 and os.path.isfile(saveto + filename) and checklastmodified:
                br = Browser()
                self.setupBrowser(br, url, httpUsername, httpPassword)

                br.open(url)
                remote_time = time.strptime(br.response().info()["last-modified"], "%a, %d %b %Y %H:%M:%S GMT")
                local_time = time.gmtime(os.stat(saveto + filename).st_mtime)
                do_download = (remote_time > local_time)
                uptodate = True
            elif overwrite == 0 and os.path.isfile(saveto + filename):
                do_download = False
            else:
                do_download = True

            if do_download:
                br = Browser()
                self.setupBrowser(br, url, httpUsername, httpPassword)

                if createdirs and not os.path.exists(saveto):
                    os.makedirs(saveto)

                os.chdir(saveto)
                print("Downloading {} as \"{}\" ...".format(url, filename))
                br.retrieve(url, filename)
                self.reportFinished(section, filename)
                self.reportLog(section, filename, logMessage)
                return True
            else:
                if uptodate:
                    print("[Ignored] {} is already up to date".format(url))
                else:
                    print("[Ignored] {} exists already".format(url))
        except Exception as ex:
            print("[Failed] {}, Error: {}".format(url, ex))
            self.reportFailed(section, filename)

        return False

    # Downloads all files with links containing pattern on path to saveto
    def downloadAll(self, section: str, url: str, createdirs: bool, overwrite: int = 1, pattern: str = "", saveto: str = "", httpUsername: str = None, httpPassword: str = None):
        br = Browser()
        self.setupBrowser(br, url, httpUsername, httpPassword)

        br.open(url)
        for link in br.links(url_regex=pattern):
            if link.url.startswith("http://") or link.url.startswith("https://"):
                self.download(section, link.url, createdirs, overwrite, saveto=saveto, httpUsername=httpUsername, httpPassword=httpPassword)
            elif link.url.startswith("/"):
                self.download(section, link.base_url[:link.base_url.find("/", 8)] + link.url, createdirs, overwrite, saveto=saveto, httpUsername=httpUsername, httpPassword=httpPassword)
            else:
                self.download(section, link.base_url[:link.base_url.rfind("/") + 1] + link.url, createdirs, overwrite, saveto=saveto, httpUsername=httpUsername, httpPassword=httpPassword)

    # Downloads YouTuve-Video with id to saveto and overwrites (or not)
    def downloadYoutube(self, section: str, id: str, overwrite=True, saveto=""):
        output = "-o \"{}%(title)s-%(id)s.%(ext)s\"".format(saveto)
        if overwrite or len(glob.glob("{}*{}*".format(saveto, id))) == 0:
            url = "https://www.youtube.com/watch?v={}".format(id)
            subprocess.call("youtube-dl {} \"{}\"".format(output, url), shell=True)
            self.reportFinished(section, id)

    # Parses .ini file and executes the given Downloads
    def downloadFromIni(self, ini: configparser.ConfigParser, createdirs: bool, rules: str):
        workingdir: str = pathlib.Path().absolute()
        ruleList: List[str] = None if rules is None else rules.split(",")

        for section in ini.sections():
            os.chdir(workingdir)  # Reset working dir in case it has been changed

            if ruleList is not None and section not in ruleList and rules != "all":
                print("### Skipping {} ###".format(section))
                continue

            skip = int(ini.get(section, "skip", fallback=0))
            if ruleList is None and skip == 1:
                print("### Skipping {} - must be started manually ###".format(section))
                continue

            print("### Processing {} ###".format(section))

            uri = ini.get(section, "uri")
            saveto = ini.get(section, "saveto")
            mode = ini.get(section, "mode")
            httpUsername = ini.get(section, "username", fallback=None)
            httpPassword = ini.get(section, "password", fallback=None)

            if mode == "batch":
                pattern = ini.get(section, "pattern")
                overwrite = ini.get(section, "overwrite", fallback=1)
                self.downloadAll(section, uri, createdirs, overwrite, pattern, saveto, httpUsername=httpUsername, httpPassword=httpPassword)
            elif mode == "cms" or mode == "moodle":
                name = mode
                module = __import__(name, globals=globals())

                items = dict(ini.items(section))
                items["createdirs"] = createdirs
                module.start(section, items, self)
            elif mode == "module":
                name = "cms" if mode == "cms" else ini.get(section, "module")
                module = __import__(name, globals=globals())

                items = dict(ini.items(section))
                items["createdirs"] = createdirs
                module.start(section, items, self)
            elif mode == "single":
                name = ini.get(section, "filename", fallback="")
                overwrite = ini.get(section, "overwrite", fallback=1)
                self.download(section, uri, createdirs, overwrite, name, saveto, httpUsername=httpUsername, httpPassword=httpPassword)
            elif mode == "youtube":
                overwrite = int(ini.get(section, "overwrite", fallback=1))
                self.downloadYoutube(section, uri, overwrite, saveto)
            else:
                print("Mode '{}' unsupported".format(mode))

    def openLog(self, path: str):
        if path is not None:
            self.logFile = open(path, 'a')

    def printReport(self):
        print("### Report ###")
        if len(self.failed) != 0:
            print("Failed:")
            for failed in self.failed:
                print("{} | {}".format(failed[0], failed[1]))

        if len(self.downloaded) == 0:
            print("Downloaded: nothing")
        else:
            print("Downloaded:")
            for downloaded in self.downloaded:
                print("{} | {}".format(downloaded[0], downloaded[1]))

    def reportFailed(self, section: str, filename: str):
        self.failed.append((section, filename))

    def reportFinished(self, section: str, filename: str):
        self.downloaded.append((section, filename))

    def reportLog(self, section: str, filename: str, message: str = None):
        if self.logFile is not None:
            self.logFile.write("{} [{}] {}: {}\n".format(datetime.now().isoformat(), section, filename, "Downloaded" if message is None else message))


def main():
    parser = ArgumentParser()
    parser.add_argument("inipath", nargs="?")
    parser.add_argument("--createdirs", action="store_true", help="Automatically create directories")
    parser.add_argument("-l", "--list", action="store_true", help="Display a list of all user-defined rules")
    parser.add_argument("--log", action="store", help="Logs history of downloads to specified path")
    parser.add_argument("-r", "--rules", help="List of rules to run seperated by commas")
    parser.add_argument("--version", action='version', version='%(prog)s 2.0 | https://github.com/muekoeff/pythomat')
    args = parser.parse_args()

    ini = Pythomat.getConfigFromIni(args.inipath if args.inipath else "pythomat.ini")
    if args.list:
        print(",".join(ini.sections()))
    else:
        pythomat = Pythomat()
        pythomat.openLog(args.log)
        pythomat.downloadFromIni(ini, args.createdirs, args.rules)
        pythomat.printReport()
        pythomat.closeLog()


if __name__ == "__main__":
    main()
