import keyring
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from mechanize import Browser
import http.client
import getpass

http.client._MAXHEADERS = 1000


def start(name: str, items: list):
    items = dict(items)

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
    overwrite = items["overwrite"] if "overwrite" in items else 0

    if password is None and keyring_id is None:
        print("No credentials provided for {}!", name)
        exit(1)
    if password is None and keyring_id is not None:
        try:
            password = keyring.get_password("pythomat.{}".format(keyring_id), username)

            if password is None:
                print("Credentials 'pythomat.{}' not found in keyring".format(keyring_id))
                print("You'll be prompted to enter you password for '{}' with the username '{}' in order to save it in your keyring as 'pythomat.{}'.".format(name, username, keyring_id))
                print("If you don't want to please terminate Pythomat and edit your *.ini-file.")
                password = getpass.getpass("Password for {} keyring: ".format(name))
                keyring.set_password("pythomat.{}".format(keyring_id), username, password)
        except keyring.errors.KeyringError as ex:
            print("Login for {} failed. Keyring locked: {}".format(name, ex))
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
        print("[Failed] Login failed for {}. Expected to be redirected to '/students/view' or '/tutors/view', but url was {}".format(name, uri_afterlogin))
        exit(1)
    else:
        print("Login successful for {}".format(name))

    soup = br.open(uri_materials)
    soup = BeautifulSoup(soup.read(), features="lxml")
    for row in soup.findAll("tr"):
        filelink_dom = row.find(lambda tag: tag.name == "a" and tag.find_parent("td", {"class": "name-cell"}))
        rev_dom = row.find("td", {"class": "rev-column"})
        rev = rev_dom.getText().strip().replace(" ", "")
        downloadpath = urljoin(uri, filelink_dom.get("href"))

        filename = "".join(downloadpath.split("/")[-1].split(".")[:-1]).replace("_", " ")
        fileext = downloadpath.split("/")[-1].split(".")[-1]

        if fileext_blacklist is not None and fileext in fileext_blacklist:
            print("[Ignored] {} since its file extension is blacklisted".format(downloadpath))
            continue
        if fileext_whitelist is not None and fileext not in fileext_whitelist:
            print("[Ignored] {} since its file extension is not whitelisted".format(downloadpath))
            continue

        if downloadpath.startswith(uri):
            download(br, downloadpath, "{} ({}).{}".format(filename, rev, fileext), saveto, overwrite)
        else:
            print("[Ignored] {} since it's an externally hosted file".format(downloadpath))


# @FIXME: Use download in pythomat.py
def download(br: Browser, url: str, filename: str = "", saveto: str = "", overwrite: int = 1):
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
            os.chdir(saveto)
            br.retrieve(url, saveto + filename)
            print("Downloaded {} succesfully".format(url))
        else:
            print("[Ignored] {} exists already".format(url))
    except Exception as ex:
        print("[Failed] {}, Error: {}".format(url, ex))
