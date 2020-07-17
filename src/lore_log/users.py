import falcon
from .resource import Resource
from .utils import generate_new_id, JWT_KEY
import sqlite3
import bcrypt
import logging
import jwt
import datetime
from string import ascii_lowercase
from random import choice, randint
import time


class UsersResource(Resource):
    """ Allows for creating new users and provides methods for authenticating """

    def on_post(self, req: falcon.Request, res: falcon.Response):
        if not req.media:
            raise falcon.HTTPBadRequest("Bad or missing user payload")
        user = req.media
        if 'email' not in user or 'alias' not in user or 'password' not in user or 'captcha' not in user \
                or 'code' not in user:
            raise falcon.HTTPBadRequest("Missing fields for user. Requires email, alias, password, captcha, and code")
        captcha = user['captcha']
        if not captcha['id'] or not captcha['answer']:
            raise falcon.HTTPBadRequest("Missing captcha fields. Required id and answer")

        c = self._db.cursor()
        row = c.execute("SELECT [answer] FROM [captcha_tokens] WHERE id = ?", (captcha["id"],)).fetchone()
        if row is None:
            raise falcon.HTTPBadRequest("No captcha with id {} found".format(captcha["id"]))
        c.execute("DELETE FROM [captcha_tokens] WHERE id = ? OR [time] <  date('now', '-1 hour')", (captcha["id"],))
        self._db.commit()
        if row[0] != captcha["answer"]:
            raise falcon.HTTPForbidden("Captcha answer incorrect. Please try again")

        row = c.execute("SELECT [campaign_id] FROM campaign_referral WHERE code=?", (user['code'],)).fetchone()
        if not row:
            raise falcon.HTTPBadRequest("referral code not found")
        campaign_id = row[0]

        hash_pw = bcrypt.hashpw(user['password'].encode(), bcrypt.gensalt())
        new_id = generate_new_id()
        try:
            c.execute("INSERT INTO [user] ([id], [email], [alias], [password]) VALUES (?, ?, ?, ?)",
                      (new_id, user['email'], user['alias'], hash_pw))
        except sqlite3.IntegrityError:
            raise falcon.HTTPBadRequest("Email already exists")
        logging.info("Created new user with email [{}]".format(user['email']))
        # Create an empty profile, to be populated later
        c.execute("INSERT INTO [profile] ([user_id]) VALUES (?)", (new_id,))
        # For now, all new users auto-join the two campaigns until campaign support is added
        c.execute("""
        INSERT INTO [user_campaign_map] ([user_id], [campaign_id]) 
        VALUES (?, ?), (?, ?)""", (new_id, 1, new_id, campaign_id))
        self._db.commit()
        res.status = falcon.HTTP_CREATED

    def get_user_campaigns(self, id) -> dict:
        c = self._db.cursor()
        rows = c.execute("""
                SELECT [id], [name] FROM [campaign] 
                JOIN user_campaign_map ucm on campaign.id = ucm.campaign_id
                WHERE ucm.user_id = ? 
                """, (id,)).fetchall()
        campaigns = {}
        for each in rows:
            campaigns[each[0]] = each[1]
        return campaigns

    def get_jwt(self, id, email, alias, selected_campaign=None):
        campaigns = self.get_user_campaigns(id)
        if selected_campaign is None:
            selected_campaign = tuple(campaigns.keys())[0]
        if selected_campaign not in campaigns:
            raise falcon.HTTPUnauthorized("You do not belong to that campaign")
        return jwt.encode({
            "id": id,
            "email": email,
            "alias": alias,
            "campaigns": campaigns,
            "selected_campaign": selected_campaign,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3)
        }, JWT_KEY)

    def authenticate(self, email: str, password: str) -> bytes:
        c = self._db.cursor()
        row = c.execute("SELECT [id], [password], [alias], [active] FROM [user] WHERE [email] = ?", [email]).fetchone()
        if row is None:
            raise falcon.HTTPUnauthorized("Invalid email or password")
        if not int(row[3]):
            raise falcon.HTTPUnauthorized("User is inactive")
        if not bcrypt.checkpw(password.encode(), row[1]):
            raise falcon.HTTPUnauthorized("Invalid email or password")
        id = row[0]
        alias = row[2]
        return self.get_jwt(id, email, alias)

    def validate_claims(self, claims):
        c = self._db.cursor()
        try:
            result = c.execute("""SELECT [id], [alias], [active] FROM [user] WHERE [id] = ? AND [email] = ?""",
                               (claims["id"], claims["email"])).fetchone()
        except sqlite3.Error:
            # Unauthorized/invalid or unable to authorize at this time
            return None
        id, alias, active = result
        if not active:
            return None
        campaigns = self.get_user_campaigns(id)
        if claims['selected_campaign'] not in campaigns.keys():
            return None
        return {
            'id': id,
            'email': claims['email'],
            'alias': claims['alias'],
            'campaign': claims['selected_campaign']
        }


class Captcha(Resource):
    words = {"arm", "cat", "dog", "god", "kid", "rip", "ten", "sac", "was", "him", "her", "big", "bag", "mop", "sap",
             "sip", "tip", "map", "nap", "yen", "van", "man", "tan", "ban", "can", "car", "bar", "lap", "lip", "rap",
             "gap", "sap", "tap", "zap", "vet", "net", "get", "yet", "pet", "jet", "bet", "art", "ire", "ore", "oar",
             "tar", "zip", "war", "hip", "dim", "raw", "hog", "log", "get", "jar", "dew", "mew", "don", "pop", "pip",
             "ant", "app", "cup", "fit", "far", "fan", "wig", "fur", "tug", "pig", "rig", "gig", "hag", "sag", "sad",
             "wag", "wan", "nag", "fig", "fop", "hop", "mob", "fog", "elf", "fed", "bed", "flu", "new", "cue", "hue",
             "hat", "bat", "sat", "mat", "fat", "rat", "pat", "vat"}

    length = 12

    @staticmethod
    def _overwrite_merge(a: list, b, idx: int):
        for i, char in enumerate(b):
            a[idx + i] = char

    def _try_random_letter(self, i: int, chars: list):
        letter = choice(ascii_lowercase)
        if i > 1 and chars[i - 2] + chars[i - 1] + letter in self.words:
            return self._try_random_letter(i, chars)
        if 0 < i < len(chars)-1:
            if chars[i + 1] and chars[i - 1] + letter + chars[i + 1] in self.words:
                return self._try_random_letter(i, chars)
        if i < len(chars) - 2:
            if chars[i + 1] and chars[i + 2] and letter + chars[i + 1] + chars[i + 2] in self.words:
                return self._try_random_letter(i, chars)
        chars[i] = letter

    def on_post(self, req: falcon.Request, res: falcon.Response):
        id = generate_new_id()
        chars = [None] * self.length
        first_idx = randint(0, self.length-7)
        second_idx = randint(first_idx + 3, self.length-4)
        words = list(self.words)
        first = choice(words)
        second = choice(words)
        self._overwrite_merge(chars, first, first_idx)
        self._overwrite_merge(chars, second, second_idx)
        for i, each in enumerate(chars):
            if not each:
                self._try_random_letter(i, chars)
        c = self._db.cursor()
        c.execute("INSERT INTO [captcha_tokens] ([id], [answer], [time]) VALUES (?, ?, ?)",
                  (id, first+second, time.time()))
        self._db.commit()
        res.media = {
            "id": id,
            "question": "".join(chars)
        }


class Login(UsersResource):

    def on_post(self, req: falcon.Request, res: falcon.Response):
        if not req.media:
            raise falcon.HTTPBadRequest("Bad or missing login payload")
        form = req.media
        if not form['email'] or not form['password']:
            raise falcon.HTTPBadRequest("Missing fields for login. Required email and password")
        jwt = self.authenticate(form['email'], form['password'])
        res.status = falcon.HTTP_OK
        res.media = {"jwt": jwt.decode()}


class Profile(UsersResource):

    def on_get(self, req: falcon.Request, res: falcon.Response, profile_id: str):
        c = self._db.cursor()
        sql_res = c.execute("SELECT [image], [timezone], [status] FROM [profile] WHERE user_id = ?", (profile_id,))
        row = sql_res.fetchone()
        if row is None:
            raise falcon.HTTPNotFound("No profile exists for user")
        profile = {
            "image": row[0],
            "timezone": row[1],
            "status": row[2]
        }
        res.media = profile
        res.status = falcon.HTTP_OK

    def on_patch(self, req: falcon.Request, res: falcon.Response):
        if not req.media:
            raise falcon.HTTPBadRequest("Bad or missing profile payload")
        profile = req.media
        c = self._db.cursor()
        c.execute("UPDATE [profile] SET [status]=?, [timezone]=?, [image]=? WHERE user_id = ?",
                  (profile['status'], profile['timezone'], profile.get('image', None), req.context['user']['id']))
        self._db.commit()
        logging.info("Updated profile for user {}".format(req.context['user']['id']))
        res.media = profile
        res.status = falcon.HTTP_OK

    def on_post(self, req: falcon.Request, res: falcon.Response, campaign_id):
        """ Switch campaigns """
        user = req.context['user']
        res.media = {
            "jwt": self.get_jwt(user['id'], user['email'], user['alias'], int(campaign_id)).decode()
        }
