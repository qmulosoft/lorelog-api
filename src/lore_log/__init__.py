import falcon
import sqlite3
from .users import UsersResource, Login, Profile, Captcha
from .characters import Characters, Character
from .factions import Factions, Faction
from .places import Places, Place
from .things import Things, Thing
from .chronicle import ChronicleEntries, ChronicleEntry
from .utils import JWT_KEY
from falcon_auth import FalconAuthMiddleware, JWTAuthBackend


__version__ = "0.2.0"


class API(falcon.API):
    """ The HTTP REST API for the storage service. """

    def __init__(self, sql_conn: sqlite3.Connection, data_path: str, **kwargs):
        users_resource = UsersResource(sql_conn, data_path)
        auth_backend = JWTAuthBackend(users_resource.validate_claims, JWT_KEY,
                                      required_claims=['exp', 'selected_campaign', 'email'])
        auth_middleware = FalconAuthMiddleware(auth_backend,
                                               exempt_routes=['/users', '/login', '/captcha'],
                                               exempt_methods=['HEAD', 'OPTIONS'])
        super().__init__(middleware=[auth_middleware], **kwargs)
        auth_resource = Login(sql_conn, data_path)
        profile_resource = Profile(sql_conn, data_path)
        captcha_resource = Captcha(sql_conn, data_path)
        characters_resource = Characters(sql_conn, data_path)
        character_resource = Character(sql_conn, data_path)
        factions_resource = Factions(sql_conn, data_path)
        faction_resource = Faction(sql_conn, data_path)
        places_resource = Places(sql_conn, data_path)
        place_resource = Place(sql_conn, data_path)
        things_resource = Things(sql_conn, data_path)
        thing_resource = Thing(sql_conn, data_path)
        entries_resource = ChronicleEntries(sql_conn, data_path)
        entry_resource = ChronicleEntry(sql_conn, data_path)
        self.add_route("/users/", users_resource)
        self.add_route("/login", auth_resource)
        self.add_route("/profile", profile_resource)
        self.add_route("/profile/{profile_id}", profile_resource)
        self.add_route("/profile/campaigns/{campaign_id}", profile_resource)
        self.add_route("/captcha/", captcha_resource)
        self.add_route("/characters/", characters_resource)
        self.add_route("/characters/{character_id}", character_resource)
        self.add_route("/factions/", factions_resource)
        self.add_route("/factions/{faction_id}", faction_resource)
        self.add_route("/places/", places_resource)
        self.add_route("/places/{place_id}", place_resource)
        self.add_route("/things/", things_resource)
        self.add_route("/things/{thing_id}", thing_resource)
        self.add_route("/chronicle/", entries_resource)
        self.add_route("/chronicle/{entry_id}", entry_resource)
