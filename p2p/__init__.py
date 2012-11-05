'''
Python wrapper for the Content Services API

'''
import requests
import json
import iso8601
from iso8601.iso8601 import ISO8601_REGEX
from dateutil.parser import parse
import re
import time
import sys
import math
from datetime import datetime

from cache import NoCache

import logging
log = logging.getLogger(__name__)


def get_connection():
    """
    Get a connected p2p object. This function is meant to auto-discover
    the settings from your shell environment or from Django.

    We'll read these from your shell variables::

        export P2P_API_KEY=your_p2p_api_key
        export P2P_API_URL=url_of_p2p_endpoint
        export P2P_API_DEBUG=plz  # display an http log

    Or those same settings from your Django settings::

        P2P_API_KEY = your_p2p_api_key
        P2P_API_URL = url_of_p2p_endpoint
        P2P_API_DEBUG = plz  # display an http log

    If you need to pass in your config, just create a new p2p object.
    """

    import os
    # Try getting settings from environment variables
    if 'P2P_API_KEY' in os.environ and 'P2P_API_URL' in os.environ:
        return P2P(
            url=os.environ['P2P_API_URL'],
            auth_token=os.environ['P2P_API_KEY'],
            debug=os.environ['P2P_API_DEBUG'] if 'P2P_API_DEBUG' in os.environ else False
        )

    # Try getting settings from Django
    try:
        from django.conf import settings
        return P2P(
            url=settings.P2P_API_URL,
            auth_token=settings.P2P_API_KEY,
            debug=settings.DEBUG
        )
    except ImportError, e:
        pass

    raise P2PException("No connection settings available. Please put settings in your environment variables or your Django config")


_slugify_strip_re = re.compile(r'[^\w\s./-]')
_slugify_hyphenate_re = re.compile(r'[-./\s]+')
_iso8601_full_date = re.compile(r'^\d{4}-\d{2}-\d{2}.\d{2}:\d{2}.*$')
_iso8601_part_date = re.compile(r'^\d{4}-\d{2}-\d{2}$')


# API calls
class P2P(object):
    """
    Get a connection to the P2P Content Services API::

        p2p = P2P(my_p2p_url, my_auth_token)

    You can send debug messages to stderr by using the keyword::

        p2p = P2P(my_p2p_url, my_auth_token, debug=True)

    A P2P object can cache the API calls you make. Pass a new Cache_
    object with the cache keyword::

        p2p = P2P(my_p2p_url, my_auth_token, debug=True
                  cache=DictionaryCache())

    A DictionaryCache just caches in a python variable. If you're using
    Django caching::

        p2p = P2P(my_p2p_url, my_auth_token, debug=True
                  cache=DjangoCache())
    """

    def __init__(self, url, auth_token, debug=False, cache=NoCache(),
                 default_content_item_query=None,
                 content_item_defaults=None):
        self.config = {
            'P2P_API_ROOT': url,
            'P2P_AUTH_TOKEN': auth_token,
        }
        self.cache = cache

        if default_content_item_query is None:
            self.default_content_item_query = {'include': ['web_url']}
        else:
            self.default_content_item_query = default_content_item_query

        if debug:
            self.config['REQUESTS_CONFIG'] = {'verbose': sys.stderr}
        else:
            self.config['REQUESTS_CONFIG'] = {}

        if content_item_defaults is None:
            self.content_item_defaults = {
                "content_item_type_code": "blurb",
                "product_affiliate_code": "chinews",
                "source_code": "chicagotribune",
                "content_item_state_code": "live",
                "body": "",
            }
        else:
            self.content_item_defaults = content_item_defaults

    def get_content_item(self, slug, query=None, force_update=False):
        """
        Get a single content item by slug.

        Takes an optional `query` parameter which is dictionary containing
        parameters to pass along in the API call. See the P2P API docs
        for details on parameters.

        Use the parameter `force_update=True` to update the cache for this
        item and query.
        """
        if not query:
            query = self.default_content_item_query

        if force_update:
            j = self.get("/content_items/%s.json" % (slug), query)
            ci = j['content_item']
            self.cache.save_content_item(ci, query=query)
        else:
            ci = self.cache.get_content_item(slug=slug, query=query)
            if ci is None:
                j = self.get("/content_items/%s.json" % (slug), query)
                ci = j['content_item']
                self.cache.save_content_item(ci, query=query)
        return ci

    def get_multi_content_items(self, ids, query=None, force_update=False):
        """
        Get a bunch of content items at once. We need to use the content items
        ids to use this API call.

        The API only allows 25 items to be requested at once, so this function
        breaks the list of ids into groups of 25 and makes multiple API calls.

        Takes an optional `query` parameter which is dictionary containing
        parameters to pass along in the API call. See the P2P API docs
        for details on parameters.
        """
        ret = list()
        items = list()
        if_modified_since = datetime(1900, 1, 1)

        if not query:
            query = self.default_content_item_query

        # Pull as many items out of cache as possible
        for id in ids:
            if force_update:
                items.append({
                    "id": id,
                    "if_modified_since": self.formatdate(if_modified_since),
                })
            else:
                ci = self.cache.get_content_item(id=id, query=query)
                if ci is None:
                    items.append({
                        "id": id,
                        "if_modified_since": self.formatdate(
                            if_modified_since),
                    })
                else:
                    ret.append(ci)

        if len(items) > 0:
            # We can only request 25 things at a time
            # so we're gonna break up the list into batches
            max_items = 25
            if len(items) > max_items:
                # we have to use <gasp>MATH</gasp>
                num_items = len(ids)

                # how many batches of max_items do we have?
                num_batches = int(math.ceil(float(num_items) / float(max_items)))

                # make a list of indices where we should break the item list
                index_breaks = [j * max_items for j in range(num_batches)]

                # break up the items into batches of 25
                batches = [items[i:i + max_items] for i in index_breaks]
            else:
                batches = [items]

            for items in batches:
                multi_query = query.copy()
                multi_query['content_items'] = items

                resp = self.post_json('/content_items/multi.json', multi_query)
                for ci_resp in resp:
                    if ci_resp['status'] == 200:
                        ci = ci_resp['body']['content_item']
                        ret.append(ci)
                        self.cache.save_content_item(ci, query=query)
                    elif ci_resp['status'] == 404:
                        pass
                        #log.error("Content item %(id)s doesn't exsist" % ci_resp)
                    elif ci_resp['status'] == 304:
                        pass
                        #log.warn("Content item %(id)s hasn't changed" % ci_resp)
                    else:
                        raise P2PException('%(status)s fetching %(id)s' % ci_resp)

        return ret

    def update_content_item(self, content_item, slug=None):
        """
        Update a content item.

        Takes a single dictionary representing the content_item to be updated.
        Refer to the P2P API docs for the content item field names.

        By default this function uses the value of the 'slug' key from the
        dictionary to perform the API call. It takes an optional `slug`
        parameter in case the dictionary does not contain a 'slug' key or if
        the dictionary contains a changed slug.
        """
        content = content_item.copy()

        if slug is None:
            slug = content.pop('slug')

        d = {'content_item': content}

        resp = self.put_json("/content_items/%s.json" % slug, d)
        return resp

    def create_content_item(self, content_item):
        """
        Create a new content item.

        Takes a single dictionary representing the new content item.
        Refer to the P2P API docs for the content item field names.
        """
        content = content_item.copy()

        defaults = self.content_item_defaults.copy()
        defaults.update(content)
        data = {'content_item': defaults}

        resp = self.post_json('/content_items.json', data)
        return resp

    def create_or_update_content_item(self, content_item):
        """
        Attempts to update a content item, if it doesn't exist, attempts to
        create it::

            create, response = p2p.create_or_update_content_item(item_dict)

        TODO: swap the tuple that is returned.
        """
        create = False
        try:
            response = self.update_content_item(content_item)
        except requests.exceptions.HTTPError, e:
            if e.response.status_code == 404:
                time.sleep(2)
                response = self.create_content_item(content_item)
                create = True
            else:
                raise e

        return (create, response)

    def junk_content_item(self, slug):
        """
        Sets a content item to junk status.
        """
        return self.update_content_item({
            'slug': slug,
            'content_item_state_code': 'junk'
        })

    def search(self, params):
        resp = self.get("/content_items/search.json", params)
        return resp

    def get_collection(self, slug, query=None, force_update=False):
        if force_update:
            data = self.get('/collections/%s.json' % slug, query)
            collection = data['collection']
            self.cache.save_collection(collection, query=query)
        else:
            collection = self.cache.get_collection(slug, query=query)
            if collection is None:
                data = self.get('/collections/%s.json' % slug, query)
                collection = data['collection']
                self.cache.save_collection(collection, query=query)

        return collection

    def get_collection_layout(self, slug, query=None, force_update=False):
        if not query:
            query = {'include': 'items'}

        if force_update:
            resp = self.get('/current_collections/%s.json' % slug, query)
            collection_layout = resp['collection_layout']
            collection_layout['code'] = slug  # response is missing this
            self.cache.save_collection_layout(collection_layout, query=query)
        else:
            collection_layout = self.cache.get_collection_layout(
                slug, query=query)
            if collection_layout is None:
                resp = self.get('/current_collections/%s.json' % slug, query)
                collection_layout = resp['collection_layout']
                collection_layout['code'] = slug  # response is missing this
                self.cache.save_collection_layout(
                    collection_layout, query=query)

        return collection_layout

    def get_fancy_collection(self, slug, with_collection=False,
                             limit_items=25, content_item_query=None,
                             force_update=False):
        """
        Make a few API calls to fetch all possible data for a collection
        and its content items. Returns a collection layout with
        extra 'collection' key on the layout, and a 'content_item' key
        on each layout item.
        """
        collection_layout = self.get_collection_layout(
            slug, force_update=force_update)
        if with_collection:
            # Do we want more detailed data about the collection?
            collection = self.get_collection(slug, force_update=force_update)

            collection_layout['collection'] = collection

        if limit_items:
            # We're only going to fetch limit_items number of things
            # so cut out the extra items in the content_layout
            collection_layout['items'] = collection_layout['items'][:limit_items]

        content_item_ids = [
            ci['contentitem_id'] for ci in collection_layout['items']
        ]

        content_items = self.get_multi_content_items(
            content_item_ids, query=content_item_query)

        for ci in collection_layout['items']:
            for ci2 in content_items:
                if ci['contentitem_id'] == ci2['id']:
                    ci['content_item'] = ci2
                    break

        return collection_layout

    # Utilities
    def http_headers(self, content_type=None):
        h = {
            'Authorization': 'Bearer %(P2P_AUTH_TOKEN)s' % self.config,
        }
        if content_type is not None:
            h['content-type'] = content_type
        return h

    def get(self, url, query=None):
        if query is not None:
            url += '?' + self.dict_to_qs(query)

        resp = requests.get(
            self.config['P2P_API_ROOT'] + url,
            headers=self.http_headers(),
            config=self.config['REQUESTS_CONFIG'],
            verify=False)
        if not resp.ok:
            resp.raise_for_status()
        return self.parse_response(json.loads(resp.content))

    def post_json(self, url, data):
        resp = requests.post(
            self.config['P2P_API_ROOT'] + url,
            data=json.dumps(data),
            headers=self.http_headers('application/json'),
            config=self.config['REQUESTS_CONFIG'],
            verify=False)
        if not resp.ok:
            resp.raise_for_status()
        return self.parse_response(json.loads(resp.content))

    def put_json(self, url, data):
        resp = requests.put(
            self.config['P2P_API_ROOT'] + url,
            data=json.dumps(data),
            headers=self.http_headers('application/json'),
            config=self.config['REQUESTS_CONFIG'],
            verify=False)
        if not resp.ok:
            resp.raise_for_status()
        return self.parse_response(json.loads(resp.content))

    @staticmethod
    def slugify(value):
        """
        Normalizes string, converts to lowercase, removes non-alpha characters,
        and converts spaces to hyphens.

        From Django's "django/template/defaultfilters.py".
        """
        import unicodedata
        if not isinstance(value, unicode):
            value = unicode(value)
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = unicode(_slugify_strip_re.sub('', value).strip().lower())
        return _slugify_hyphenate_re.sub('-', value)

    @staticmethod
    def dict_to_qs(dictionary):
        """
        Takes a dictionary of query parameters and returns a query string
        that the p2p API will handle.
        """
        qs = list()

        for k, v in dictionary.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    if type(v2) in (str, unicode, int, float, bool):
                        qs.append("%s[%s]=%s" % (k, k2, v2))
                    elif type(v2) in (list, tuple):
                        for v3 in v2:
                            qs.append("%s[%s][]=%s" % (k, k2, v3))
                    else:
                        raise TypeError
            elif type(v) in (str, unicode, int, float, bool):
                qs.append("%s=%s" % (k, v))
            elif type(v) in (list, tuple):
                for v2 in v:
                    qs.append("%s[]=%s" % (k, v2))
            else:
                raise TypeError

        return "&".join(qs)

    @staticmethod
    def parse_response(resp):
        """
        Recurse through a dictionary from an API call, and fix weird values,
        convert date strings to objects, etc.
        """
        if type(resp) in (str, unicode):
            if resp in ("null", "Null"):
                # Null value as a string
                return None
            elif (_iso8601_full_date.match(resp) is not None
                    or _iso8601_part_date.match(resp) is not None):
                # Date as a string
                return P2P.parsedate(resp)
        elif type(resp) is dict:
            # would use list comprehension, but that makes unnecessary copies
            for k, v in resp.items():
                resp[k] = P2P.parse_response(v)
        elif type(resp) is list:
            # would use list comprehension, but that makes unnecessary copies
            for i in range(len(resp)):
                resp[i] = P2P.parse_response(resp[i])

        return resp

    @staticmethod
    def formatdate(d=datetime.utcnow()):
        return d.strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def parsedate(d):
        if _iso8601_full_date.match(d) is not None:
            return iso8601.parse_date(d)
        else:
            return parse(d)


class P2PException(Exception):
    pass
