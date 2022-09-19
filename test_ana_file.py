#!/usr/bin/env python
import urls, os

os.system("cp P100.html site/yidxsfpt/www_ifma_org_il/BRPortal/br/P100.html")

ROOT_URL = "http://www.ifma.org.il/BRPortal/br/P100.jsp"
DEFAULT_SITE = "http://www.ifma.org.il"
LOCAL_PATH = "site/yidxsfpt/"
DONT_MODIFY = [ "js", "gif", "png", "jpg" ]
DOMAIN_WHITE_LIST = [ "www.ifma.org.il", "www.ifma.022.co.il", "www.022.co.il", "www.files.org.il" ]

u = urls.URLs(ROOT_URL)
u.setDomainWhiteList(DOMAIN_WHITE_LIST)

url = "http://www.ifma.org.il/BRPortal/br/P100.jsp"
numFound = 0
localFile = "site/yidxsfpt/www_ifma_org_il/BRPortal/br/P100.html"
fileText = open(localFile).read()
referencedUrlIndexes = [ ]
referencedUrlIndexes += urls.find("src=", fileText)
referencedUrlIndexes += urls.find("href=", fileText)
for i in referencedUrlIndexes:
    referencedUrl = u.getReferencedUrl(fileText, i)
    if not referencedUrl: continue
    u.addFound(referencedUrl)
    u.fixRefToFound(LOCAL_PATH, url, referencedUrl)
    numFound += 1

