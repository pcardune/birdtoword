import logging
from google.appengine.ext import db
from facebook import Facebook
from birdtoword.page import filepath, PageHandler
from birdtoword import api

API_KEY = "bd02d19336f0dd5399414f1ef8b6cc9c"
SECRET_KEY = "64c60fe9f312802501d5a455ad194846"

fbAPI = Facebook(API_KEY, SECRET_KEY)

class FacebookPage(PageHandler):

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

    def update(self):
        super(FacebookPage, self).update()

        self.fb = Facebook(API_KEY, SECRET_KEY, auth_token=self.request.get("auth_token"))
        if self.fb.auth_token:
            self.fb.auth.getSession()
        else:
            if self.request.get('fb_sig_in_profile_tab') == '1':
                logging.info("this is a profile page")
                self.fb.session_key = self.request.get('fb_sig_profile_session_key')
                self.fb.uid = self.request.get('fb_sig_profile_user')
            else:
                logging.info("this is an application page")
                self.fb.session_key = self.request.get('fb_sig_session_key')
                self.fb.uid = self.request.get('fb_sig_user')
        self.model['fb'] = self.fb
        self.player = api.getPlayer(self.request, self.fb)
        self.model['player'] = self.player

    def post(self):
        logging.info("request is:\n%s",
                     "\n".join(["%s = %s" % (a, self.request.get(a))
                                for a in self.request.arguments()]))
        return self.get()


class Canvas(FacebookPage):
    '''A simple test page.'''
    url = '/facebook/api/canvas/'

    template = filepath('fbml','canvas.fbml')

    def update(self):
        super(Canvas, self).update()
        self.model['games'] = reversed(list(db.GqlQuery("SELECT * FROM GameRecord WHERE player = :1", self.player)))
        logging.info("fb id is: %s" % self.fb.uid)


class BoxCanvas(FacebookPage):
    url = '/facebook/api/canvas/birdtoword'

    template = filepath('fbml','box.fbml')

    def update(self):
        super(BoxCanvas, self).update()
        self.model['games'] = reversed(list(db.GqlQuery("SELECT * FROM GameRecord WHERE player = :1", self.player)))
        logging.info("fb id is: %s" % self.fb.uid)


class PostAuthorize(FacebookPage):
    url = '/facebook/api/post-authorize'

    def update(self):
        super(PostAuthorize, self).update()


class PostRemove(FacebookPage):
    url = '/facebook/api/post-remove'

    def update(self):
        super(PostRemove, self).update()


class XDReceiver(PageHandler):
    url = '/xd_receiver.htm'
    template = filepath('fbml','xd_receiver.htm')
