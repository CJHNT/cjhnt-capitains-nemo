from flask import current_app
from . import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    project_team = db.Column(db.Boolean, index=True, default=False)
    default_locale = db.Column(db.String(32), index=True, default="de")

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},
                          current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class NtComRels(db.Model):
    """ This maps the relationships from the NT to the Commentaries.
        id is the identifier of the relationship. Having a separate ID will allow two records to refer to the same NT text.
        nt should be a passage-level identifier of an NT text.
        com should be a passage-level identifier of a commentary section.
        These records should be queried whenever an NT text is opened in the commentary view. And it should return a
        list of the commentary sections that comment on this NT passage.
    """
    id = db.Column(db.Integer, primary_key=True)
    nt = db.Column(db.String(256), index=True)
    com = db.Column(db.String(256), index=True)

    def __repr__(self):
        return 'NT: {} --> Commentary: {}'.format(self.nt, self.com)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
