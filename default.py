# -*- coding: utf-8 -*-
import urllib, sys, xbmcplugin, xbmcvfs, xbmcgui, xbmcaddon, xbmc, os, json, glob, requests, re, \
	 os

AddonID = 'plugin.video.nfogen'
Addon = xbmcaddon.Addon(AddonID)
AddonName = Addon.getAddonInfo("name")
icon = Addon.getAddonInfo('icon')

addonDir = Addon.getAddonInfo('path').decode("utf-8")


def intro():
	dialog = xbmcgui.Dialog()
	ok = dialog.ok(getLocaleString(10004),
	               getLocaleString(10005),
	               getLocaleString(10006),
	               getLocaleString(10007)
	               )


def getLocaleString(id):
	return Addon.getLocalizedString(id).encode('utf-8')


def SelectFolder():
	folder = xbmcgui.Dialog().browse(3, getLocaleString(10008), "videos", ".mkv|.mp4|.m4v|.avi|.ts|.part").decode(
		"utf-8")
	return folder


def getShowName(folder):
	folders = folder.split("/")
	folder = folders[len(folders) - 2]
	xbmc.log("NFOGEN: folder name : " + folder.encode("utf-8"), level=xbmc.LOGDEBUG)
	search = re.search("([a-zA-Z0-9éèà ._-]+)[_. -]S\d+", folder, flags=re.I)
	if search is None:
		showName = folder
	else:
		showName = search.group(1).replace(".", " ").replace("_", " ")

	xbmc.log("NFOGEN: showName found : " + showName.encode("utf-8"), level=xbmc.LOGDEBUG)

	return GetKeyboardText(getLocaleString(10002), showName)


def ListFilesInFolder():
	acceptableExtensions = [".mkv", '.mp4', '.m4v', '.avi', '.ts', '.part', '.mpg', '.mpeg']
	dirs, fullFiles = xbmcvfs.listdir(folder)
	files = []
	for fullFile in fullFiles:
		filename, file_extension = os.path.splitext(fullFile)
		xbmc.log("testing file : " + fullFile.encode("utf-8"), level=xbmc.LOGDEBUG)
		xbmc.log("testing file extension : " + file_extension, level=xbmc.LOGDEBUG)
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

	xbmc.log("item length : " + str(len(listItems)), level=xbmc.LOGINFO)
	num = xbmcgui.Dialog().select("Choose a picture", listItems, useDetails=True)
	xbmc.log("selected picture : " + str(num), level=xbmc.LOGINFO)

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
				xbmcvfs.rename(folder2 + "/" + file, folder2 + "/" + newFileName);
				newFilesNames.append(newFileName)
			except UnicodeDecodeError:
				xbmc.log("unicode decode error : " + file.encode('utf8'), level=xbmc.LOGINFO)

		folder2 = folder.encode('utf8')
		xbmcvfs.rename(folder2 + "/" + file, folder2 + "/" + newFileName);
		newFilesNames.append(newFileName)

	else:
		newFilesNames = files

		for newFileName in newFilesNames:
			if not re.search("[._-]S\d+", newFileName, flags=re.I):
				raise Exception()

	return newFilesNames


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
	xbmc.log("NFOGEN: tvshow " + str(len(files)).encode('utf8'), level=xbmc.LOGDEBUG)
	seasonXML = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<tvshow>"
	seasonXML += "\n\t<title>"+showName+"</title>"
	seasonXML += "\n\t<season>"+showNumber+"</season>"
	seasonXML += "\n\t<episode>"+str(len(files))+"</episode>"
	seasonXML += "\n\t<thumb>"+picture+"</thumb>"
	seasonXML += "\n</tvshow>"
	xbmc.log(("writing nfo file " + folder + "tvshow.nfo").encode('utf8'), level=xbmc.LOGINFO)
	text_file = xbmcvfs.File(folder + "tvshow" + ".nfo", "w+")
	text_file.write(seasonXML.encode('utf8'))
	text_file.close()


def createFilesNfo(showName, showNumber, files):
	i = 1
	for file in files:
		xbmc.log("NFOGEN: file " + file.encode('utf8'), level=xbmc.LOGDEBUG)
		test_str = file
		xbmc.log("NFOGEN: file " + test_str.encode('utf8'), level=xbmc.LOGDEBUG)
		search = re.search("S\d+E(\d+)", test_str, flags=re.I)

		episodeNum = search.group(1);
		xbmc.log("NFOGEN: file " + file.encode('utf8'), level=xbmc.LOGDEBUG)
		xbmc.log("NFOGEN: episode number " + episodeNum.encode('utf8'), level=xbmc.LOGDEBUG)
		episodeXML = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<episodedetails>"
		episodeXML += "\n\t<title>"+episodeNum+"</title>"
		episodeXML += "\n\t<showtitle>"+showName+"</showtitle>"
		episodeXML += "\n\t<season>"+showNumber+"</season>"
		episodeXML += "\n\t<episode>"+episodeNum+"</episode>"
		episodeXML += "\n</episodedetails>"
		filename, file_extension = os.path.splitext(file)
		xbmc.log(("writing nfo file " + folder + filename + ".nfo").encode('utf8'), level=xbmc.LOGINFO)
		text_file = xbmcvfs.File(folder + filename + ".nfo", "w+")
		text_file.write(episodeXML.encode('utf8'))
		text_file.close()

def confirm():
	dialog = xbmcgui.Dialog(showName, showNumber)
	return dialog.yesno(getLocaleString(10009),
	                    getLocaleString(10010) + showName,
	                    getLocaleString(10011) + showNumber
	                    )


def outro():
	dialog = xbmcgui.Dialog()
	ok = dialog.ok(getLocaleString(10012),
	               getLocaleString(10013)
	               )


def error():
	dialog = xbmcgui.Dialog()
	ok = dialog.ok(getLocaleString(10014),
	               getLocaleString(10015),
	               getLocaleString(10016)
	               )


params = get_params()
folder = None
files = []
showName = None
showNumber = None

xbmc.log("NFOGEN: start nfogen", level=xbmc.LOGINFO)


def log(
		txt):  # Log admits both unicode strings and str encoded with "utf-8" (or ascii). will fail with other str encodings.
	if isinstance(txt, str):
		txt = txt.decode("utf-8")  # if it is str we assume it's "utf-8" encoded.
		# will fail if called with other encodings (latin, etc) BE ADVISED!
	# At this point we are sure txt is a unicode string.
	message = u'%s: %s' % ('plugin.video.nfogen', txt)
	xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)
	# I reencode to utf-8 because in many xbmc versions log doesn't admit unicode.


log("start nfogen")
try:
	intro()
	folder = SelectFolder()
	xbmc.log("folder selected " + folder.encode('utf8'), level=xbmc.LOGINFO)
	files = ListFilesInFolder()
	xbmc.log("files found " + (', '.join(files)).encode('utf8'), level=xbmc.LOGINFO)
	showName = getShowName(folder)
	xbmc.log("Show name " + showName.encode('utf8'), level=xbmc.LOGINFO)
	showNumber = GetKeyboardText(getLocaleString(10003), "01")
	xbmc.log("Show Number " + showNumber.encode('utf8'), level=xbmc.LOGINFO)
	picture = selectPicture(showName)
	xbmc.log("Picture selected" + picture.encode('utf8'), level=xbmc.LOGINFO)
	files = fixFileNames(files, showNumber, folder)
	xbmc.log("filenames fixed" + (', '.join(files)).encode('utf8'), level=xbmc.LOGINFO)
	if confirm():
		xbmc.log("confirmed creating files".encode('utf8'), level=xbmc.LOGINFO)
		createTvShowNfo(showName, showNumber, picture, files, folder)
		createFilesNfo(showName, showNumber, files)
		outro()
except Exception as err:
	xbmc.log("Unexpected error:" + err.message, level=xbmc.LOGDEBUG)
	xbmc.log("Unexpected error:", level=xbmc.LOGDEBUG)
	error()
	raise

sys.exit()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
