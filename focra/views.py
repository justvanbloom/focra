import subprocess, re
from subprocess import PIPE
from django.shortcuts import render, redirect
from django.http import HttpResponse
from scrapy.utils.jsonrpc import jsonrpc_client_call
from models import Crawler
import json, collections
from datetime import datetime

'''
welcome page and sign up page
''' 
def index(request):
    '''
    Development purpose, login as jayden
    '''
    username = 'jayden'
    request.session['username'] = username
    crawlers = Crawler.objects(crawlerOwner=username)
    names = []
    for crawler in crawlers:
        names.append(crawler.crawlerName)
    request.session['crawlers'] = names
    return redirect('/' + username)
    '''
    if request.method == 'GET':      
        return render(request, 'index.html')   
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        request.session['username'] = username
        newUser = User(username=username, password=password).save()
        print newUser.username
        return home(request)
    else: 
        return render(request, 'index.html')
    '''

'''
Home page to authenticated usernames
'''   
def overview(request, username):
    if request.method == 'GET':
        username = request.session.get('username');
        if username:
            print 'authenticated'
            crawlers = request.session.get('crawlers')
            return render(request, 'overview.html', {'username': username, 'crawlers': crawlers})
        else:
            print 'not authorised'
            return redirect('/')

'''
Crawler page for crawlers to show stats
'''   
def crawler(request, username=None, crawlerName=None):
    if request.method == 'GET':
        username = request.session.get('username');
        if username:
            crawlers = request.session.get('crawlers')
            crawler = Crawler.objects.get(crawlerName=crawlerName)
            request.session['crawlerName'] = crawler.crawlerName
            request.session['crawlerAddr'] = crawler.crawlerAddr
            request.session['crawlerSeeds'] = crawler.crawlerSeeds
            request.session['crawlerTemplate']= crawler.crawlerTemplate
            t = json.loads(crawler.crawlerTemplate, object_pairs_hook=collections.OrderedDict)
            return render(request, 'crawler.html', {'username': username, 'crawlers': crawlers, 'crawler': crawler, 't': t})
    
'''
To create crawler page
'''
def createCrawler(request):
    username = request.session.get('username')
    crawlers = request.session.get('crawlers')
    if request.method == 'GET':
        if username:
            return render(request, 'create.html', {'username': username, 'crawlers': crawlers})
    if request.method == 'POST':   
        if username:
            crawlerName = request.POST['crawlerName']
            try:
                crawlerAddr = "127.0.0.1:6080"
                #crawlerAddr = runCrawler(crawlerName, seeds, crawlerTemplate);
                Crawler(crawlerName=crawlerName, 
                        crawlerSeeds=request.POST['crawlerSeeds'].split('\r\n'), 
                        crawlerAddr=crawlerAddr, 
                        crawlerStatus='running', 
                        crawlerOwner=username, 
                        crawlerTemplate=request.POST['crawlerTemplate'],
                        crawlerDateTime=datetime.now()).save()            
            except Exception as err:
                print err
            request.session['crawlers'] = crawlers + [crawlerName]
            return redirect('/' + username + '/' + crawlerName)
        
    return redirect('/')
 
'''
To update current crawler in session
'''
def updateCrawler(request):
    return

'''
To delete current crawler in session
'''
def deleteCrawler(request):
    if request.method == 'POST':  
        try:
            crawlerName = request.session.get('crawlerName')
            Crawler.objects(crawlerName=crawlerName).delete()
            crawlers = request.session.get('crawlers')
            crawlers.remove(crawlerName)
            request.session['crawlers'] = crawlers
            return HttpResponse(crawlerName + " has been deleted.")
        except Exception as err:
            print err
    return

'''
To handle start crawler requests
'''
def startCrawl(request):  
    if request.method == 'POST':  
        crawlerName = request.session.get('crawlerName')
        crawlerSeeds = request.session.get('crawlerSeeds')
        crawlerTemplate = request.session.get('crawlerTemplate')
        try:
            crawlerAddr = runCrawler(crawlerName, crawlerSeeds, crawlerTemplate)
            Crawler.objects(crawlerName=crawlerName).update_one(set__crawlerStatus='running', set__crawlerAddr=crawlerAddr)
            request.session['crawlerAddr'] = crawlerAddr
        except Exception as err:
            print err
        return HttpResponse(crawlerName + ' is running')
    else:
        return HttpResponse("Crawl failed")
        
    return redirect('/')
    
'''
To handle stop crawler requests
'''      
def stopCrawl(request):
    if request.method == 'POST':
        print 'stopping ' + request.session.get('crawlerAddr')
        crawlerName = request.session.get('crawlerName')
        stopCrawler(request.session.get('crawlerAddr'))
        try:
            Crawler.objects(crawlerName=crawlerName).update_one(set__crawlerStatus='stopped', set__crawlerAddr='')
        except Exception as err:
            print err
        return HttpResponse(crawlerName + ' has been stopped')
    else:
        return HttpResponse("Stop failed")
    return redirect('/')

'''
starting the crawler through cmdline in local machine
needs to be changed to start through http call for scalability
'''  
def runCrawler(name, seeds, template):
    commands = ["scrapy", "crawl", "focras", "-a", "name=" + name, "-a", "seeds=" + ','.join(seeds), "-a", "template=" + template]
    crawlerProcess = subprocess.Popen(commands, stderr=PIPE)    
    while True:
        crawlerAddr = re.findall('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\:[0-9]{1,5}', crawlerProcess.stderr.readline())
        if crawlerAddr:
            print ''.join(crawlerAddr)
            break;
    return ''.join(crawlerAddr)

'''
stopping crawler through jsonrpc
'''  
def stopCrawler(addr):
    try: 
        jsonrpc_client_call("http://" + addr + "/crawler/engine", 'close_spider', 'focras')
    except:
        print 'Expected stop error, dont worry'

'''
fetch seed url page
'''
def fetch(request):
    
    if request.method == 'GET':
        
        try: 
            from urlparse import urljoin
            url = request.GET['url']  
            
            '''
            Javascript support but very slow
            '''
#             import os
#             p = subprocess.Popen(["python", os.path.dirname(os.path.dirname(__file__)) +'/scripts/test.py', url], stdout=PIPE)  
#             cleaned = ''
#             while True:
#                 res = p.stdout.readline()
#                      
#                 if res == '' and p.poll() != None:
#                     break
#                 a = re.findall('url\((.*?)\)', res)   
#                 if a:
#                     for link in a:           
#                         if 'http' not in link:
#                             link = link.replace("'","")
#                             link = link.replace('"',"")
#                             res = re.sub("url\((.*?)\)", 'url(' + str(urljoin(parsed_url.scheme + "://" + parsed_url.netloc + "/", ''.join(link))) + ')' , res)
#                             print res
#                 cleaned = cleaned + str(res)
            
            '''
            No javascript support, fast
            '''
            import urllib2
            #r = urllib2.urlopen(url)
            req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            r = urllib2.urlopen(req)
            cleaned = ''
            for line in r:
                a = re.findall('url\((.*?)\)', line)

                if a:
                    for link in a:  
                        if 'http' not in link:
                            link = link.replace("'","")
                            link = link.replace('"',"")
                            line = re.sub("url\((.*?)\)"
                                          , 'url(' + str(url) + ''.join(link) + ')' 
                                          , line) 
                    
                cleaned = cleaned + line

            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(cleaned)
            
            for tag in soup.find_all('a', href=True):
                if 'http' not in tag['href']:
                    tag['href'] = urljoin(url + "/", tag['href'])
          
            for tag in soup.find_all('link', href=True):
                if 'http' not in tag['href']:
                    tag['href'] = urljoin(url, tag['href'])
                    print tag['href']
                    
            for tag in soup.find_all('img', src=True):
                if 'http' not in tag['src']:
                    tag['src'] = urljoin(url, tag['src'])
                    #print tag['src'] 
                    
            for tag in soup.find_all('script', src=True):
                if 'http' not in tag['src']:
                    tag['src'] = urljoin(url, tag['src'])
                    #print tag['src']
            
            for tag in soup.find_all('script', async=True):
                tag.decompose()
                
            for tag in soup.find_all('iframe', src=True):
                tag.decompose()
            
            from django.utils.safestring import mark_safe
            return HttpResponse(mark_safe(soup.prettify()))
    
        except Exception as err:
            print err
            
