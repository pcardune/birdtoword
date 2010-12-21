from google.appengine.ext import db
from google.appengine.api import users

class JsonModel(db.Model):

    def json(self):
        result = dict(
            key=str(self.key()),
            type=self.__class__.__name__,)

        for key, prop in self.properties().items():
            value = getattr(self, key)
            if isinstance(prop, (db.StringProperty, db.TextProperty, db.BooleanProperty)):
                result[key] = value
            elif isinstance(prop, db.UserProperty):
                result[key] = value.email()
        return result

class Player(JsonModel):
    googleAccount = db.UserProperty(required=False)
    facebookAccount = db.StringProperty()

    @property
    def nickname(self):
        return self.googleAccount.nickname()

    def guessEmail(self):
        if self.googleAccount:
            nick = self.googleAccount.nickname()
            if "@" in nick:
                return nick
            else:
                return "%s@gmail.com" % nick
        return ""

    @property
    def games(self):
        return list(db.GqlQuery("SELECT * FROM GameRecord WHERE player = :1", self))

class GameRecord(JsonModel):
    player = db.ReferenceProperty(Player)
    fromWord = db.StringProperty()
    toWord = db.StringProperty()
    words = db.StringListProperty(unicode)
    times = db.ListProperty(float)

    @property
    def time(self):
        return sum(self.times)

    @property
    def formattedTime(self):
        t = self.time
        if t >= 60:
            return "%i:%im" % (t/60, t%60)
        else:
            return "%.1fs" % t

    @property
    def changes(self):
        return len(self.words)+1

    def json(self):
        return dict(
            fromWord=self.fromWord,
            toWord=self.toWord,
            time=self.formattedTime,
            changes=self.changes)


class GamePath(JsonModel):
    fromWord = db.StringProperty()
    toWord = db.StringProperty()
    length = db.IntegerProperty()
