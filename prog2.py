import base64
import glob
import subprocess

from mechanize import Browser


# Downloads the Videos for Prog2
def start(items):
    user = items["username"]
    password = base64.b64decode(items["password"])
    saveto = items["saveto"]
    br = Browser()
    br.open("https://prog2.cdl.uni-saarland.de/users/login")
    br.select_form(nr=0)
    br["data[User][username]"] = user
    br["data[User][password]"] = password
    response = br.submit()
    p = br.open("https://prog2.cdl.uni-saarland.de/units")
    dummy = p.read()
    for link in br.links(url_regex="/units/view"):
        page = br.follow_link(link)
        content = page.read()
        ids = []
        endindex = 0
        index = content.find("videoId: '", endindex)
        while index > -1:
            endindex = content.find("'", index + 10)
            ids.append(content[index + 10:endindex])
            index = content.find("videoId: '", endindex)
        for id in ids:
            downloadYoutube(id, saveto, False)


# Downloads YouTuve-Video with id to saveto and overwrites (or not)
def downloadYoutube(id, saveto="", overwrite=True):
    output = "-o \"" + saveto + "%(title)s-%(id)s.%(ext)s\""
    if overwrite or len(glob.glob(saveto + "*" + id + "*")) == 0:
        url = "http://www.youtube.com/watch?v=" + id
        subprocess.call("youtube-dl " + output + " \"" + url + " \"", shell=True)
    else:
        print("Video with id " + id + " already exists.")
