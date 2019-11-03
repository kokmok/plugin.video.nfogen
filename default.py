# -*- coding: utf-8 -*-
import urllib, sys, xbmcplugin, xbmcvfs, xbmcgui, xbmcaddon, xbmc, os, json, glob, requests, re, \
    xml.etree.cElementTree as ET, os

AddonID = 'plugin.video.nfogen'
Addon = xbmcaddon.Addon(AddonID)
AddonName = Addon.getAddonInfo("name")
icon = Addon.getAddonInfo('icon')

addonDir = Addon.getAddonInfo('path').decode("utf-8")


def intro():
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('How to be sure kodi will find tvshow',
                   'Store your season folder in the tvshows (scanned) root folder' + ' ok : /folder/tvshow/dinotrux Season 1',
                   'not ok : /folder/tvshow/dinotrux/dinotrux Season 1',
                   'Be sure files are well named (ex dinotrainE02) the episode number should be visible'
                   )


def getLocaleString(id):
    return Addon.getLocalizedString(id).encode('utf-8')


def SelectFolder():
    folder = xbmcgui.Dialog().browse(3, "select source folder", "videos", ".mkv|.mp4|.m4v|.avi|.ts|.part").decode("utf-8")
    return folder

def getShowName(folder):
	folders = folder.split("/")
	folder = folders[len(folders) - 2]
	return GetKeyboardText(getLocaleString(10002), folder)


def ListFilesInFolder():
    acceptableExtensions = [".mkv", '.mp4', '.m4v', '.avi', '.ts', '.part', '.mpg', '.mpeg']
    dirs, fullFiles = xbmcvfs.listdir(folder)
    files = []
    for fullFile in fullFiles:
        filename, file_extension = os.path.splitext(fullFile)
#        xbmc.log("testing file : " + fullFile.encode("utf-8"), level=xbmc.LOGDEBUG)
#        xbmc.log("testing file extension : " + file_extension, level=xbmc.LOGDEBUG)
        if (len(filter(lambda x: x == file_extension, acceptableExtensions)) > 0):
            files.append(fullFile)

    return files


def selectPicture(showName):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0',
    }
    requestUrl = "https://api.qwant.com/api/search/images?count=10&offset=0&q=" + showName + "&t=images&uiv=4"
    r = requests.get(requestUrl, headers=headers)
    xbmc.log(r.text.encode('utf-8'), level=xbmc.LOGINFO)
    result = r.json()
    images = result['data']['result']['items']

    listItems = []
    i = 0
    for item in images:
        name = item['title']
        icon = item['media']
        addonid = int(item['size']) / 1024
        listitem = xbmcgui.ListItem(label=name, label2=str(addonid) + "Ko", iconImage=icon, thumbnailImage=icon)
        listItems.append(listitem)
        i += 1

    log("item length : " + str(len(listItems)))
    num = xbmcgui.Dialog().select("Choose a picture", listItems, useDetails=True)
    log("selected picture : " + str(num))

    return images[num]['media']


def fixFileNames(files, showNumber, folder):
    newFilesNames = []
    if not re.search("[._-]S\d+", files[0], flags=re.I):
        for file in files:
            if re.search("(e[0-9]+)", file, flags=re.I):
                newFileName = re.sub("(e[0-9]+)", "S" + str(showNumber) + "\\1", file, flags=re.I)

            else:
                newFileName = re.sub("[._-]([0-9]+)", "S" + str(showNumber) + "E\\1", file, flags=re.I)

            try:
		xbmcvfs.rename(folder + "/" + file, folder + "/" + newFileName);
		newFilesNames.append(newFileName)
	    except UnicodeDecodeError:
		#newFileName = newFileName.decode('utf8')
		folder = folder.encode('utf8')
		xbmcvfs.rename(folder + "/" + file, folder + "/" + newFileName);
		newFilesNames.append(newFileName)
		
    else:
        newFilesNames = files

	for newFileName in newFilesNames:
		if not re.search("[._-]S\d+", newFileName, flags=re.I):
			raise Exception()

    return newFilesNames;


def GetKeyboardText(title="", defaultText=""):
    keyboard = xbmc.Keyboard(defaultText, title)
    keyboard.doModal()
    text = "" if not keyboard.isConfirmed() else keyboard.getText()
    return text

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0].lower()] = splitparams[1]
    return param



def createTvShowNfo(showName, showNumber, picture, files, folder):

    tvshow = ET.Element('tvshow')
    ET.SubElement(tvshow, 'title').text = showName
    ET.SubElement(tvshow, 'season').text = showNumber
    ET.SubElement(tvshow, 'episode').text = str(len(files))
    ET.SubElement(tvshow, 'thumb').text = picture
    tree = ET.ElementTree(tvshow)
    tree.write(folder + "/tvshow.nfo", encoding='utf-8', xml_declaration=True)


def createFilesNfo(showName, showNumber, files):
    for file in files:
        regex = r"S\d+E(\d+)"
        test_str = file
        matches = re.finditer(regex, test_str, flags=re.I)
        match = next(matches)
        episodeNum = match.group(1);
        log("file " + file)
        log("episode number " + episodeNum)

        episode = ET.Element('episodedetails')
        ET.SubElement(episode, 'title').text = episodeNum
        ET.SubElement(episode, 'showtitle').text = showName
        ET.SubElement(episode, 'season').text = showNumber
        ET.SubElement(episode, 'episode').text = episodeNum
        tree = ET.ElementTree(episode)
        filename, file_extension = os.path.splitext(file)
        #log(("writing nfo file " + folder + filename + ".nfo"))
        try: 
	    tree.write(folder + filename + ".nfo",encoding='utf-8', xml_declaration=True )
	except UnicodeDecodeError:
	    tree.write(folder.encode('utf8') + filename + ".nfo",encoding='utf-8', xml_declaration=True )
def confirm():
	dialog = xbmcgui.Dialog(showName, showNumber)
	return dialog.yesno('Please confirm generation, existing nfo files will be overwritten',
				   'TV show : '+showName,
				   'Season : '+showNumber
				   )

def outro():
	dialog = xbmcgui.Dialog()
	ok = dialog.ok('The nfo files should have be created',
			   'Now you can update your video library'
			   )
def error():
	dialog = xbmcgui.Dialog()
	ok = dialog.ok('Oops',
				   'Something went wrong',
				   'Please check your filenames'
				   )

params = get_params()
folder = None
files = []
showName = None
showNumber = None




def log(txt): #Log admits both unicode strings and str encoded with "utf-8" (or ascii). will fail with other str encodings.
    if isinstance (txt,str):
        txt = txt.decode("utf-8") #if it is str we assume it's "utf-8" encoded.
                                  #will fail if called with other encodings (latin, etc) BE ADVISED!
# At this point we are sure txt is a unicode string.
    message = u'%s: %s' % ('plugin.video.nfogen', txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)
    # I reencode to utf-8 because in many xbmc versions log doesn't admit unicode. 



log("start nfogen")
try:
    intro()
    folder = SelectFolder()
    log("folder selected ")
    files = ListFilesInFolder()
    log("files found " + (', '.join(files)))
    showName = getShowName(folder)
    log("Show name " + showName)
    showNumber = GetKeyboardText(getLocaleString(10003), "01")
    log("Show Number " + showNumber)
    picture = selectPicture(showName)
    log("Picture selected" + picture)
    files = fixFileNames(files, showNumber, folder)
    log("filenames fixed" + (', '.join(files)))
    if confirm():
        log("confirmed creating files")
        createTvShowNfo(showName, showNumber, picture, files, folder)
        createFilesNfo(showName, showNumber, files)
        outro()
except:
    error()
    raise

sys.exit()


xbmcplugin.endOfDirectory(int(sys.argv[1]))
