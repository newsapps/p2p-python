'''
Python wrapper for the Content Services API

'''
import requests
import json
import os
import math
from datetime import datetime
from copy import deepcopy

from cache import NoCache
import utils

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
            debug=os.environ.get('P2P_API_DEBUG', False)
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

    raise P2PException("No connection settings available. Please put settings "
                       "in your environment variables or your Django config")


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
        self.debug = debug

        if default_content_item_query is None:
            self.default_content_item_query = {'include': ['web_url']}
        else:
            self.default_content_item_query = default_content_item_query

        if content_item_defaults is None:
            self.content_item_defaults = {
                "content_item_type_code": "blurb",
                "product_affiliate_code": "chinews",
                "source_code": "chicagotribune",
                "content_item_state_code": "live",
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
                    "if_modified_since": utils.formatdate(if_modified_since),
                })
            else:
                ci = self.cache.get_content_item(id=id, query=query)
                if ci is None:
                    items.append({
                        "id": id,
                        "if_modified_since": utils.formatdate(
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
                num_batches = int(
                    math.ceil(float(num_items) / float(max_items)))

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

    def get_collection(self, code, query=None, force_update=False):
        if force_update:
            data = self.get('/collections/%s.json' % code, query)
            collection = data['collection']
            self.cache.save_collection(collection, query=query)
        else:
            collection = self.cache.get_collection(code, query=query)
            if collection is None:
                data = self.get('/collections/%s.json' % code, query)
                collection = data['collection']
                self.cache.save_collection(collection, query=query)

        return collection

    def push_into_collection(self, code, content_item_slugs):
        """
        Push a list of content item slugs onto the top of a collection
        """
        return self.put_json(
            '/collections/prepend.json?id=%s' % code,
            {'items': content_item_slugs})

    def suppress_in_collection(
            self, code, content_item_slugs, affiliates=['chinews']):
        """
        Suppress a list of slugs in the specified collection
        """
        return self.put_json(
            '/collections/suppress.json?id=%s' % code,
            {'items': [{
                'slug': slug, 'affiliates': affiliates
            } for slug in content_item_slugs]})

    def insert_position_in_collection(
            self, code, slug, affiliates=['chinews']):
        """
        Suppress a list of slugs in the specified collection
        """
        return self.put_json(
            '/collections/insert.json?id=%s' % code,
            {'items': [{
                'slug': slug, 'position': 1
            }]})

    def push_into_content_item(self, code, content_item_slugs):
        """
        Push a list of content item slugs onto the top of a collection
        """
        return self.put_json(
            '/content_items/prepend.json?id=%s' % code,
            {'items': content_item_slugs})

    def get_collection_layout(self, code, query=None, force_update=False):
        if not query:
            query = {'include': 'items'}

        if force_update:
            resp = self.get('/current_collections/%s.json' % code, query)
            collection_layout = resp['collection_layout']
            collection_layout['code'] = code  # response is missing this
            self.cache.save_collection_layout(collection_layout, query=query)
        else:
            collection_layout = self.cache.get_collection_layout(
                code, query=query)
            if collection_layout is None:
                resp = self.get('/current_collections/%s.json' % code, query)
                collection_layout = resp['collection_layout']
                collection_layout['code'] = code  # response is missing this
                self.cache.save_collection_layout(
                    collection_layout, query=query)

        return collection_layout

    def get_fancy_collection(self, code, with_collection=False,
                             limit_items=25, content_item_query=None,
                             force_update=False):
        """
        Make a few API calls to fetch all possible data for a collection
        and its content items. Returns a collection layout with
        extra 'collection' key on the layout, and a 'content_item' key
        on each layout item.
        """
        collection_layout = self.get_collection_layout(
            code, force_update=force_update)
        if with_collection:
            # Do we want more detailed data about the collection?
            collection = self.get_collection(code, force_update=force_update)

            collection_layout['collection'] = collection

        if limit_items:
            # We're only going to fetch limit_items number of things
            # so cut out the extra items in the content_layout
            collection_layout['items'] = collection_layout['items'][:limit_items]

        content_item_ids = [
            ci['contentitem_id'] for ci in collection_layout['items']
        ]

        content_items = self.get_multi_content_items(
            content_item_ids, query=content_item_query, force_update=force_update)

        for ci in collection_layout['items']:
            for ci2 in content_items:
                if ci['contentitem_id'] == ci2['id']:
                    ci['content_item'] = ci2
                    break

        return collection_layout

    def get_fancy_content_item(self, slug, query=None,
                               related_items_query=None,
                               force_update=False):
        if query is None:
            query = deepcopy(self.default_content_item_query)
            query['include'].append('related_items')

        if related_items_query is None:
            related_items_query = self.default_content_item_query

        content_item = self.get_content_item(
            slug, query, force_update=force_update)

        # We have our content item, now loop through the related
        # items, build a list of content item ids, and retrieve them all
        ids = [item_stub['relatedcontentitem_id']
               for item_stub in content_item['related_items']]

        related_items = self.get_multi_content_items(
            ids, related_items_query, force_update=force_update)

        # now that we've retrieved all the related items, embed them into
        # the original content item dictionary to make it fancy
        for item_stub in content_item['related_items']:
            for item in related_items:
                if item_stub['relatedcontentitem_id'] == item['id']:
                    item_stub['content_item'] = item

        return content_item

    def get_section(self, path, force_update=False):
        query = {
            'section_path': path,
            'product_affiliate_code': 'chinews'
        }
        if force_update:
            data = self.get('/sections/show_collections.json', query)
            section = data
            self.cache.save_section(section, path=path)
        else:
            section = self.cache.get_section(path)
            if section is None:
                data = self.get('/sections/show_collections.json', query)
                section = data
                self.cache.save_section(section, path=path)

        return section

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
            url += '?' + utils.dict_to_qs(query)

        resp = requests.get(
            self.config['P2P_API_ROOT'] + url,
            headers=self.http_headers(),
            verify=False)
        if self.debug:
            log.debug('URL: %s' % url)
            log.debug('HEADERS: %s' % self.http_headers())
        if resp.status_code >= 500:
            resp.raise_for_status()
        elif resp.status_code >= 400:
            try:
                data = resp.json()
            except ValueError:
                data = resp.text
            raise P2PException(resp.content, data)
        return utils.parse_response(resp.json())

    def post_json(self, url, data):
        resp = requests.post(
            self.config['P2P_API_ROOT'] + url,
            data=json.dumps(data),
            headers=self.http_headers('application/json'),
            verify=False)
        if self.debug:
            log.debug('URL: %s' % url)
            log.debug('HEADERS: %s' % self.http_headers())
            log.debug('PAYLOAD: %s' % json.dumps(data))
        if resp.status_code >= 500:
            resp.raise_for_status()
        elif resp.status_code >= 400:
            raise P2PException(resp.content, resp.json())
        return utils.parse_response(resp.json())

    def put_json(self, url, data):
        resp = requests.put(
            self.config['P2P_API_ROOT'] + url,
            data=json.dumps(data),
            headers=self.http_headers('application/json'),
            verify=False)
        if self.debug:
            log.debug('URL: %s' % url)
            log.debug('HEADERS: %s' % self.http_headers())
            log.debug('PAYLOAD: %s' % json.dumps(data))
        if resp.status_code >= 500:
            resp.raise_for_status()
        elif resp.status_code >= 400:
            raise P2PException(resp.content)
        return utils.parse_response(resp.json())


class P2PException(Exception):
    pass
