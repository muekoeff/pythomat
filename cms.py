import getpass
import http.client
import os
import sys
import urllib
from urllib.parse import urljoin

import keyring
from bs4 import BeautifulSoup
from mechanize import Browser

from pythomat import Pythomat

http.client._MAXHEADERS = 10000


def start(section: str, items: dict, pythomat: Pythomat):
    saveto = items["saveto"]
    detect = items["password"] if "detect" in items else items["saveto"]
    detect_recursive = items["detect_recursive"] if "detect_recursive" in items else False
    uri = items["uri"]
    uri = uri + ("/" if not uri.endswith("/") else "")
    uri_materials = uri + "materials"
    uri_login = uri + "users/login"
    username = items["username"]
    password = items["password"] if "password" in items else None
    keyring_id = items["keyring_id"] if "keyring_id" in items else None
    fileext_whitelist = items["fileext_whitelist"] if "fileext_whitelist" in items else None
    fileext_blacklist = items["fileext_blacklist"] if "fileext_blacklist" in items else None
    overwrite = int(items["overwrite"]) if "overwrite" in items else 0
    createdirs = items["createdirs"] if "createdirs" in items else None

    if password is None and keyring_id is None:
        print(f"No credentials provided for {section}!", file=sys.stderr)
        exit(1)
    if password is None and keyring_id is not None:
        try:
            password = keyring.get_password(f"pythomat.{keyring_id}", username)

            if password is None:
                print(f"Credentials 'pythomat.{keyring_id}' not found in keyring")
                print(
                    f"You'll be prompted to enter you password for '{section}' with the username '{username}' in order to save it in your keyring as 'pythomat.{keyring_id}'.")
                print("If you don't want to please terminate Pythomat and edit your *.ini-file.")
                password = getpass.getpass(f"Password for {section} keyring: ")
                keyring.set_password(f"pythomat.{keyring_id}", username, password)
        except keyring.errors.KeyringError as ex:
            print(f"Login for {section} failed. Keyring locked: {ex}", file=sys.stderr)
            exit(1)

    br = Browser()
    br.set_handle_robots(False)
    br.open(uri_login)
    br.select_form(id_="UserLoginForm")
    br["data[User][username]"] = username
    br["data[User][password]"] = password
    br.submit()

    uri_afterlogin = br.geturl()
    if "/students/view" not in uri_afterlogin and "/tutors/view" not in uri_afterlogin:
        print(f"[Failed] Login failed for {section}. Expected to be redirected to '/students/view' or '/tutors/view', but url was {uri_afterlogin}", file=sys.stderr)
        exit(1)
    else:
        print(f"Login successful for {section}")

    soup = br.open(uri_materials)
    soup = BeautifulSoup(soup.read(), "html.parser")

    if createdirs and not os.path.exists(saveto):
        os.makedirs(saveto)
        print(f"Created path: {saveto}")
    
    os.chdir(saveto)
    for row in soup.findAll("tr"):
        filelink_dom = row.find(lambda tag: tag.name == "a" and tag.find_parent("td", {"class": "name-cell"}))
        rev_dom = row.find("td", {"class": "rev-column"})
        rev = rev_dom.getText().strip().replace(" ", "")
        downloadpath = urljoin(uri, filelink_dom.get("href"))

        filename = urllib.parse.unquote("".join(downloadpath.split("/")[-1].split(".")[:-1]).replace("_", " "))
        fileext = downloadpath.split("/")[-1].split(".")[-1]

        if fileext_blacklist is not None and fileext in fileext_blacklist:
            print(f"[Ignored] File extension blacklisted: {downloadpath}")
            continue
        if fileext_whitelist is not None and fileext not in fileext_whitelist:
            print(f"[Ignored] File extension not whitelisted: {downloadpath}")
            continue

        if downloadpath.startswith(uri):
            download(pythomat, section, br, downloadpath, overwrite, f"{filename} ({rev}).{fileext}", saveto, detect, detect_recursive)
        else:
            print(f"[Ignored] Externally hosted: {downloadpath}")


def download(pythomat: Pythomat, section: str, br: Browser, url: str, overwrite: int = 1, filename: str = "", saveto: str = "", detect: str = "", detect_recursive: bool = False):
    try:
        if filename == "":
            filename = url.split("/")[-1]
            filename = filename.split("?")[0]
        do_download = True
        if not saveto.endswith("/"):
            saveto = saveto + "/"
        if overwrite == 0 and pythomat.alreadyDownloaded(detect, filename, detect_recursive):
            do_download = False

        if do_download:
            print(f"Downloading {url} as \"{filename}\" …")
            br.retrieve(url, saveto + filename)
            pythomat.reportFinished(section, filename)
            pythomat.reportLog(section, filename)
        else:
            print(f"[Ignored] Already downloaded: {url}")
    except Exception as ex:
        print(f"[Failed] {url}, Error: {ex}", file=sys.stderr)
        pythomat.reportFailed(section, filename)
