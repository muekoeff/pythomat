import getpass
import http.client
import os
import urllib
from urllib.parse import urljoin

import keyring
from bs4 import BeautifulSoup
from mechanize import Browser

from pythomat import Pythomat

http.client._MAXHEADERS = 1000


def start(section: str, items: dict, pythomat: Pythomat):
    saveto = items["saveto"]
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
        print("No credentials provided for {}!", section)
        exit(1)
    if password is None and keyring_id is not None:
        try:
            password = keyring.get_password("pythomat.{}".format(keyring_id), username)

            if password is None:
                print("Credentials 'pythomat.{}' not found in keyring".format(keyring_id))
                print(
                    "You'll be prompted to enter you password for '{}' with the username '{}' in order to save it in your keyring as 'pythomat.{}'.".format(
                        section, username, keyring_id))
                print("If you don't want to please terminate Pythomat and edit your *.ini-file.")
                password = getpass.getpass("Password for {} keyring: ".format(section))
                keyring.set_password("pythomat.{}".format(keyring_id), username, password)
        except keyring.errors.KeyringError as ex:
            print("Login for {} failed. Keyring locked: {}".format(section, ex))
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
        print(
            "[Failed] Login failed for {}. Expected to be redirected to '/students/view' or '/tutors/view', but url was {}".format(
                section, uri_afterlogin))
        exit(1)
    else:
        print("Login successful for {}".format(section))

    soup = br.open(uri_materials)
    soup = BeautifulSoup(soup.read(), "html.parser")

    if createdirs and not os.path.exists(saveto):
        os.makedirs(saveto)
        print("Created path: {}".format(saveto))
    
    os.chdir(saveto)
    for row in soup.findAll("tr"):
        filelink_dom = row.find(lambda tag: tag.name == "a" and tag.find_parent("td", {"class": "name-cell"}))
        rev_dom = row.find("td", {"class": "rev-column"})
        rev = rev_dom.getText().strip().replace(" ", "")
        downloadpath = urljoin(uri, filelink_dom.get("href"))

        filename = urllib.parse.unquote("".join(downloadpath.split("/")[-1].split(".")[:-1]).replace("_", " "))
        fileext = downloadpath.split("/")[-1].split(".")[-1]

        if fileext_blacklist is not None and fileext in fileext_blacklist:
            print("[Ignored] {} since its file extension is blacklisted".format(downloadpath))
            continue
        if fileext_whitelist is not None and fileext not in fileext_whitelist:
            print("[Ignored] {} since its file extension is not whitelisted".format(downloadpath))
            continue

        if downloadpath.startswith(uri):
            download(pythomat, section, br, downloadpath, overwrite, "{} ({}).{}".format(filename, rev, fileext), saveto)
        else:
            print("[Ignored] {} since it's an externally hosted file".format(downloadpath))


def download(pythomat: Pythomat, section: str, br: Browser, url: str, overwrite: int = 1, filename: str = "", saveto: str = ""):
    try:
        if filename == "":
            filename = url.split("/")[-1]
            filename = filename.split("?")[0]
        do_download = True
        if not saveto.endswith("/"):
            saveto = saveto + "/"
        if overwrite == 0 and os.path.isfile(saveto + filename):
            do_download = False

        if do_download:
            print("Downloading {} as \"{}\" ...".format(url, filename))
            br.retrieve(url, filename)
            pythomat.reportFinished(section, filename)
            pythomat.reportLog(section, filename)
        else:
            print("[Ignored] {} exists already".format(url))
    except Exception as ex:
        print("[Failed] {}, Error: {}".format(url, ex))
        pythomat.reportFailed(section, filename)
