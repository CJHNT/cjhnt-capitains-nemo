from flask import Flask, request, session
from MyCapytain.resources.prototypes.cts.inventory import CtsTextInventoryCollection, CtsTextInventoryMetadata
from MyCapytain.resolvers.utils import CollectionDispatcher
from capitains_nautilus.cts.resolver import NautilusCTSResolver
from capitains_nautilus.flask_ext import FlaskNautilus
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from elasticsearch import Elasticsearch
from flask_bootstrap import Bootstrap
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from werkzeug.contrib.cache import FileSystemCache

general_collection = CtsTextInventoryCollection()
formulae = CtsTextInventoryMetadata('formulae_collection', parent=general_collection)
formulae.set_label('Formulae', 'lat')
chartae = CtsTextInventoryMetadata('chartae_collection', parent=general_collection)
chartae.set_label('Chartae', 'lat')
elexicon = CtsTextInventoryMetadata('eLexicon_entries', parent=general_collection)
elexicon.set_label('E-Lexikon', 'lat')
organizer = CollectionDispatcher(general_collection, default_inventory_name='chartae_collection')

@organizer.inventory("formulae_collection")
def organize_formulae(collection, path=None, **kwargs):
    if collection.id.startswith('urn:cts:formulae:andecavensis'):
        return True
    return False

@organizer.inventory("eLexicon_entries")
def organize_elexicon(collection, path=None, **kwargs):
    if collection.id.startswith('urn:cts:formulae:elexicon'):
        return True
    return False

flask_app = Flask("Flask Application for Nemo")
flask_app.config.from_object(Config)
db = SQLAlchemy(flask_app)
login = LoginManager(flask_app)
login.login_view = '.r_login'
login.login_message = _l("Please log in to access this page.")
migrate = Migrate(flask_app, db)
flask_app.elasticsearch = Elasticsearch(flask_app.config['ELASTICSEARCH_URL']) \
    if flask_app.config['ELASTICSEARCH_URL'] else None
bootstrap = Bootstrap(flask_app)
babel = Babel(flask_app, default_locale='de')
resolver = NautilusCTSResolver(flask_app.config['CORPUS_FOLDERS'], dispatcher=organizer, cache=FileSystemCache('./cache/'))

@babel.localeselector
def get_locale():
    if 'locale' in session:
        return session['locale']
    if current_user.is_authenticated and current_user.default_locale:
        return current_user.default_locale
    return request.accept_languages.best_match(flask_app.config['LANGUAGES'])

from formulae import models

nautilus_api = FlaskNautilus(prefix="/api", resolver=resolver, app=flask_app)

from .nemo import NemoFormulae

nemo = NemoFormulae(
    name="InstanceNemo",
    app=flask_app,
    resolver=resolver,
    base_url="",
    css=["assets/css/theme.css"],
    js=["assets/js/empty.js"],
    static_folder="./assets/",
    transform={"default": "components/epidoc.xsl",
               "notes": "components/extract_notes.xsl"},
    templates={"main": "templates/main"},
    pdf_folder="pdf_folder/"
)


