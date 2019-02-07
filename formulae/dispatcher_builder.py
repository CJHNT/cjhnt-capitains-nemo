from MyCapytain.resources.prototypes.cts.inventory import CtsTextInventoryCollection, CtsTextInventoryMetadata
from MyCapytain.resolvers.utils import CollectionDispatcher

general_collection = CtsTextInventoryCollection()
formulae = CtsTextInventoryMetadata('new_testament', parent=general_collection)
formulae.set_label('Neues Testament', 'ger')
formulae.set_label('New Testament', 'eng')
formulae.set_label('Formulae', 'fre')
chartae = CtsTextInventoryMetadata('jewish_texts', parent=general_collection)
chartae.set_label('Jüdische Texte', 'ger')
chartae.set_label('Jewish Texts', 'eng')
chartae.set_label('Autres Textes', 'fre')
elexicon = CtsTextInventoryMetadata('commentaries', parent=general_collection)
elexicon.set_label('Kommentare', 'ger')
elexicon.set_label('Commentaries', 'eng')
elexicon.set_label('Lexique', 'fre')
organizer = CollectionDispatcher(general_collection, default_inventory_name='jewish_texts')

@organizer.inventory("new_testament")
def organize_formulae(collection, path=None, **kwargs):
    if collection.id.startswith('urn:cts:cjhnt:nt'):
        return True
    return False

@organizer.inventory("commentaries")
def organize_elexicon(collection, path=None, **kwargs):
    if collection.id.startswith('urn:cts:cjhnt:commentary'):
        return True
    return False
