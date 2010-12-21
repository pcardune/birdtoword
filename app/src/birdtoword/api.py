import re
import os
import simplejson
import random
import logging

from google.appengine.api import users, mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import RequestHandler
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache

from birdtoword import graph
from birdtoword import model
import logging


def json(func):
    """json decorator that will return json"""
    def wrapped(self, *args, **kwargs):
        self.response.headers['Content-Type'] = 'application/json'
        data = func(self, *args, **kwargs)
        if isinstance(data, model.JsonModel):
            data = data.json()
        self.response.out.write(simplejson.dumps(data))
        wrapped
    return wrapped

def xml(func):
    """xml decorator that will render templates"""
    def wrapped(self, *args, **kwargs):
        self.response.headers['Content-Type'] = 'text/xml'
        templateName, templateData = func(self, *args, **kwargs)
        templatePath = os.path.join(os.path.dirname(__file__), 'xml', templateName)
        self.response.out.write(template.render(templatePath, templateData))
    return wrapped

class GetConnectedWords(RequestHandler):

    url = '/api/words/(.*)/connected'

    @json
    def get(self, word):
        bucket = graph.BUCKETS.get(len(word), {})
        return bucket.get(word, [])

class GetConnectedWordsXML(RequestHandler):

    url = '/api/words/(.*)/connected.xml'

    @xml
    def get(self, word):
        bucket = graph.BUCKETS.get(len(word), {})
        return "connected.xml", dict(connected=bucket.get(word, []))

class GetWordDefinition(RequestHandler):

    url = '/api/words/(.*)/definition'

    def parseDefinition(self, definition):
        types = re.findall(r"\n\s{5}([nv]|adj)\s", definition)
        logging.info(types)
        segments = re.split(r"\n\s{5}(?:[nv]|adj)\s", definition)
        logging.info(segments)
        json = {}
        for i in xrange(len(types)):
            wordType = types[i]
            definitionText = " "*5+segments[i+1]
            json[wordType] = re.split(r"\s{5}[0-9]?:\s",definitionText)[1:]
        return json

    def fetchDefinition(self, word):
        url = "http://services.aonaware.com/DictService/DictService.asmx/DefineInDict?word=%s&dictId=wn" % word
        errors = []
        try:
            response = fetch(url)
            logging.info("%r returned from %r" % (response.status_code, url))
            if response.status_code != 200:
                logging.warn("%r probably isn't a real word.  Dictionary lookup failed with code: %r" % (word, response.status_code))
                json = "No definition found, try searching google."
            elif "<WordDefinition>" in response.content:
                startIndex = response.content.index("<WordDefinition>")+len("<WordDefinition>")
                endIndex = response.content.index("</WordDefinition>")
                json = self.parseDefinition(response.content[startIndex:endIndex])
            else:
                logging.warn("%r probably isn't a real word.  Dictionary lookup failed with code: %r" % (word, response.status_code))
                json = "No definition found, try searching google."
        # XXX: use a proper exception... find out where DownloadError is defined.
        except Exception, e:
            json = "There was an error retrieving the definition.  Wordnet might be down."
            logging.warn("Failed to reach %s" % url)
            errors.append(e)
        return json, errors

    def findDefinition(self, word):
        key = "%s-definition" % word
        json = memcache.get(key)
        if json is None:
            url = "http://services.aonaware.com/DictService/DictService.asmx/DefineInDict?word=%s&dictId=wn" % word
            json, errors = self.fetchDefinition(word)
            if not errors:
                memcache.add(key, json)
        if isinstance(json, str) and word.endswith('s'):
            json = self.findDefinition(word[:-1])
        return json

    @json
    def get(self, word):
        return self.findDefinition(word)

class GetWordDefinitionXml(GetWordDefinition):

    url = '/api/words/(.*)/definition.xml'

    @xml
    def get(self, word):
        data = self.findDefinition(word)
        #data = {"n":"A game about words","v":"to play a game about words"}
        if isinstance(data, str):
            return 'definition-not-found.xml', {"message":data}
        return 'definition.xml', {"definitions":[{"type":t,"definition":d}
                                                for t, d in data.items()]}

class GetEasyGameWords(RequestHandler):

    url = '/api/easy-game-words'

    def getWords(self):
        player = getPlayer(self.request)
        playedGame = random.choice(list(db.GqlQuery("SELECT * FROM GameRecord WHERE player != :1", player)))
        return {'from':playedGame.fromWord,
                'to':playedGame.toWord}

    @json
    def get(self):
        return self.getWords()

class GetEasyGameWordsXML(GetEasyGameWords):

    @xml
    def get(self):
        return "game-words.xml", self.getWords()


class GetGameWords(RequestHandler):

    url = '/api/game-words/([345])'

    def getPath(self, bucket):
        fromWord = random.choice(bucket.keys())

        path = [fromWord]
        segments = random.choice(range(5,20))
        toWord = fromWord
        while len(path) < segments:
            possible = list(set(bucket[toWord]).difference(path))
            if len(possible) == 0:
                #crap, reached a dead end...
                return None
            toWord = random.choice(possible)
            path.append(toWord)
        return path

    def getWords(self, bucketSize):
            bucket = graph.BUCKETS[int(bucketSize)]
            path = self.getPath(bucket)
            count = 0
            while path is None:
                count += 1
                path = self.getPath(bucket)
                logging.info("Ok, trying again: "+str(count))
            logging.info("Got game words: %s" % ' -> '.join(path))

            return {'from':path[0],'to':path[-1]}

    @json
    def get(self, bucketSize):
        return self.getWords(bucketSize)

class GetGameWordsXML(GetGameWords):

    url = '/api/game-words/([345]).xml'

    @xml
    def get(self, bucketSize):
        return 'game-words.xml', self.getWords(bucketSize)

def getPlayer(request, fb=None):
    player = None

    # grab the googleUser from google.
    googleUser = users.get_current_user()
    if googleUser is not None:
        logging.info("Found google user %r", googleUser)
        players = list(db.GqlQuery("SELECT * FROM Player WHERE googleAccount = :1",googleUser))
        if len(players) == 0:
            player = model.Player(googleAccount=googleUser)
            player.put()
        else:
            player = players[0]

    # grab the facebook user.
    else:
        logging.info("trying to get facebook player")
        facebookUid = None
        if fb is None:
            facebookUid = request.cookies.get("facebook-uid")
        elif fb.uid is not None:
            facebookUid = str(fb.uid)
        if facebookUid is not None:
            logging.info("getting facebook player with uid %r", facebookUid)
            players = list(db.GqlQuery("SELECT * FROM Player WHERE facebookAccount = :1",facebookUid))
            if len(players) == 0:
                logging.info("no player found for facebook user %r. Creating one now", facebookUid)
                player = model.Player(facebookAccount=facebookUid)
                player.put()
            else:
                player = players[0]
    logging.info("got player %r", player)
    return player


class SaveGameRecord(RequestHandler):

    url = '/api/save-game'

    @json
    def post(self):
        player = getPlayer(self.request)
        if player is None:
            return

        words = self.request.get("words", allow_multiple=True)
        times = self.request.get("times", allow_multiple=True)

        gameRecord = model.GameRecord(
            player=player,
            fromWord=words[0],
            toWord=words[-1],
            words=words[1:-1],
            times=[float(t) for t in times])
        gameRecord.put()

        return gameRecord

class SendChallenge(RequestHandler):
    url = '/api/challenge/email'

    @json
    def post(self):
        player = getPlayer(self.request)

        if player is None:
            return dict(error=True, errorMessage="You must be logged in to send challenges.")

        toEmail = self.request.get('to')
        fromEmail = self.request.get('from')
        message = self.request.get('message')

        if not fromEmail:
            return dict(error=True, errorMessage="You must provide a 'From:' email address")
        if not mail.is_email_valid(fromEmail):
            return dict(error=True, errorMessage="'%s' is not a valid email address"%fromEmail)
        if not toEmail:
            return dict(error=True, errorMessage="You must provide a 'To:' email address")
        if not mail.is_email_valid(toEmail):
            return dict(error=True, errorMessage="'%s' is not a valid email address"%toEmail)

        mail.send_mail(fromEmail, toEmail, "You have been challenged!", message)

        logging.info("Sending challenge from %s to %s with message %r", toEmail, fromEmail, message)
        return {'error':False,
                'from':fromEmail,
                'to':toEmail,
                'message':message}
