#!/usr/bin python3
import configparser
import glob
import os
import pathlib
import subprocess
import sys
import time
import traceback
from argparse import ArgumentParser
from datetime import datetime
from typing import List, Tuple, TextIO

from mechanize import Browser


# noinspection PyPep8Naming
class Pythomat:
    downloaded: List[Tuple[str, str]] = []
    errors: List[Tuple[str, str]] = []
    failed: List[Tuple[str, str]] = []
    logFile: TextIO = None

    @staticmethod
    def getConfigFromIni(inipath: str):
        ini = configparser.ConfigParser()
        ini.read(inipath)
        return ini

    @staticmethod
    def get_browser(url: str, httpUsername: str, httpPassword: str):
        br = Browser()
        br.addheaders = [
            ('User-agent', 'Pythomat')
        ]
        if httpUsername is not None and httpPassword is not None:
            br.set_handle_robots(False)
            br.add_password(url, httpUsername, httpPassword)

        return br

    def alreadyDownloaded(self, root: str, filename: str, recursive: bool) -> bool:
        if recursive:
            for dir, sub_dirs, files in os.walk(root):
                if filename in files:
                    return True

            return False
        else:
            return os.path.isfile(os.path.join(root, filename))

    def closeLog(self):
        if self.logFile is not None:
            self.logFile.close()

    # Downloads a single file form url to path and names it filename
    def download(self, section: str, url: str, createdirs: bool, overwrite: int, filename: str = "", saveto: str = "", detect: str = "", detect_recursive: bool = False,
                 checklastmodified: bool = True, httpUsername: str = None, httpPassword: str = None, logMessage: str = None) -> bool:
        uptodate: bool = False

        try:
            if filename == "":
                filename = url.split("/")[-1]
                filename = filename.split("?")[0]
            if not saveto.endswith("/"):
                saveto = saveto + "/"

            if overwrite == 1 and self.alreadyDownloaded(detect, filename, detect_recursive) and checklastmodified:
                br = self.get_browser(url, httpUsername, httpPassword)

                br.open(url)
                remote_time = time.strptime(br.response().info()["last-modified"], "%a, %d %b %Y %H:%M:%S GMT")
                local_time = time.gmtime(os.stat(os.path.join(saveto, filename)).st_mtime)
                do_download = (remote_time > local_time)
                uptodate = True
            elif overwrite == 0 and os.path.isfile(os.path.join(saveto, filename)):
                do_download = False
            else:
                do_download = True

            if do_download:
                br = self.get_browser(url, httpUsername, httpPassword)

                if createdirs and not os.path.exists(saveto):
                    os.makedirs(saveto)

                os.chdir(saveto)
                print(f"Downloading {url} as \"{filename}\" …")
                br.retrieve(url, filename)
                self.reportFinished(section, filename)
                self.reportLog(section, filename, logMessage)
                return True
            else:
                if uptodate:
                    print(f"[Ignored] Up-to-date: {url}")
                else:
                    print(f"[Ignored] Already downloaded: {url}")
        except Exception as ex:
            print(f"[Failed] {url}, Error: {ex}", file=sys.stderr)
            self.reportFailed(section, filename)

        return False

    # Downloads all files with links containing pattern on path to saveto
    def downloadAll(self, section: str, url: str, createdirs: bool, overwrite: int, pattern: str, saveto: str, detect: str, detect_recursive: bool, httpUsername: str, httpPassword: str):
        br = self.get_browser(url, httpUsername, httpPassword)
        br.open(url)
        for link in br.links(url_regex=pattern):
            if link.url.startswith("http://") or link.url.startswith("https://"):
                self.download(section, link.url, createdirs, overwrite, saveto=saveto, detect=detect, detect_recursive=detect_recursive, httpUsername=httpUsername, httpPassword=httpPassword)
            elif link.url.startswith("/"):
                self.download(section, link.base_url[:link.base_url.find("/", 8)] + link.url, createdirs, overwrite, saveto=saveto, detect=detect, detect_recursive=detect_recursive, httpUsername=httpUsername, httpPassword=httpPassword)
            else:
                self.download(section, link.base_url[:link.base_url.rfind("/") + 1] + link.url, createdirs, overwrite, saveto=saveto, detect=detect, detect_recursive=detect_recursive, httpUsername=httpUsername, httpPassword=httpPassword)

    # Downloads YouTuve-Video with id to saveto and overwrites (or not)
    def downloadYoutube(self, section: str, id: str, overwrite=True, saveto=""):
        output = f"-o \"{saveto}%(title)s-%(id)s.%(ext)s\""
        if overwrite or len(glob.glob(f"{saveto}*{id}*")) == 0:
            url = f"https://www.youtube.com/watch?v={id}"
            subprocess.call(f"youtube-dl {output} \"{url}\"", shell=True)
            self.reportFinished(section, id)

    # Parses .ini file and executes the given Downloads
    def downloadFromIni(self, ini: configparser.ConfigParser, createdirs: bool, rules: str):
        workingdir: str = str(pathlib.Path().absolute())
        ruleList: List[str] = None if rules is None else rules.split(",")

        for section in ini.sections():
            os.chdir(workingdir)  # Reset working dir in case it has been changed

            if ruleList is not None and section not in ruleList and rules != "all":
                print(f"### Skipping {section} ###")
                continue

            skip = int(ini.get(section, "skip", fallback=0))
            if ruleList is None and skip == 1:
                print(f"### Skipping {section} - must be started manually ###")
                continue

            print(f"### Processing {section} ###")

            uri = ini.get(section, "uri")
            saveto = ini.get(section, "saveto")
            detect = ini.get(section, "detect", fallback=saveto)
            detect_recursive = ini.get(section, "detect_recursive", fallback=False)
            mode = ini.get(section, "mode")
            httpUsername = ini.get(section, "username", fallback=None)
            httpPassword = ini.get(section, "password", fallback=None)

            if mode == "batch":
                pattern = ini.get(section, "pattern")
                overwrite = ini.get(section, "overwrite", fallback=1)
                try:
                    self.downloadAll(section, uri, createdirs, overwrite, pattern, saveto, detect, detect_recursive, httpUsername, httpPassword)
                except Exception as e:
                    print("An error occured", file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)
                    self.reportError(section, str(e))
            elif mode == "cms" or mode == "moodle":
                name = mode
                module = __import__(name, globals=globals())

                items = dict(ini.items(section))
                items["createdirs"] = createdirs
                try:
                    module.start(section, items, self)
                except Exception as e:
                    print("An error occured", file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)
                    self.reportError(section, str(e))
            elif mode == "module":
                name = "cms" if mode == "cms" else ini.get(section, "module")
                module = __import__(name, globals=globals())

                items = dict(ini.items(section))
                items["createdirs"] = createdirs
                try:
                    module.start(section, items, self)
                except Exception as e:
                    print("An error occured", file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)
                    self.reportError(section, str(e))
            elif mode == "single":
                name = ini.get(section, "filename", fallback="")
                overwrite = ini.get(section, "overwrite", fallback=1)
                try:
                    self.download(section, uri, createdirs, overwrite, name, saveto, detect, detect_recursive, httpUsername=httpUsername, httpPassword=httpPassword)
                except Exception as e:
                    print("An error occured", file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)
                    self.reportError(section, str(e))
            elif mode == "youtube":
                overwrite = int(ini.get(section, "overwrite", fallback=1))
                try:
                    self.downloadYoutube(section, uri, overwrite, saveto)
                except Exception as e:
                    print("An error occured", file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)
                    self.reportError(section, str(e))
            else:
                print(f"Mode '{mode}' unsupported", file=sys.stderr)

    def openLog(self, path: str):
        if path is not None:
            self.logFile = open(path, 'a')

    def printReport(self):
        print("### Report ###")
        if len(self.errors) != 0:
            print("Errors:")
            for error in self.errors:
                print(f"• {error[0]} | {error[1]}")

        if len(self.failed) != 0:
            print("Failed:")
            for failed in self.failed:
                print(f"• {failed[0]} | {failed[1]}")

        if len(self.downloaded) == 0:
            print("Downloaded: nothing")
        else:
            print("Downloaded:")
            for downloaded in self.downloaded:
                print(f"• {downloaded[0]} | {downloaded[1]}")

    def reportError(self, section: str, msg: str):
        self.errors.append((section, msg))

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
