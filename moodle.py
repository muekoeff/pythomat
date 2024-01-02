import getpass
import http.client
import os
import re
import sys
import urllib
from typing import List, Tuple

import keyring
from bs4 import BeautifulSoup
from mechanize import Browser

from pythomat import Pythomat

http.client._MAXHEADERS = 1000


def classify_ressource(icon_src: str, fileext_whitelist: List[str]) -> Tuple[str, int] | None:
	# Detect ressource type from icon (LOL). Moodle HTML-output is pretty ugly and seems to provide no better way for detection
	if "/assign" in icon_src:
		return "assignment", 3
	elif "/choicegroup" in icon_src:
		return "choicegroup", 0
	elif "/folder" in icon_src:
		return "folder", 2
	elif "/forum" in icon_src:
		return "forum", 0
	elif "/resource" in icon_src:
		return "unknown", 1
	else:
		for fileext in fileext_whitelist:
			if f"/{fileext}" in icon_src:
				return fileext, 1
		return None

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
	overwrite = items["overwrite"] == "true" or items["overwrite"] == "1" if "overwrite" in items else False
	createdirs = items["createdirs"] if "createdirs" in items else None

	if fileext_whitelist is None:
		fileext_whitelist = ["mpeg", "mp4", "pdf", "png"]
		print(f"[Warn] No whitelist provided for {section}! Due to limitations of Moodle it's highly recommended to provide a whitelist. Defaulted to `fileext_whitelist = mpeg mp4 pdf png`", file=sys.stderr)
	else:
		fileext_whitelist = fileext_whitelist.split(" ")

	if password is None and keyring_id is None:
		print(f"No credentials provided for {section}!", file=sys.stderr)
		pythomat.reportError(section, f"No credentials provided")
		return
	if password is None and keyring_id is not None:
		try:
			password = keyring.get_password(f"pythomat.{keyring_id}", username)

			if password is None:
				print(f"Credentials 'pythomat.{keyring_id}' not found in keyring")
				print(f"You'll be prompted to enter you password for '{section}' with the username '{username}' in order to save it in your keyring as 'pythomat.{keyring_id}'.")
				print("If you don't want to please terminate Pythomat and edit your *.ini-file.")
				password = getpass.getpass(f"Password for {section} keyring: ")
				keyring.set_password(f"pythomat.{keyring_id}", username, password)
		except keyring.errors.KeyringError as ex:
			print(f"Login for {section} failed. Keyring locked: {ex}", file=sys.stderr)
			pythomat.reportError(section, f"Login failed. Keyring locked: {ex}")
			return

	br = Browser()
	br.set_handle_robots(False)
	br.addheaders = [
		('User-agent', 'Pythomat')
	]
	br.open(uri_login)
	br.select_form(id_="login")
	br["username"] = username
	br["password"] = password
	br.submit()

	uri_afterlogin = br.geturl()
	if "/login" in uri_afterlogin:
		print(f"[Failed] Login failed for {section}. Url was {uri_afterlogin}", file=sys.stderr)
		pythomat.reportError(section, f"Login failed. Url was {uri_afterlogin}")
		return
	else:
		print(f"Login successful for {section}")
	
	os.chdir(saveto)
	scan_page(br, uri_materials, saveto, fileext_whitelist, pythomat, section, overwrite, detect, detect_recursive=detect_recursive, createdirs=createdirs)
			

def filelink(icon):
	if icon.parent.get("href") is not None:
		return icon.parent.get("href")
	else:
		links = icon.find_previous("div", class_="activity-item").select(".activityname a")

		if len(links) > 0:
			return links[0].get("href")
		else:
			return None


def scan_page(br: Browser, uri_materials: str, saveto: str, fileext_whitelist: List[str], pythomat: Pythomat, section: str, overwrite: bool, detect: str,
			  detect_recursive: bool = False, createdirs: bool = False):
	soup = br.open(uri_materials)
	soup = BeautifulSoup(soup.read(), "html.parser")
	
	os.chdir(saveto)

	icons = soup.select(".activityinstance .activityicon, .activity-instance .activityicon")
	for icon in icons:
		ressource_classification = classify_ressource(icon.get("src"), fileext_whitelist)

		if ressource_classification is None:
			print(f"[Ignored] Icon could not be classified: {icon.get('src')}")
		elif ressource_classification[1] == 1 or ressource_classification[1] == 3:# Download or Folder
			downloadpath = filelink(icon)

			if downloadpath is not None:
				download_from_raw_url(downloadpath, pythomat, section, br, fileext_whitelist, overwrite, saveto, detect, detect_recursive=detect_recursive, createdirs=createdirs)
		elif ressource_classification[1] == 2:	# Folder
			downloadpath = filelink(icon)

			if downloadpath is not None:
				scan_sub_page(br, downloadpath, saveto, fileext_whitelist, pythomat, section, overwrite, detect, detect_recursive=detect_recursive, createdirs=createdirs)
		else:	# Don't download | ressource_classification[1] == 0:
			print(f"[Ignored] Icon not whitelisted: {icon.get('src')}")


def scan_assignment_page(br: Browser, url: str, saveto: str, fileext_whitelist: List[str], pythomat: Pythomat, section: str, overwrite: bool, detect: str,
						 detect_recursive: bool  =False, createdirs: bool  =False):
	soup = br.open(url)
	soup = BeautifulSoup(soup.read(), "html.parser")

	icons = soup.select("#intro div > .icon")
	for icon in icons:
		ressource_classification = classify_ressource(icon.get("src"), fileext_whitelist)

		if ressource_classification is None:
			print(f"[Ignored] Icon could not be classified: {icon.get('src')}")
		elif ressource_classification[1] == 1:	# Download
			filelink_dom = icon.parent.parent.find("a")
			downloadpath = filelink_dom.get("href")
			download_from_raw_url(downloadpath, pythomat, section, br, fileext_whitelist, overwrite, saveto, detect, detect_recursive=detect_recursive, createdirs=createdirs)
		else:	# Don't download | ressource_classification[1] == 0:
			print(f"[Ignored] Icon not whitelisted: {icon.get('src')}")


def scan_sub_page(br: Browser, url: str, saveto: str, fileext_whitelist: List[str], pythomat: Pythomat, section: str, overwrite: bool, detect: str,
				  detect_recursive: bool = False, createdirs: bool = False):
	soup = br.open(url)
	soup = BeautifulSoup(soup.read(), "html.parser")

	icons = soup.select(".fp-filename-icon .icon")
	for icon in icons:
		ressource_classification = classify_ressource(icon.get("src"), fileext_whitelist)

		if ressource_classification is None:
			print(f"[Ignored] Icon could not be classified: {icon.get('src')}")
		elif ressource_classification[1] == 1: # Download
			filelink_dom = icon.parent.parent
			downloadpath = filelink_dom.get("href")
			download_from_raw_url(downloadpath, pythomat, section, br, fileext_whitelist, overwrite, saveto, detect, detect_recursive=detect_recursive, createdirs=createdirs)
		else: # Don't download | ressource_classification[1] == 0:
			print(f"[Ignored] Icon is not whitelisted: {icon.get('src')}")


def download_from_raw_url(href: str, pythomat: Pythomat, section: str, br: Browser, fileext_whitelist, overwrite: bool, saveto: str, detect: str,
						  detect_recursive: bool = False, createdirs: bool = False):
	response = br.open(href)
	actualdownloadpath = response.geturl()
	filename = urllib.parse.unquote("".join(actualdownloadpath.split("/")[-1].split(".")[:-1]).replace("_", " "))
	fileext = re.sub(r"\?.*", "", actualdownloadpath.split("/")[-1].split(".")[-1])

	if fileext_whitelist is not None and fileext not in fileext_whitelist:
		print(f"[Ignored] File extension is not whitelisted: {href}")
		return

	pythomat.download(section, href, f"{filename}.{fileext}", saveto, detect, detect_recursive=detect_recursive, createdirs=createdirs, overwrite=overwrite, browser=br)
