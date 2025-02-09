from MyCapytain.resolvers.capitains.local import XmlCapitainsLocalResolver
from capitains_nautilus.flask_ext import FlaskNautilus
from . import create_app
from .nemo import NemoFormulae

flask_app = create_app()
resolver = XmlCapitainsLocalResolver(flask_app.config['CORPUS_FOLDERS'])
nautilus_api = FlaskNautilus(prefix="/api", resolver=resolver, app=flask_app)

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
    templates={"main": "templates/main",
               "errors": "templates/errors",
               "auth": "templates/auth",
               "search": "templates/search"},
    pdf_folder="pdf_folder/"
)


