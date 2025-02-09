from flask import url_for, Markup, g, session, flash, request, abort, send_from_directory
from flask_login import current_user, login_required
from flask_babel import _, refresh, get_locale
from flask_babel import lazy_gettext as _l
from werkzeug.utils import redirect
from flask_nemo import Nemo, filters
from rdflib.namespace import DCTERMS, DC, Namespace
from MyCapytain.common.constants import Mimetypes
from MyCapytain.resources.collections.capitains import XmlCapitainsReadableMetadata, XmlCapitainsCollectionMetadata
from MyCapytain.errors import UnknownCollection
from formulae.search.forms import SearchForm
from lxml import etree
from typing import List, Tuple, Union, Match, Dict, Any, Sequence, Callable
from .errors.handlers import e_internal_error, e_not_found_error, e_unknown_collection_error
import re
from datetime import date
from urllib.parse import quote
from string import punctuation
from .models import NtComRels
from operator import itemgetter
from json import load as json_load, JSONDecodeError


class NemoFormulae(Nemo):

    ROUTES = [
        ("/", "r_index", ["GET"]),
        ("/collections", "r_collections", ["GET"]),
        ("/collections/<objectId>", "r_collection", ["GET"]),
        ("/work/<objectId>", "r_work", ["GET"]),
        ("/text/<objectId>/references", "r_references", ["GET"]),
        ("/texts/<objectIds>/passage/<subreferences>", "r_multipassage", ["GET"]),
        ("/add_collections/<objectIds>/<reffs>", "r_add_text_collections", ["GET"]),
        ("/add_collection/<objectId>/<objectIds>/<reffs>", "r_add_text_collection", ["GET"]),
        ("/add_text/<objectId>/<objectIds>/<reffs>", "r_add_text_work", ["GET"]),
        ("/lang", "r_set_language", ["GET", "POST"]),
        # ("/sub_elements/<coll>/<objectIds>/<reffs>", "r_add_sub_elements", ["GET"]),
        # ("/sub_elements/<coll>", "r_get_sub_elements", ["GET"]),
        ("/imprint", "r_impressum", ["GET"]),
        ("/nt_com/<objectIds>/passage/<subreferences>", "r_commentary_view", ['GET']),
        ("/text/<objectId>/passage", "r_first_passage", ["GET"]),
        ("/snippet/<objectId>/subreference/<subreference>", "r_get_snippet", ["GET"]),
        ("/related/<objectIds>", "r_get_related_texts", ["GET"])
    ]
    SEMANTIC_ROUTES = [
        "r_collection", "r_references", "r_multipassage"
    ]

    FILTERS = [
        "f_formatting_passage_reference",
        "f_i18n_iso",
        "f_order_resource_by_lang",
        "f_hierarchical_passages",
        "f_is_str",
        "f_i18n_citation_type",
        "f_slugify",
        "f_make_members"
    ]

    CACHED = [
        # Routes
        "r_index", # "r_collection", "r_collections", "r_references", "r_assets", "r_multipassage",
        # Controllers
        "get_inventory", "get_collection", "get_reffs", "get_passage", "get_siblings", "get_all_corpora",
        # Translater
        "semantic", "make_coins", "expose_ancestors_or_children", "make_members", "transform",
        # Business logic
        # "view_maker", "route", #"render",
    ]

    OPEN_NOTES = []

    LANGUAGE_MAPPING = {"lat": _l('Latein'), "deu": _l("Deutsch"), "fre": _l("Französisch"),
                        "eng": _l("Englisch"), "grc": _l("Griechisch"), "mul": _l("Verschiedene")}

    BIBO = Namespace('http://bibliotek-o.org/1.0/ontology/')

    def __init__(self, *args, **kwargs):
        if "pdf_folder" in kwargs:
            self.pdf_folder = kwargs["pdf_folder"]
            del kwargs["pdf_folder"]
        super(NemoFormulae, self).__init__(*args, **kwargs)
        self.sub_colls = self.get_all_corpora()
        self.app.jinja_env.filters["remove_from_list"] = self.f_remove_from_list
        self.app.jinja_env.filters["join_list_values"] = self.f_join_list_values
        self.app.jinja_env.filters["replace_indexed_item"] = self.f_replace_indexed_item
        self.app.register_error_handler(404, e_not_found_error)
        self.app.register_error_handler(500, e_internal_error)
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        self.parallel_texts = self.load_external_json('TEXT_PARALLELS')
        self.nt_commentary_sections = self.load_external_json('NT_COMMENTARY_SECTIONS')
    
    def load_external_json(self, config_var: str) -> dict:
        """ Ingests an existing JSON file that contains notes about specific manuscript transcriptions"""
        for j in self.app.config[config_var]:
            with open(j) as f:
                try:
                    json_dict = json_load(f)
                except JSONDecodeError:
                    self.app.logger.warning(j + ' is not a valid JSON file. Unable to load valid collected collections from it.')
                    continue
        return json_dict

    def get_all_corpora(self):
        """ A convenience function to return all sub-corpora in all collections

        :return: dictionary with all the collections as keys and a list of the corpora in the collection as values
        """
        colls = {}
        for member in self.make_members(self.resolver.getMetadata(), lang=None):
            members = self.make_members(self.resolver.getMetadata(member['id']))
            for m in members:
                m.update({'short_title':
                              str(self.resolver.getMetadata(m['id']).metadata.get_single(self.BIBO.AbbreviatedTitle))})
            colls[member['id']] = members
        return colls

    def check_project_team(self):
        """ A convenience function that checks if the current user is a part of the project team"""
        try:
            return current_user.project_team is True
        except AttributeError:
            return False

    def create_blueprint(self):
        """ Enhance original blueprint creation with error handling

        :rtype: flask.Blueprint
        """
        blueprint = super(NemoFormulae, self).create_blueprint()
        blueprint.register_error_handler(UnknownCollection, e_unknown_collection_error)
        # blueprint.register_error_handler(500, self.e_internal_error)
        # blueprint.register_error_handler(404, self.e_not_found_error)
        return blueprint

    def get_locale(self):
        """ Retrieve the best matching locale using request headers

        .. note:: Probably one of the thing to enhance quickly.

        :rtype: str
        """
        best_match = str(get_locale())
        lang = self.__default_lang__
        if best_match == "de":
            lang = "ger"
        elif best_match == "fr":
            lang = "fre"
        elif best_match == "en":
            lang = "eng"
        return lang

    def f_remove_from_list(self, l, i):
        """ remove item "i" from list "l"

        :param l: the list
        :param i: the item
        :return: the list without the item
        """
        l.remove(i)
        return l

    def f_join_list_values(self, l, s):
        """ join the values of "l" user the separator "s"

        :param l: the list of values
        :param s: the separator
        :return: a string of the values joined by the separator
        """
        return s.join(l).strip(s)

    def f_replace_indexed_item(self, l, i, v):
        """

        :param l: the list of values
        :param i: the index to be replace
        :param v: the value with which the indexed value will be replaced
        :return: new list
        """
        l[i] = v
        return l

    def r_set_language(self, code):
        """ Sets the seseion's language code which will be used for all requests

        :param code: The 2-letter language code
        :type code: str
        """
        session['locale'] = code
        refresh()

    def before_request(self):
        g.search_form = SearchForm()

    def after_request(self, response):
        """ Currently used only for the Cache-Control header
            max_age calculates days, hours, minutes and seconds and adds them together.
            First number after '+' is the respective number for each value.
        """
        response.cache_control.max_age = self.app.config['CACHE_MAX_AGE']
        response.cache_control.public = True
        return response

    def semantic(self, collection: Union[XmlCapitainsCollectionMetadata, XmlCapitainsReadableMetadata],
                 parent: XmlCapitainsCollectionMetadata = None) -> str:
        """ Generates a SEO friendly string for given collection

        :param collection: Collection object to generate string for
        :param parent: Current collection parent
        :return: SEO/URL Friendly string
         """
        # The order of the ancestors isn't kept in MyCap v3 (ancestors is a dictionary)
        #  So the reversing of the list of parent values probably doesn't make much sense here.
        if parent is not None:
            collections = list(parent.ancestors.values())[::-1] + [parent, collection]
        else:
            collections = list(collection.ancestors.values())[::-1] + [collection]

        return filters.slugify("--".join([item.get_label() for item in collections if item.get_label()]))

    def make_coins(self, collection: Union[XmlCapitainsCollectionMetadata, XmlCapitainsReadableMetadata],
                   text: XmlCapitainsReadableMetadata, subreference: str = "", lang: str = None) -> str:
        """ Creates a CoINS Title string from information

        :param collection: Collection to create coins from
        :param text: Text/Passage object
        :param subreference: Subreference
        :param lang: Locale information
        :return: Coins HTML title value
        """
        if lang is None:
            lang = self.__default_lang__
        return "url_ver=Z39.88-2004" \
               "&ctx_ver=Z39.88-2004" \
               "&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook" \
               "&rft_id={cid}" \
               "&rft.genre=bookitem" \
               "&rft.btitle={title}" \
               "&rft.edition={edition}"\
               "&rft.au={author}" \
               "&rft.atitle={pages}" \
               "&rft.language={language}" \
               "&rft.pages={pages}".format(
                    title=quote(str(text.get_title(lang))), author=quote(str(text.get_creator(lang))),
                    cid=url_for("InstanceNemo.r_collection", objectId=collection.id, _external=True),
                    language=collection.lang, pages=quote(subreference), edition=quote(str(text.get_description(lang)))
                 )

    @staticmethod
    def sort_parents(d: Dict[str, Union[str, int]]) -> int:
        """ Sort parents from closest to furthest

        :param d: The dictionary to be sorted
        :return: integer representing how deep in the collection a collection stands from lowest (i.e., text) to highest
        """
        return 10 - len(d['ancestors'])

    @staticmethod
    def sort_sigla(x: str) -> list:
        sorting_groups = list(re.search(r'(\D+)(\d+)?(\D+)?', x).groups(default=0))
        sorting_groups[1] = int(sorting_groups[1])
        return sorting_groups

    def make_parents(self, collection: Union[XmlCapitainsCollectionMetadata, XmlCapitainsReadableMetadata],
                     lang: str=None) -> List[Dict[str, Union[str, int]]]:
        """ Build parents list for given collection

        :param collection: Collection to build dict view of for its members
        :param lang: Language to express data in
        :return: List of basic objects
        """
        parents = [
            {
                "id": member.id,
                "label": str(member.metadata.get_single(DC.title)),
                "model": str(member.model),
                "type": str(member.type),
                "size": member.size,
                "subtype": member.subtype,
                "ancestors": member.ancestors,
                "short_title": str(member.metadata.get_single(self.BIBO.AbbreviatedTitle))
            }
            for member in collection.ancestors.values()
            if member.get_label()
        ]
        parents = sorted(parents, key=self.sort_parents)
        return parents

    def r_assets(self, filetype, asset):
        """ Route for specific assets.

        :param filetype: Asset Type
        :param asset: Filename of an asset
        :return: Response
        """
        if filetype in self.assets and asset in self.assets[filetype] and self.assets[filetype][asset]:
            return send_from_directory(
                directory=self.assets[filetype][asset],
                path=asset
            )
        abort(404)

    @login_required
    def r_collections(self, lang=None):
        data = super(NemoFormulae, self).r_collections(lang=lang)
        return data
    
    @login_required
    def r_collection(self, objectId, lang=None):
        data = super(NemoFormulae, self).r_collection(objectId, lang=lang)
        data['interface'] = request.args.get('interface')
        new_members = []
        for member in sorted(data['collections']['members'], key=itemgetter('id')):
            md = self.resolver.getMetadata(member['id'])
            member['readable'] = md.readable
            new_members.append([member, self.make_members(self.resolver.getMetadata(member['id']), lang=lang)])
        data['collections']['members'] = new_members
        return data

    @login_required
    def r_work(self, objectId, lang=None):
        """ Route to browse collections and add another text to the view

        :param objectId: Collection identifier
        :type objectId: str
        :param lang: Lang in which to express main data
        :type lang: str
        :return: Template and collections contained in given collection
        :rtype: [(str, list)]
        """
        collection = self.resolver.getMetadata(objectId)
        reffs = self.resolver.getReffs(objectId)
        r = list()
        for reff in reffs:
            try:
                r.append((str(reff), [str(x) for x in self.resolver.getReffs(objectId, subreference=str(reff))]))
            except:
                r.append((str(reff), []))
        return {
            "template": "main::sub_collection.html",
            "collections": {
                "current": {
                    "label": str(collection.get_label(lang)),
                    "id": collection.id,
                    "model": str(collection.model),
                    "type": str(collection.type),
                    "open_regesten": True
                },
                "readable": r,
                "parents": self.make_parents(collection, lang=lang)
            },
            'interface': request.args.get('interface')
        }

    @login_required
    def r_add_text_collections(self, objectIds, reffs, lang=None):
        """ Retrieve the top collections of the inventory

        :param lang: Lang in which to express main data
        :type lang: str
        :return: Collections information and template
        :rtype: {str: Any}
        """
        collection = self.resolver.getMetadata()
        return {
            "template": "main::collection.html",
            "current_label": collection.get_label(lang),
            "collections": {
                "members": [[member, self.make_members(self.resolver.getMetadata(member['id']), lang=lang)] for member in self.make_members(collection, lang=lang)]
            },
            "prev_texts": objectIds,
            "prev_reffs": reffs
        }

    @login_required
    def r_add_text_collection(self, objectId, objectIds, reffs, lang=None):
        """ Route to browse a top-level collection and add another text to the view

        :param objectId: Collection identifier
        :type objectId: str
        :param lang: Lang in which to express main data
        :type lang: str
        :return: Template and collections contained in given collection
        :rtype: {str: Any}
        """
        d = self.r_collection(objectId, lang=lang)
        d['prev_texts'] = objectIds
        d['prev_reffs'] = reffs
        d['interface'] = 'reading'
        """
        if self.check_project_team() is False:
            members = [x for x in members if x['id'] in self.OPEN_COLLECTIONS]
        if len(members) == 1:
            return redirect(url_for('.r_add_text_corpus', objectId=members[0]['id'],
                                    objectIds=objectIds, reffs=reffs, lang=lang))
        elif len(members) == 0:
            flash(_('Diese Sammlung steht unter Copyright und darf hier nicht gezeigt werden.'))"""
        return d

    @login_required
    def r_add_text_work(self, objectId, objectIds, reffs, lang=None):
        """ Route to browse collections and add another text to the view

        :param objectId: Collection identifier
        :type objectId: str
        :param lang: Lang in which to express main data
        :type lang: str
        :return: Template and collections contained in given collection
        :rtype: {str: Any}
        """
        initial = self.r_work(objectId, lang=lang)
        initial.update({'prev_texts': objectIds, 'prev_reffs': reffs, 'interface': 'reading'})
        return initial

    @login_required
    def get_first_passage(self, objectId):
        """ Provides a redirect to the first passage of given objectId

        :param objectId: Collection identifier
        :type objectId: str
        :return: Redirection to the first passage of given text
        """
        collection, reffs = self.get_reffs(objectId=objectId, export_collection=True)
        first, _ = reffs[0]
        return str(first)

    def r_passage(self, objectId, subreference, lang=None):
        """ Retrieve the text of the passage

        :param objectId: Collection identifier
        :type objectId: str
        :param lang: Lang in which to express main data
        :type lang: str
        :param subreference: Reference identifier
        :type subreference: str
        :return: Template, collections metadata and Markup object representing the text
        :rtype: {str: Any}
        """
        # pdf_path = ''
        collection = self.get_collection(objectId)
        if isinstance(collection, XmlCapitainsCollectionMetadata):
            editions = [t for t in collection.children.values() if isinstance(t, XmlCapitainsReadableMetadata) and 'cts:edition' in t.subtype]
            if len(editions) == 0:
                raise UnknownCollection('{}.{}'.format(collection.get_label(lang), subreference) + _l(' wurde nicht gefunden.'))
            objectId = editions[0].id
            collection = self.get_collection(objectId)
        try:
            text = self.get_passage(objectId=objectId, subreference=subreference)
        except IndexError:
            new_subref = self.get_reffs(objectId)[0][0]
            text = self.get_passage(objectId=objectId, subreference=new_subref)
            flash('{}.{}'.format(collection.get_label(lang), subreference) + _l(' wurde nicht gefunden. Der ganze Text wird angezeigt.'))
            subreference = new_subref
        passage = self.transform(text, text.export(Mimetypes.PYTHON.ETREE), objectId)
        passage = passage.replace('span><span', 'span> <span')
        if 'cjhnt:nt' in objectId:
            passage = self.nt_commentary_link(objectId, subreference, passage)
        if 'notes' in self._transform:
            notes = self.extract_notes(passage)
        else:
            notes = ''
        prev, next = self.get_siblings(objectId, subreference, text)
        text_parallels = list()
        if objectId in self.parallel_texts and subreference in self.parallel_texts[objectId]:
            for p in self.parallel_texts[objectId][subreference]:
                text_parallels.append((p[0], p[1], ' '.join([str(self.get_collection(p[0]).metadata.get_single(DC.title, lang=lang)), p[1]])))
        # if current_user.project_team is False and str(text.get_creator(lang)) not in self.OPEN_COLLECTIONS:
        #     pdf_path = self.pdf_folder + objectId.split(':')[-1] + '.pdf'
        return {
            "template": "main::text.html",
            "objectId": objectId,
            "subreference": subreference,
            "collections": {
                "current": {
                    "label": collection.get_label(lang),
                    "id": collection.id,
                    "model": str(collection.model),
                    "type": str(collection.type),
                    "author": text.get_creator(lang),
                    "title": text.get_title(lang),
                    "description": text.get_description(lang),
                    "citation": collection.citation,
                    "coins": self.make_coins(collection, text, subreference, lang=lang),
                    'lang': collection.lang,
                    'parallels': text_parallels
                },
                "parents": self.make_parents(collection, lang=lang)
            },
            "text_passage": Markup(passage),
            "notes": Markup(notes),
            "prev": prev,
            "next": next,
            "open_regest": True,
            "show_notes": True,
            "date": "{:04}-{:02}-{:02}".format(date.today().year, date.today().month, date.today().day)
        }

    @login_required
    def r_multipassage(self, objectIds, subreferences, lang=None, result_sents=''):
        """ Retrieve the text of the passage

        :param objectIds: Collection identifiers separated by '+'
        :type objectIds: str
        :param lang: Lang in which to express main data
        :type lang: str
        :param subreferences: Reference identifiers separated by '+'
        :type subreferences: str
        :param result_sents: The list of sentences from elasticsearch results
        :type result_sents: str
        :return: Template, collections metadata and Markup object representing the text
        :rtype: {str: Any}
        """
        ids = objectIds.split('+')
        translations = {}
        for i in ids:
            p = self.resolver.getMetadata(self.make_parents(self.resolver.getMetadata(i))[0]['id'])
            translations[i] = [v for k, v in p.readableDescendants.items() if k not in ids]
        passage_data = {'template': 'main::multipassage.html', 'objects': [], "translation": translations}
        subrefers = subreferences.split('+')
        result_sents = request.args.get('result_sents')
        for i, id in enumerate(ids):
            if subrefers[i] in ["all", 'first']:
                subref = self.get_reffs(id)[0][0]
            else:
                subref = subrefers[i]
            d = self.r_passage(id, subref, lang=lang)
            del d['template']
            if result_sents:
                d['text_passage'] = self.highlight_found_sents(d['text_passage'],
                                                               self.convert_result_sents(result_sents))
            passage_data['objects'].append(d)
        if len(ids) > len(passage_data['objects']):
            flash(_('Mindestens ein Text, den Sie anzeigen möchten, ist nicht verfügbar.'))
        return passage_data

    def nt_commentary_link(self, objectId: str, subreference: str, passage:str):
        """ Mark up the NT passages with their links to the commentaries
        """
        sub_ref_parts = subreference.split('.')
        passage_xml = etree.XML(passage)
        if len(sub_ref_parts) == 2:
            for w_num, comm_passages in self.nt_commentary_sections[objectId][sub_ref_parts[0]][sub_ref_parts[1]].items():
                if comm_passages:
                    xml_word = passage_xml.xpath('//span[@wordnum="{}"]'.format(w_num))[0]
                    xml_word.set('class', xml_word.get('class') + ' commentary-word')
                    xml_word.set('comm-passages', '%'.join([';'.join(x) for x in comm_passages]))
                    # xml_word.set('data-content', '%'.join([';'.join(x) for x in comm_passages]))
                    xml_word.set('data-container', 'body')
                    xml_word.set('data-toggle', 'popover')
                    xml_word.set('data-placement', 'bottom')
                    xml_word.set('title', 'Passages related to this word')
                    xml_word.set('data-trigger', 'focus')
                    xml_word.set('tabindex', '0')
        return Markup(etree.tostring(passage_xml, pretty_print=True, encoding=str))
    
    @login_required
    def r_commentary_view(self, objectIds, subreferences, lang=None, result_sents=''):
        """ Retrieve the appropriate NT passage as well as the commentary section(s) that go with it

        :param nt_book: the id of the NT book
        :type nt_book: str
        :param lang: Lang in which to express main data
        :type lang: str
        :param subreference: portion (e.g., chapter.verse) of the NT book
        :type subreference: str
        :param result_sents: The list of sentences from elasticsearch results
        :type result_sents: str
        :return: Template, collections metadata and Markup object representing the text
        :rtype: {str: Any}
        """
        def split_comms(com):
            ident = ':'.join(com.split(':')[:-1]).replace('greekLit', 'cjhnt')
            ref = com.split(':')[-1]
            return {'id': ident, 'ref': ref}

        comms = [split_comms(x.com) for x in NtComRels.query.filter_by(nt=objectIds + ':' + subreferences).all()]
        passage_data = {'template': 'main::commentary_view.html', 'comm_sections': [], "nt": self.r_passage(objectIds,
                                                                                                            subreferences,
                                                                                                            lang=lang)}
        for com in comms:
            d = self.r_passage(com['id'], com['ref'], lang=lang)
            del d['template']
            passage_data['comm_sections'].append(d)
        return passage_data
    
    @login_required
    def r_get_snippet(self, objectId: str, subreference: str):
        data = self.r_passage(objectId=objectId, subreference=subreference)
        data['template'] = 'main::source_collapse.html'
        translation_id = re.sub(r'grc(?=\d+)', 'eng', objectId)
        if translation_id != objectId:
            try:
                translation_data = self.r_passage(objectId=re.sub(r'grc(?=\d+)', 'eng', objectId), subreference=subreference)
                data['translation_passage'] = translation_data['text_passage']
            except:
                data["translation_passage"] = ''
        else:
            data["translation_passage"] = ''
        if 'cjhnt:nt' in objectId:
            data['template'] = 'main::commentary_nt.html'
            if request.args.get('words', None):
                passage_xml = etree.XML(data['text_passage'])
                word_range = [int(x) for x in request.args.get('words').split('-')]
                if len(word_range) == 2:
                    word_range = range(word_range[0], word_range[1] + 1)
                for word in passage_xml.xpath('//span[@class="w"]'):
                    if int(word.get('wordnum')) in word_range:
                        word.set('class', word.get('class') + ' cited-word')
                data['text_passage'] = Markup(etree.tostring(passage_xml, pretty_print=True, encoding=str))
        if request.args.get('source') == 'ntPassage':
            data['template'] = 'main::commentary_popover.html'
        return data
    
    @login_required
    def r_get_related_texts(self, objectIds: str):
        """ Return snippets of all commentary and early Jewish texts that are somehow related to an NT word
        """
        referring_text_refs = re.search(r'.*texts/(.*)/passage/([\d\w\.\-\+]+).*', request.referrer)
        passages = {'commentaries': [], 'ancient': [], 'template': 'main::commentary_popover.html'}
        for urn_reference in objectIds.split('%'):
            objectId, subreference = urn_reference.split(';')
            data = self.r_passage(objectId=objectId, subreference=subreference)
            passage_xml = etree.XML(data['text_passage'])
            if 'commentary' in objectId:
                header = passage_xml.xpath('//*[@class="cjh-Überschrift-2" or @class="cjh-Überschrift-1"]/text()')[0]
                passages['commentaries'].append({'title': data['collections']['current']['label'], 'header': header, 'subref': subreference, 'all_texts': '+'.join([referring_text_refs[1], objectId]), 'all_reffs': '+'.join([referring_text_refs[2], subreference])})
            else:
                print(etree.tostring(passage_xml))
                header = ''.join(passage_xml.xpath('//text()'))
                if len(header.split()) > 5:
                    header = ' '.join(header.split()[:6]) + '...'
                passages['ancient'].append({'title': data['collections']['current']['label'], 'header': header, 'subref': subreference, 'all_texts': '+'.join([referring_text_refs[1], objectId]), 'all_reffs': '+'.join([referring_text_refs[2], subreference])})
        return passages

    def convert_result_sents(self, sents):
        """ Remove extraneous markup and punctuation from the result_sents returned from the search page

        :param sents: the original 'result_sents' request argument
        :return: list of the individual sents with extraneous markup and punctuation removed
        """
        intermediate = sents.replace('+', ' ').replace('%2C', '').replace('%2F', '').replace('%24', '$')
        intermediate = re.sub('strong|small', '', intermediate)
        intermediate = re.sub('\s+', ' ', intermediate)
        intermediate = intermediate.split('$')
        return [re.sub('[{}„“…]'.format(punctuation), '', x) for x in intermediate]

    def highlight_found_sents(self, html, sents):
        """ Adds "searched" to the classList of words in "sents" from elasticsearch results

        :param html: the marked-up text to be searched
        :param sents: list of the "sents" strings
        :return: transformed html
        """
        root = etree.fromstring(html)
        spans = root.xpath('//span[contains(@class, "w")]')
        texts = [re.sub('[{}„“…]'.format(punctuation), '', re.sub(r'&[lg]t;', '', x.text)) for x in spans if re.sub('[{}„“…]'.format(punctuation), '', x.text) != '']
        for sent in sents:
            words = sent.split()
            for i in range(len(spans)):
                if words == texts[i:i + len(words)]:
                    spans[i].set('class', spans[i].get('class') + ' searched-start')
                    spans[i + len(words) - 1].set('class', spans[i + len(words) - 1].get('class') + ' searched-end')
                    for span in spans[i:i + len(words)]:
                        if span.getparent().index(span) == 0 and 'searched-start' not in span.get('class'):
                            span.set('class', span.get('class') + ' searched-start')
                        if span == span.getparent().findall('span')[-1] and 'searched-end' not in span.get('class'):
                            span.set('class', span.get('class') + ' searched-end')
                    break
        xml_string = etree.tostring(root, encoding=str, method='html', xml_declaration=None, pretty_print=False,
                                    with_tail=True, standalone=None)
        span_pattern = re.compile(r'(<span class="w \w*\s?searched-start.*?searched-end".*?</span>)', re.DOTALL)
        xml_string = re.sub(span_pattern, r'<span class="searched">\1</span>', xml_string)
        return Markup(xml_string)

    def r_impressum(self):
        """ Impressum route function

        :return: Template to use for Impressum page
        :rtype: {str: str}
        """
        return {"template": "main::impressum.html"}

    def extract_notes(self, text):
        """ Constructs a dictionary that contains all notes with their ids. This will allow the notes to be
        rendered anywhere on the page and not only where they occur in the text.

        :param text: the string to be transformed
        :return: dict('note_id': 'note_content')
        """
        with open(self._transform['notes']) as f:
            xslt = etree.XSLT(etree.parse(f))

        return str(xslt(etree.fromstring(text)))

    ''' I may add these back in later.
    def r_add_sub_elements(self, coll, objectIds, reffs, lang=None):
        """ A convenience function to return all sub-corpora in all collections

        :return: dictionary with all the collections as keys and a list of the corpora in the collection as values
        """
        texts = self.r_add_text_collection(coll, objectIds, reffs, lang=lang)
        texts["template"] = 'main::sub_element_snippet.html'
        return texts

    def r_get_sub_elements(self, coll, objectIds='', reffs='', lang=None):
        """ A convenience function to return all sub-corpora in all collections

        :return: dictionary with all the collections as keys and a list of the corpora in the collection as values
        """
        texts = self.r_add_text_collection(coll, objectIds, reffs, lang=lang)
        texts["template"] = 'main::sub_element_snippet.html'
        return texts
        '''
