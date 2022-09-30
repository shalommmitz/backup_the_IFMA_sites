import yaml, os, random, time, glob, urllib.request, urllib.parse, urllib.error, shutil

HEADER = "<META HTTP-EQUIV='Content-Type' CONTENT='text/html; charset=utf-8'>"
WAIT_LOW = 5; WAIT_HIGH = 29
#WAIT_LOW = 0; WAIT_HIGH = 14

embededUrlsPreambles = [ 'src=', 'href=', 'background:url' ]

urlEncodings = [ ('#b#','<'),('#e#','>'),('#q#','"'),('#d#','.'),('#h#','http://'), ('#_sc#', ':') ] 

UrlStartsToIgnore  = [ "javascript:XSubmit('update')", "javascript:XSubmit('cancel_comment');", "javascript:XSubmit('add_comment');" ] 
UrlStartsToIgnore += [ "javascript:XSubmit('send_email');" ]
UrlStartsToIgnore += [ "data:", "javascript:changeDisplayState" ]
UrlStartsToIgnore += [ "javascript:changeAllDisplayState(", "javascript:refreshForum(" ]
UrlStartsToIgnore += [ "/BRPortal/resources/gan/css/stylesheet.css" ]    # File does not exist at server
UrlStartsToIgnore += [ "../../what_us_can_learn_from_%20Singapore_math.doc" ]    # File does not exist at server
UrlStartsToIgnore += [ "http://www.ifma.org.il/principles/lipingmaintroduction.pdf" ]    # File does not exist at server
UrlStartsToIgnore += [ "http://www.ifma.org.il/detailed_examples/%D7%A1%D7%99%D7%A4%D7%95%D7%A8%D7%99%D7%9D%20%D7%97%D7%A9%D7%91%D7%95%D7%A0%D7%99%D7%99%D7%9D.doc"  ]    # File does not exist at server
UrlStartsToIgnore += [ "javascript:showFloatingPanel_printArticle(", "location.href;"]
UrlStartsToIgnore += [ "#_ftn" ] # A group of files not existing on the server
UrlStartsToIgnore += [ "javascript:printpage();", "mailto:" ]
UrlStartsToIgnore += [ "#menuslide", "//www.youtube.com/embed/" ]

UrlEquatesToIgnore  = [ "../../", "javascript:hideFloatingPanel_printArticle();" ]
UrlEquatesToIgnore += [ "javascript:closeMe();", "javascript:hideMsg('message_layer');" ]
UrlEquatesToIgnore += [ "http://www.ifma.022.co.il/BRPortalStorage/a/62/79/46-AWtPAVsDgm.pdf" ]    # File does not exist at server
UrlEquatesToIgnore += [ "http://www.ifma.022.co.il/BRPortalStorage/a/62/79/47-h7d4tXEvdH.pdf" ]    # File does not exist at server
UrlEquatesToIgnore += [ "http://www.ifma.022.co.il/BRPortalStorage/a/62/79/45-i7DFl11lMe.pdf" ]    # File does not exist at server
UrlEquatesToIgnore += [ "http://www.ifma.022.co.il/BRPortalStorage/a/62/79/42-2XQd5Dmq83.pdf" ]    # File does not exist at server

DONT_MODIFY_FILE_TYPES = [ "js", "gif", "png", "jpg", "pdf", "ico" ]


                                              
def findMulti(substring, string):
    last_found = -1  # Begin at -1 so the next position to search from is 0
    while True:
        # Find next index of substring, by starting after its last known position
        last_found = string.find(substring, last_found + 1)
        if last_found == -1:  
            break  # All occurrences have been found
        yield last_found

def getShortUrl(url): 
    removeUrlStart = [ "http://", "http#_sc#//", "https://" ] 
    for r in removeUrlStart:
        if url.startswith(r): 
            url = url[len(r):]
            break
    if len(url)<27:
        return url.rjust(28)
    else:
        return url[:13] +"..."+ url[-12:]
logEntryNumber = 0       
def toLog(msg, relatedUrl, show=False):
    global logEntryNumber
    logEntryNumber += 1
    if show: 
        print((str(logEntryNumber).zfill(3) +" "+getShortUrl(relatedUrl) +" "+ msg[:160]))
    with open("log.txt", 'a') as log:
        textToFile  = str(logEntryNumber).zfill(3) +" "+ msg
        textToFile += "\n         "+ relatedUrl +"\n\n"
        log.write( textToFile)

class URL(object):
    def __init__(self):
        # phase can be: SEEN, FETCH-STSRTED, FETCHED, DONE
        self.phase = "SEEN"
        self.parentURL = None
        self.protocol = None
        self.netLocation = None
        self.path = None
        self.fileName = None
        self.localFileNames = [ ]
class URLs(object):
    #Main data store: 
    #        urls: a dictionary, with the original URL as key and instance of "URL" as data
    #
    def __init__(self, rootUrl, localStorageRootPath):
        self.urls = { }
        if os.path.isfile("urls.yaml"):
            tmpUrls = yaml.safe_load(open("urls.yaml"))
            for url in list(tmpUrls.keys()):
                self.urls[url] = URL()
                self.urls[url].phase = tmpUrls[url]["phase"]
                self.urls[url].parentURL = tmpUrls[url]["parentURL"]  
                self.urls[url].protocol = tmpUrls[url]["protocol"]             
                self.urls[url].netLocation = tmpUrls[url]["netLocation"]            
                self.urls[url].path = tmpUrls[url]["path"]            
                self.urls[url].fileName = tmpUrls[url]["fileName"] 
                try:           
                    self.urls[url].localFileNames = tmpUrls[url]["localFileNames"]
                except:
                    pass            
        else:
            self.addNewUrl(rootUrl, rootUrl)
        
        self.localStorageRootPath = localStorageRootPath
        self.useWhiteList = False
        self.whiteList = [ ]

    def saveUrls(self):
        tmpUrls = { }
        for url in list(self.urls.keys()):
            tmpUrls[url] = { }
            tmpUrls[url]["phase"] = self.urls[url].phase
            tmpUrls[url]["parentURL"] = self.urls[url].parentURL             
            tmpUrls[url]["protocol"] = self.urls[url].protocol             
            tmpUrls[url]["netLocation"] = self.urls[url].netLocation             
            tmpUrls[url]["path"] = self.urls[url].path             
            tmpUrls[url]["fileName"] = self.urls[url].fileName  
            tmpUrls[url]["localFileNames"] = self.urls[url].localFileNames                         
        yaml.dump( tmpUrls, open("urls.yaml", 'w') )

    def addNewUrl(self, url, parentUrl):
        toLog("    addNewUrl: adding url: '"+ str(url) +"'", url, True)
        #toLog("    addNewUrl: adding url with partent '"+ str(parentUrl) +"'", url)
        if url in list(self.urls.keys()):
            toLog("ERROR: trying to add pre-existing URL - Abort")
            assert url in list(self.urls.keys()), "trying to add pre-existing URL"
        u = URL()
        u.parentURL = parentUrl
        self.urls[url] = u                 # Intermidiate insertion, needed because getUrlParts needs parentUrl
        parts = self.getUrlParts(url)
        u.protocol = parts.protocol
        u.netLocation = parts.netLocation
        u.path = parts.path
        u.fileName = parts.fileName
        self.urls[url] = u

    def deleteUrl(self, url):
        toLog("    deleteUrl: deleting url", url)
        del self.urls[url]

    def setWhiteList(self, whiteList):
        self.useWhiteList = True
        self.whiteList = whiteList

    def logStats(self):
        numSeen = numFetchStarted = numFetched = numDone = 0
        for url in list(self.urls.keys()):
            p = self.urls[url].phase
            if p=="SEEN": 
                numSeen += 1
            elif p=="FETCH-STARTED": 
                numFetchStarted += 1
            elif p=="FETCHED": 
                numFetched += 1
            elif p=="DONE": 
                numDone += 1
            else:
                toLog("ERROR: Phase of URL is unexpected: '"+p+"' - Aborting.", url, True)
                exit()
        toLog("Stats: Seen %d, Fetched-started %d, Fetched %d, Done %d" % (numSeen, numFetchStarted, numFetched, numDone), "", True)

    def decodeUrl(self, url):
        def isHashedUrl(url):
            return url.startswith("#q#")

        origUrl = url

              
        if isHashedUrl( url):
            url = url[len("#q#"):]
            end = url.find("#q#")
            url = url[:end]            
            
        for ue in urlEncodings:
            url = url.replace( ue[0], ue[1] )
        #toLog("    decodeUrl returned: "+url, origUrl)   
        return url

    def encodeUrl(self, url, urlToBeEncoded):
        def isHashedUrl(url):
            return url.startswith("#q#") 
 
        if isHashedUrl(url):
            for ue in urlEncodings:
                urlToBeEncoded = urlToBeEncoded.replace( ue[1], ue[0] )
            encodedUrl  = "#q#"
            encodedUrl += urlToBeEncoded
            encodedUrl += url[url.find("#q#", 4):]
        else:
            encodedUrl = urlToBeEncoded
 

        if url.startswith("javascript:redirect('"):
            encodedUrl = "javascript:redirect("+ encodedUrl +"');"

        #toLog("encodedUrl returned: ", url)
        return encodedUrl


    def setPhase(self, url, newPhase):
        if newPhase not in ["SEEN", "FETCH-STARTED", "FETCHED", "DONE"]:
            toLog("ERROR: Requested new phase '"+ newPhase +"' is not allowed - Aborting", url, True)
            exit()
        self.urls[url].phase = newPhase
    def isInPhase(self, url, phase):
        return self.urls[url].phase == phase
    
    def getParentUrl(self, url):
        return self.urls[url].parentURL
 
    def getUrlParts(self, url, localUrl = False):
        class UrlParts(object):
            def __init__(self, protocol, netLocation, path, fn):
                self.protocol = protocol
                self.netLocation = netLocation
                self.path = path
                self.fileName  = fn
            def __repr__(self):
                s  = "proto: "+str(self.protocol)+", netLoc: "+ str(self.netLocation)+",\n"
                s += getShortUrl("")+"     path: "+str(self.path)+", fn: "+ str(self.fileName)
                return s

        #toLog("    getUrlParts: got as input: '"+ str(url) +"'", "")
        #toLog("    getUrlParts: got as input: (optional) is local: '"+ str(localUrl) +"'", "")

        protocol = netLocation = path = fn = None
        u = self.decodeUrl(url)
        if "://" in u and not localUrl:
            protocol = u.split("://")[0]
            u = u.split("://")[1]
            netLocation = u.split("/")[0]
            pathFn =  "/".join( u.split("/")[1:] )
        elif not localUrl:
            parentUrlParts = self.getUrlParts( self.getParentUrl(url) )
            protocol = parentUrlParts.protocol
            netLocation = parentUrlParts.netLocation
            #if parentUrlParts.path.startswith("/"):
            if u.startswith("/"):
                pathFn = u[1:]
            else:
                pathFn = parentUrlParts.path
                if not pathFn.endswith("/"): pathFn += "/"
                pathFn +=  u
        else:     # localUrl
            protocol = None; netLocation = None
            pathFn =  u
        path = "/".join(pathFn.split("/")[:-1]) +"/"       
        fn = pathFn.split("/")[-1]
        up = UrlParts( protocol, netLocation, path, fn )
        #toLog("    getUrlParts: returning: '"+ str(up) +"'", "")
        return up

    def getCachePathFileName(self, url):
        return "cache/"+ self.urls[url].netLocation.replace(".", "_") +"/"+ self.urls[url].fileName

    def handleRedirect(self, url, resFN, cachePath, fn):
        res = open(resFN).read()
        if not "302 Moved Temporarily" in res: return

        toLog("    handleRedirect: URL that was redirect detected", url, True)
        #Get redirectedFileName + fetch redirected file
        res = open(resFN).read().split("\n")
        targetRedirectedURL = None
        for line in res:
            line = line.strip()
            if line.startswith("Location:"): targetRedirectedURL = line.split()[1]
 
        toLog("    handleRedirect: Target redirected URL", targetRedirectedURL, True)
        #genrate redireciton file at the cache, replacing original file (no need to copy - this will be done by parent function)
        s  = '<!DOCTYPE HTML>' +'\n'                        
        s += '<html lang="en-US">' +'\n'
        s += '    <head>' +'\n'
        #s += '        <meta charset="UTF-8">' +'\n'   # inserted later by 'finalize'
        s += '        <meta http-equiv="refresh" content="0; url=URL">' +'\n'
        s += '        <script type="text/javascript">' +'\n'
        s += '            window.location.href="URL"' +'\n'
        s += '        </script>' +'\n'
        s += '        <title>Page Redirection</title>' +'\n'
        s += '    </head>' +'\n'
        s += '    <body>' +'\n'
        s += '        If you are not redirected automatically, follow this <a href=\'URL\'> link</a>' +'\n'
        s += '    </body>' +'\n'
        s += '</html>' +'\n'
        redirectPage = s.replace("URL", targetRedirectedURL)
        toLog("    redirectURL: overwriting fetched w/redirect-file", cachePath + fn, True)
        existingFileInCache = self.getCachePathFileName(url)
        open(existingFileInCache, 'w').write(redirectPage)

    def createPathIfNeeded(self, url):
        localPathFN = self.getLocalPathFilename(url)
        localPathFnParts = self.getUrlParts(localPathFN, True)
        localPath = localPathFnParts.path
        if not os.path.isdir(localPath): 
            toLog("    Creating local path: "+ localPath, url)
            os.makedirs(localPath)

    
        
    def fetch(self, url):
        def copyFileFromCacheToLocalAndFixCharSet(url):
            localPathFN = self.getLocalPathFilename(url)
            cmd = "cp '"+ self.getCachePathFileName(url) +"' '"+ localPathFN +"'"
            toLog("    fetch: copy cmd: "+ cmd, url)
            os.system(cmd)
            if localPathFN.endswith("html"):
                if HEADER not in open(localPathFN).read(1000):
                    self.replaceInFile( localPathFN, "\n<head>\n", "\n<head>\n"+ HEADER +"\n" )

        toLog("    Entering fetch", url)

        localPathFN = self.getLocalPathFilename(url)
        self.createPathIfNeeded(url)
        #if localPathFN.endswith("jsp"):
        #    localPathFN = localPathFN[:-len("jsp")] +"html"
        if os.path.isfile(localPathFN):
            # Since the file this URL points to is already handled by another URL, there is nothing more
            #    we need to do with this URL - so we can mark it "done".
            # Multiple URLs pointing at the same file on the server, at the same location, is legitimate, since different URLs (esp. with relative path) can point to same file.
            toLog("    Local file pre-exists - Will mark URL as DONE and return", localPathFN, True)
            self.setPhase(url, "DONE")   
            return
        
        #If we are here, we are commited to work on this URL, so good time to change the phase
        self.setPhase(url, "FETCH-STARTED")

        fn = self.urls[url].fileName
        cachePath = "cache/"+ self.urls[url].netLocation.replace(".", "_") +"/"
        if not os.path.isdir(cachePath): 
            toLog("    Creating local path: "+ cachePath, url)
            os.makedirs(cachePath)

        if os.path.isfile(cachePath + fn): 
            toLog("    At fetch: cache hit - no fetch from the Internet", cachePath + fn, True)
            copyFileFromCacheToLocalAndFixCharSet(url)
            self.setPhase(url, "FETCHED")  
            return 
        
        toLog("    fetch: cache miss, will fetch from the Internet to the cache", url, True)
        u = self.urls[url]
        fullUrl = u.protocol +"://"+ u.netLocation +"/"+ u.path + u.fileName
        toLog("    fetch: Full url for fetching.", fullUrl)
        #urllib.urlretrieve( fullUrl, "cache/"+ fn )
        resFN = cachePath + fn +"_fetch_result.txt"
        cmd = "wget -o '"+ resFN + "' -O '"+ cachePath + fn +"' '"+ fullUrl +"'"
        toLog("    wget command: "+ cmd, url)
        os.system(cmd)
        size = os.path.getsize(cachePath + fn)
        if size<3:
            toLog("ERROR at fetch: file too small - Aborting", url, True)
            assert not size<3, "ERROR at fetch: file too small"

        self.handleRedirect(url, resFN, cachePath, fn)

        sleepSeconds = random.randint(WAIT_LOW, WAIT_HIGH)
        toLog("    Fetch done. Will sleep for "+ str(sleepSeconds) +" seconds.", "", True)
        time.sleep( sleepSeconds )

        copyFileFromCacheToLocalAndFixCharSet(url)
        self.setPhase(url, "FETCHED")   
            
    def isOkToFetch(self, url):
        if not self.isInPhase(url, "SEEN"):
            toLog("    isOkToFetch rejected URL because phase not 'SEEN'", url)
            return False
        return True
         
    def replaceInFile(self, fn, findStr, newStr):
         toLog("    replaceInFile: in file '"+ fn +"':", "")
         toLog("        replacing '"+ findStr.replace("\n","\\n") +"'", "")
         toLog("        with '"+ newStr.replace("\n","\\n") +"'", "")
         if "ifma." in newStr:
             toLog("ERROR at replaceInFile: try to insert string with unmodified site name - Aborting", "", True)
             assert True==False
         s = open(fn).read()
         s = s.replace(findStr, newStr)
         open(fn, 'w').write(s)


    def fetchIfNeeded(self):
        numToLookAt = 0
        for url in list(self.urls.keys()):
            #print(f'fetchIfNeeded: looking at url {url}. isOkToFetch: {self.isOkToFetch(url)}')
            if self.isOkToFetch(url): numToLookAt += 1
        toLog("fetchIfNeeded starting.","", True)

        numFetched = 0; numFilesLookedAt = 0
        for url in list(self.urls.keys()):
            if not self.isOkToFetch(url): continue
            numFilesLookedAt += 1
            if numFilesLookedAt % 10 == 0:
                toLog("Looking at file %d of %d" % (numFilesLookedAt, numToLookAt), "", True)


            self.fetch(url)
            
            
            numFetched += 1
            if numFetched%10==0: 
                self.saveUrls()
                self.logStats()
        self.saveUrls()
        toLog("fetchIfNeeded: fetched "+ str(numFetched), "", True)
        return numFetched

    def getLocalPathFilename( self, url):
        if url not in list(self.urls.keys()):
            toLog("ERROR at getLocalPathFilename: requested URL does not exist in URLs - Aborting", str(url), True)
            print("   URL is: "+ str(url))
            assert url in  list(self.urls.keys())   #crash sw, so we can see stack
        netLocation = self.urls[url].netLocation.replace(".", "_")
        fileName = self.urls[url].fileName 
        
        if "?" in fileName:
            fnExtension = fileName.split("?")[0]
            if "." in fnExtension:
                fn = fnExtension.split(".")[0]
                extension = fnExtension.split(".")[1]
            else:  
                htmlFileNames = [ "w", "tasks", "rss", "page" ]
                if fnExtension in htmlFileNames:
                    fn = fnExtension
                    extension = "html"
                elif netLocation in ["www_youtube_com", "docs_google_com", "news_nana10_co_il" ]:
                    fn = fnExtension
                    extension = None
                else:
                    toLog("ERROR: Unknown file w/o extension - Aboring.", url, True)
                    toLog("   netLocation is: "+ netLocation, "")
                    toLog("   Unknown url is: "+ url, "")
                    exit()
            args = fileName.split("?")[1]
            fileName  = fn +"_"+ args.replace("=", "_").replace(",", "_").replace(":", "_").replace("&", "_") 
            if extension: fileName += "."+ extension
        localPathFN = self.localStorageRootPath + netLocation +"/"+ self.urls[url].path + fileName 

        if localPathFN.endswith(".jsp"):
            localPathFN = localPathFN[:-len(".jsp")] +".html"
        toLog("    getLocalPathFilename returning: '"+ localPathFN +"'", url)
        if "br/"+ self.localStorageRootPath in localPathFN:
            toLog("ERROR at getLocalPathFilename: returened value contains double path - Aborting", str(url), True)
            x = 12/0
        if "ifma." in localPathFN and not "?vhost=" in localPathFN:
            toLog("ERROR at getLocalPathFilename: returened value contains web site name - Aborting", str(url), True)
            exit()
        return localPathFN

     #################                                                     ##############    
     ################# find embeded URLs in local file, localize, re-embed ##############    
     #################                                                     ##############    

    def extractEmbededUrl(self, l, i):
        def stripQuotes(s):
            startingQuoteChar = s[0]
            s = s[1:]            
            startTofinishQuoteChars = { "'": "'", '"': '"', "(": ")" }
            finishQuoteChar =  startTofinishQuoteChars[startingQuoteChar] 
            end = s.find(finishQuoteChar)
            s = s[:end]
            return s

        embededUrl = l[i:]
        foundPreamble = None
        for p in embededUrlsPreambles:
            if embededUrl.startswith(p): 
                embededUrl = embededUrl[len(p):]
                foundPreamble = p
                break
        if not foundPreamble: 
            toLog("ERROR: Unexpected start of found embeded URL - Aborting.", "", True)
            toLog("    Start of embededUrl: "+embededUrl[:30], "", True)
            exit()
        if embededUrl.startswith("location.href;"):
            embededUrl = "location.href;"
        elif embededUrl.startswith("#q#"):
            embededUrl = embededUrl[:embededUrl.find("#q#", 4)+3]
        else: 
            embededUrl = stripQuotes(embededUrl)
            internalWrapper = [ "javascript: showService(", "javascript:showService(", "javascript:redirect(" ]
            for w in internalWrapper:          
                if embededUrl.startswith(w):
                    embededUrl = embededUrl[len(w):]
                    embededUrl = stripQuotes(embededUrl)
                    break

        if len(embededUrl)<3: return None

        toLog("    extractEmbededUrl: returning",embededUrl)

        return embededUrl

            
    def getRelativeLocalizedEmbededUrl( self, url):
        parentLocalUrl = self.getLocalPathFilename(self.urls[url].parentURL)
        if url=="http#_sc#//www.ifma.org.il/":  # Implment re-direciton normally done at server       
            url = "http://www.ifma.org.il/BRPortal/br/P100.jsp"
        localizedUrl = self.getLocalPathFilename(url)
        parentList = parentLocalUrl.split("/")
        urlList = localizedUrl.split("/")
        for i in range(min( len(parentList), len(urlList) )):
            if parentList[i]!=urlList[i]: 
                break
        toLog("    getRelativeLocalizedEmbededUrl: found that first %d levels are identical btwn parent and current" % i, url)
        levelsInParentPath = len(parentList) - i - 1
        parentList = parentList[i:]
        urlList = urlList[i:]
        localizedUrl = "../"*levelsInParentPath + "/".join(urlList)
        localizedUrl = self.encodeUrl(url, localizedUrl)
        toLog( "    getRelativeLocalizedEmbededUrl: return: "+ localizedUrl, url)
        return localizedUrl

    def isOkToAdd(self, url): 
        u = self.urls[url]
        decodedUrl = self.decodeUrl(url)
        #fullUrl = u.protocol +"://"+ u.netLocation +"/"+ u.path + u.fileName
        
        for ignoreStr in UrlEquatesToIgnore:
            if decodedUrl==ignoreStr: 
                toLog("    isOkToAdd: reject URL because it equates to '"+ ignoreStr +"'", url, True)
                return False
        for ignoreStr in UrlStartsToIgnore:
            if decodedUrl.startswith(ignoreStr): 
                toLog("    isOkToAdd: reject URL because it starts with '"+ ignoreStr +"'", url, True)
                return False
 
        if len(u.fileName)>200:  
            toLog("    isOkToAdd: reject URL because the file name is too long (>200)", url, True)
            return False
 
        netLocation = u.netLocation
        if netLocation not in list(self.whiteList.keys()):
            toLog("    isIgnoreUrl: reject URL because site not in white list", url, True)
            return False
        path = u.path
        for startOfWhiteListed in self.whiteList[netLocation]:
            if path.startswith(startOfWhiteListed):
                toLog("    isOkToAdd accepted URL because path+site are in white list. Path matched with: "+ startOfWhiteListed, url, True)
                return True
        toLog("    isOkToAdd rejected URL because site matched, but not path. Path starts with: '"+ path[:44] +"'", url, True)
        return False


    def localizeAllEmbededUrlsInFile(self, url):
        localFile = self.getLocalPathFilename(url)
        toLog("localizeAllEmbededUrlsInFile: will analyze/modify local file: "+ localFile, url, True)
        numFound = 0
        fileText = modifiedFileText = open(localFile).read()
        #if "If you are not redirected automatically, follow this" in fileText:
        #    toLog("    File is a redirection-file genrated by this software - no adjusment needed - Done","", True)
        #    return 
        if self.localStorageRootPath in fileText:
            toLog("ERROR in localizeAllEmbededUrlsInFile: file text contains already localized URLs - double invocation? - Aborting", self.localStorageRootPath, True)
            exit()
        embededUrlIndexes = [ ]
        for p in embededUrlsPreambles:
            embededUrlIndexes += findMulti(p, fileText)
        for i in embededUrlIndexes:
            embededUrl = self.extractEmbededUrl(fileText, i)
            if not embededUrl: continue
            if embededUrl in list(self.urls.keys()): 
                toLog("    Embeded URL pre-exist, will change parent to '"+ url +"'", embededUrl)
                self.urls[embededUrl].parentUrl = url
            else:
                toLog("    Embeded URL never seen before, will add it.", embededUrl)
                self.addNewUrl(embededUrl, url)  
                if not self.isOkToAdd(embededUrl):
                    self.deleteUrl(embededUrl)   #we needed to temporarily add the URL, so isOkToAdd can analyze it
                    continue
            
            localizedEmbededUrl = self.getRelativeLocalizedEmbededUrl(embededUrl)
            toLog("    localizeAllEmbededUrls: replacing in text of file "+ localFile, "")    
            toLog("        text to find: "+ embededUrl, "")    
            toLog("        replace by: "+ localizedEmbededUrl, "")    
            modifiedFileText = modifiedFileText.replace(embededUrl, localizedEmbededUrl)
            numFound += 1
        open(localFile, 'w').write(modifiedFileText)
        toLog("localizeEmbededUrls: found/added/localized %d urls" % numFound, url)
        #if "If you are not redirected automatically, follow this" in fileText:
        #    toLog("Abort to look at modifed redirect file","",True)
        #    assert 1==2

    def analyzeAllFetchedFiles(self):
       # For each newly fetched file:  
       #      find embeded URLs, localized references and add found URLs as see for later fetching
        numFilesModified = 0
        for url in list(self.urls.keys()):
            if not self.isInPhase(url, "FETCHED"): 
                toLog("    Ignoring URL because not in 'FETCHED' phase", url, True)
                continue
            fileType = self.urls[url].fileName.split(".")[-1]
            if fileType in DONT_MODIFY_FILE_TYPES: 
                toLog("    Skip analysing local file because of file type. URL marked DONE", url, True)
                self.setPhase(url, "DONE")
                continue
            
            if url!="http#_sc#//www.ifma.org.il/":
                numFilesModified += 1
                self.localizeAllEmbededUrlsInFile(url)

            self.setPhase(url, "DONE")
            if numFilesModified % 5 ==0:
                self.saveUrls()
        self.saveUrls()
        toLog("analyzeAllFetchedFiles: modifed %d files." % numFilesModified, "", True)
        return numFilesModified

if __name__=="__main__":
    os.system("rm 'cache/www_understending-math_022_co_il/P102.jsp?arc=970601'")
    os.system("rm 'tmp/www_understending-math_022_co_il/BRPortal/br/P102_arc_970601.html'")
    ROOT_URL = "http://www.ifma.org.il/BRPortal/br/P100.jsp"
    u = URLs(ROOT_URL, "tmp/")
    url = "http://www.understending-math.022.co.il/BRPortal/br/P102.jsp?arc=970601"
    u.addNewUrl(url, ROOT_URL)
    u.fetch(url)
    exit()

    u = URLs("ROOT_URL", ".")
    s = 'Arial;" href="../../what_us_can_learn_from_%20Singapore_math.doc"#_gt##_lt#br#'
    print(u.extractEmbededUrl(s, 8))
    exit()

    print(u.extractEmbededUrl("<a href=\"javascript:showService('P112.jsp?cmd=arc:365310',470,385);\">", 3))
    s = """
var ifsc2 = ifrm.contentWindow.document.createElement('script');
ifsc1.src='/BRPortal/resources/gan/js/bioride.js';
ifsc2.src='/BRPortal/resources/gan/js/jquery.js';
ifsc1.type ='text/javascript';
ifsc2.type ='text/javascript';
ifrm.contentWindow.document.head.appendChild(ifsc1);
ifrm.contentWindow.document.head.appendChild(ifsc2);
}
</script>
</td></tr></table></td></tr></table></div><div>&nbsp;</div><div>&nbsp;</div></td></tr></table></div><div style="padding-top:10px;" align="center"></div></td></tr></table></td></tr></table><input id="csrf_protection_token" name="csrf_protection_token" value="b7TbZjVZ0IiWcEEDgFdBRebEJlpAYO1IrLtAynR4YOXHcBj4ZKA1SZSglD3uzLJe" type="hidden" /><table width="969" cellspacing="0" cellpadding="0" align="center"><tr><td><div style="display:block;margin-right:auto;margin-left:auto;overflow:hidden;width:969px;">  
<!--[if IE]>
""" 
    loc = s.find("src=")
    print("loc:", loc)
    print(u.extractEmbededUrl(s,loc)) 
    


