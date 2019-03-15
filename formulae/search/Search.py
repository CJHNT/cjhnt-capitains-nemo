from flask import current_app, Markup, flash
from flask_babel import _
# This import is only needed for capturing the ES request. I could perhaps comment it out when it is not needed.
from tests.fake_es import FakeElasticsearch
from string import punctuation
import re


PRE_TAGS = "</small><strong>"
POST_TAGS = "</strong><small>"
AGGREGATIONS = {'corpus': {'filters': {'filters': {'NT': {'match': {'_type': 'nt'}},
                                                   'Philo': {'match': {'_type': 'tlg0018'}},
                                                   'LXX': {'match': {'_type': 'tlg0527'}}}}}}


def build_sort_list(sort_str):
    if sort_str == 'urn':
        return 'urn'
    if sort_str == 'urn_desc':
        return [{'urn': {'order': 'desc'}}]


def query_index(index, field, query, page, per_page, sort='urn'):
    if not current_app.elasticsearch:
        return [], 0, {}
    if index in ['', ['']]:
        return [], 0, {}
    query_terms = query.split()
    clauses = []
    sort = build_sort_list(sort)
    for term in query_terms:
        if '*' in term or '?' in term:
            clauses.append({'span_multi': {'match': {'wildcard': {'text': term}}}})
        else:
            clauses.append({"span_term": {'text': term}})
    search = current_app.elasticsearch.search(index=index, doc_type="",
                                              body={'query': {'span_near':
                                                                  {'clauses': clauses,
                                                                   "slop": 0,
                                                                   'in_order': True}
                                                              },
                                                    "sort": sort,
                                                    'from': (page - 1) * per_page,
                                                    'size': per_page,
                                                    'highlight':
                                                        {'fields': {field: {"fragment_size": 300}},
                                                         'pre_tags': [PRE_TAGS],
                                                         'post_tags': [POST_TAGS],
                                                         'encoder': 'html'
                                                         },
                                                    'aggs': AGGREGATIONS
                                                    }
                                              )
    ids = [{'id': hit['_id'], 'info': hit['_source'], 'sents': [Markup(highlight_segment(x, 30, 30, PRE_TAGS, POST_TAGS)) for x in hit['highlight'][field]]} for hit in search['hits']['hits']]
    return ids, search['hits']['total'], search['aggregations']


def suggest_word_search(word, **kwargs):
    """ To enable search-as-you-type for the text search

    :return: sorted set of results
    """
    results = []
    kwargs['fragment_size'] = 1000
    posts, total, aggs = advanced_query_index(q=word, **kwargs)
    for post in posts:
        for sent in post['sents']:
            r = str(sent[sent.find('</small><strong>'):])
            r = r.replace('</small><strong>', '').replace('</strong><small>', '')
            results.append(re.sub(r'[{}]'.format(punctuation), '', r[:min(r.find(' ', len(word) + 30), len(r))]))
            """ind = 0
            while w in r[ind:]:
                i = r.find(w, ind)
                results.append(re.sub(r'[{}]'.format(punctuation), '', r[i:min(r.find(' ', i + len(word) + 30), len(r))]))
                ind = r.find(w, ind) + 1"""
    return sorted(list(set(results)))


def highlight_segment(orig_str, chars_before, chars_after, pre_tag, post_tag):
    """ returns only a section of the highlighting returned by Elasticsearch. This should keep highlighted phrases
        from breaking over lines

    :param orig_str: the original highlight string that should be shortened
    :param chars_before: the number of characters to include before the pre_tag
    :param chars_after: the number of characters to include after the post_tag
    :param pre_tag: the tag(s) that mark the beginning of the highlighted section
    :param post_tag: the tag(s) that mark the end of the highlighted section
    :return: the string to show in the search results
    """
    init_index = 0
    end_index = len(orig_str)
    if orig_str.find(pre_tag) - chars_before > 0:
        init_index = max(orig_str.rfind(' ', 0, orig_str.find(pre_tag) - chars_before), 0)
    if orig_str.rfind(post_tag) + chars_after + len(post_tag) < len(orig_str):
        end_index = min(orig_str.find(' ', orig_str.rfind(post_tag) + chars_after + len(post_tag)), len(orig_str))
    if end_index == -1:
        end_index = len(orig_str)
    return orig_str[init_index:end_index]


def advanced_query_index(corpus=['all'], field="text", q='', page=1, per_page=10, fuzziness='0', phrase_search=False,
                         slop=4, in_order='False', sort='urn', **kwargs):
    # all parts of the query should be appended to the 'must' list. This assumes AND and not OR at the highest level
    old_sort = sort
    sort = build_sort_list(sort)
    body_template = {"query": {"bool": {"must": []}}, "sort": sort,
                     'from': (page - 1) * per_page, 'size': per_page,
                     'aggs': AGGREGATIONS
                     }
    if not current_app.elasticsearch:
        return [], 0, {}
    if field == 'lemmas':
        fuzz = '0'
        if '*' in q or '?' in q:
            flash(_("'Wildcard'-Zeichen (\"*\" and \"?\") sind bei der Lemmasuche nicht möglich."))
            return [], 0, {}
    else:
        fuzz = fuzziness
    if q:
        if field != 'lemmas':
            # Highlighting for lemma searches is transferred to the "text" field.
            body_template['highlight'] = {'fields': {field: {"fragment_size": kwargs['fragment_size'] if 'fragment_size' in kwargs else 1000}},
                                          'pre_tags': [PRE_TAGS],
                                          'post_tags': [POST_TAGS],
                                          'encoder': 'html'
                                          }
        clauses = []
        ordered_terms = True
        if in_order == 'False':
            ordered_terms = False
        for term in q.split():
            if '*' in term or '?' in term:
                clauses.append({'span_multi': {'match': {'wildcard': {field: term}}}})
            else:
                clauses.append({'span_multi': {'match': {'fuzzy': {field: {"value": term, "fuzziness": fuzz}}}}})
        body_template['query']['bool']['must'].append({'span_near': {'clauses': clauses, 'slop': slop,
                                                                     'in_order': ordered_terms}})
    search = current_app.elasticsearch.search(index=corpus, doc_type="", body=body_template)
    if q:
        # The following lines transfer "highlighting" to the text field so that the user sees the text instead of
        # a series of lemmata. The problem is that there is no real highlighting since the text and lemmas fields don't
        # match up 1-to-1.
        if field == 'lemmas':
            ids = []
            for hit in search['hits']['hits']:
                sentences = []
                start = 0
                lems = hit['_source']['lemmas'].split()
                inflected = hit['_source']['text'].split()
                ratio = len(inflected)/len(lems)
                if ' ' in q:
                    addend = 0 if ordered_terms else 1
                    query_words = q.split()
                    for i, w in enumerate(lems):
                        if w == query_words[0] and set(query_words).issubset(lems[max(i - (int(slop) + addend), 0):min(i + (int(slop) + len(query_words)), len(lems))]):
                            rounded = round(i * ratio)
                            sentences.append(' '.join(inflected[max(rounded - 15, 0):min(rounded + 15, len(inflected))]))
                else:
                    while q in lems[start:]:
                        i = lems.index(q, start)
                        start = i + 1
                        rounded = round(i * ratio)
                        sentences.append(' '.join(inflected[max(rounded - 10, 0):min(rounded + 10, len(inflected))]))
                ids.append({'id': hit['_id'], 'info': hit['_source'], 'sents': sentences})
        else:
            ids = [{'id': hit['_id'],
                    'info': hit['_source'],
                    'sents': [Markup(highlight_segment(x, 30, 30, PRE_TAGS, POST_TAGS)) for x in hit['highlight'][field]]} for hit in search['hits']['hits']]
    else:
        ids = [{'id': hit['_id'], 'info': hit['_source'], 'sents': []} for hit in search['hits']['hits']]
    # It may be good to comment this block out when I am not saving requests, though it probably won't affect performance.
    if current_app.config["SAVE_REQUESTS"] and 'autocomplete' not in field:
        req_name = "{corpus}&{field}&{q}&{fuzz}&{in_order}&{slop}&{sort}".format(corpus='+'.join(corpus), field=field,
                                                                                 q=q.replace(' ', '+'), fuzz=fuzziness,
                                                                                 in_order=in_order, slop=slop,
                                                                                 sort=old_sort)
        fake = FakeElasticsearch(req_name, "advanced_search")
        fake.save_request(body_template)
        # Remove the textual parts from the results
        fake.save_ids([{"id": x['id']} for x in ids])
        fake.save_response(search)
    return ids, search['hits']['total'], search['aggregations']
