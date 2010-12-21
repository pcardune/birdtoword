import re
import os
import simplejson
import random
import logging
import yaml
import copy

from google.appengine.api import users, mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import RequestHandler
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache

from birdtoword import graph, api, model

def filepath(*s):
    return os.path.join(*((os.path.dirname(__file__),)+s))
def templatepath(s):
    return os.path.join(os.path.dirname(__file__), 'templates', s)


NAV_CONFIG = yaml.load(open(filepath("nav.yaml"),'r'))

class PageHandler(RequestHandler):
    '''Helper base class that renders templates'''

    template = None

    __cookies = None
    def setCookies(self, **kwargs):
        if self.__cookies is None:
            self.__cookies = {}
        self.__cookies.update(dict((key.replace("_",'-'), str(value))
                                   for key, value in kwargs.items()))
        logging.info("setting cookies: %r" % self.__cookies)
        self.response.headers.add_header('set-cookie', None, **self.__cookies)

    def getCookie(self, key):
        cookie = self.request.cookies.get(key.replace("_","-"))
        logging.info("getting cookie %r: %r" % (key, cookie))
        return cookie

    def __updateNavigation(self):
        loggedIn = api.getPlayer(self.request)
        count = 0
        for nav in self.model['nav']['items']:
            nav['class'] = 'active' if self.request.path == nav['url'] else ''
            nav['available'] = available = (not nav.get('login') or (nav['login'] and loggedIn))
            if available:
                count += 1

        self.model['nav']['config']['spaces'] = 11-count

    def update(self):
        self.model = {
            'nav':{
                'items':copy.deepcopy(NAV_CONFIG),
                'config':{}
                },
            'request':self.request
            }
        if api.getPlayer(self.request):
            self.model['nav']['items'].append(
                {'url':users.create_logout_url('/'),
                 'title':'Logout',
                 'id':'logout'})
        else:
            self.model['nav']['items'].append(
                {'url':users.create_login_url('/'),
                 'title':'Login',
                 'id':'login'})
        self.__updateNavigation()

    def get(self):
        self.update()
        if self.template is not None:
            self.response.out.write(template.render(self.template, self.model))


class AdminFrontPage(PageHandler):
    '''A front page for application administration'''
    url = '/admin'

    template = templatepath('admin.html')

    def update(self):
        super(AdminFrontPage, self).update()

        players = self.model['players'] = list(db.GqlQuery("SELECT * FROM Player"))
        gameCount = 0
        for player in players:
            gameCount += len(player.games)
        self.model['gameCount'] = gameCount


class FrontPage(PageHandler):
    '''A simple test page.'''
    url = '/'

    template = templatepath('front-page.html')

    def update(self):
        super(FrontPage, self).update()
        self.model['loginUrl'] = users.create_login_url('/')
        player = api.getPlayer(self.request)
        self.model['player'] = player
        games = reversed(list(db.GqlQuery("SELECT * FROM GameRecord WHERE player = :1", player)))
        self.model['games'] = games


class ExplorePage(PageHandler):
    '''A simple explore page.'''
    url = '/explore'

    template = templatepath('explore.html')


class HistoryPage(PageHandler):
    '''A simple history page.'''

    url = '/history'
    template = templatepath('history.html')

    def update(self):
        super(HistoryPage, self).update()

        wordDict = {}
        games = db.GqlQuery("SELECT * FROM GameRecord WHERE player = :1", api.getPlayer(self.request))
        totalGames = 0
        for game in games:
            totalGames += 1
            for word in game.words:
                wordDict.setdefault(word, 0)
                wordDict[word] += 1
        minCount = min(wordDict.values())
        maxCount = max(wordDict.values())
        spread = maxCount-minCount
        self.model['words'] = [dict(word=word, count=count, size=(1+count-minCount)/spread*100.)
                               for word, count in sorted(wordDict.items())]
        self.model['totalWords'] = len(wordDict)
        self.model['totalGames'] = totalGames


class LabsPage(PageHandler):
    '''A page for new developments that are in beta.'''

    url = '/labs'
    template = templatepath('labs.html')


class FlexPage(PageHandler):
    '''A page to serve the flex app.'''

    url = '/flex'
    template = templatepath('flex.html')


class FacebookLoginPage(PageHandler):

    url = '/facebook/login'

    def update(self):
        uid = self.request.get("uid")
        if uid is not None:
            players = list(db.GqlQuery("SELECT * FROM Player WHERE facebookAccount = :1",uid))
            if len(players) == 0:
                player = model.Player(facebookAccount=uid)
                player.put()
            else:
                player = players[0]
        self.setCookies(player_key=player.key())
        self.redirect("/")
