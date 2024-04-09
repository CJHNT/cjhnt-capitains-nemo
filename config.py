import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('NEMO_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 10
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LANGUAGES = ['en', 'de', 'fr']
    CORPUS_FOLDERS = os.environ.get('CORPUS_FOLDERS').split(';') if os.environ.get('CORPUS_FOLDERS') else ["/home/matt/results/formulae"]
    SQLALCHEMY_BINDS = {
        'appmeta':      'sqlite:////{}/appmeta.db'.format(CORPUS_FOLDERS[0])
    }
    CACHE_DIRECTORY = os.environ.get('NEMO_CACHE_DIR') or './cache/'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('ADMINS').split(';') if os.environ.get('ADMINS') else ['no-reply@example.com']
    # This should only be changed to True when collecting search queries and responses for mocking ES
    SAVE_REQUESTS = False
    CACHE_MAX_AGE = os.environ.get('VARNISH_MAX_AGE') or 0 # This doesn't need to be set locally.
    TEXT_PARALLELS = os.environ.get('TEXT_PARALLELS') or [os.path.join(x, 'text_parallels.json') for x in CORPUS_FOLDERS]
