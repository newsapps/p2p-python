#! /usr/bin/env python
import unittest

from __init__ import get_connection
from cache import DictionaryCache
from auth import authenticate, P2PAuthError

import pprint
pp = pprint.PrettyPrinter(indent=4)


class TestP2P(unittest.TestCase):
    def setUp(self):
        self.content_item_slug = 'chi-na-lorem-a'
        self.collection_slug = 'chi_na_lorem'
        self.p2p = get_connection()
        self.maxDiff = None

        self.content_item_keys = ('altheadline', 'expire_time',
                'canonical_url', 'mobile_title', 'create_time',
                'source_name', 'last_modified_time', 'seodescription',
                'exclusivity', 'content_type_group_code', 'byline',
                'title', 'dateline', 'brief', 'id', 'web_url', 'body',
                'display_time', 'publish_time', 'undated', 'is_opinion',
                'columnist_id', 'live_time', 'titleline',
                'ad_exclusion_category', 'product_affiliate_code',
                'content_item_state_code', 'seo_redirect_url', 'slug',
                'content_item_type_code', 'deckheadline', 'seo_keyphrase',
                'mobile_highlights', 'subheadline', 'thumbnail_url',
                'source_code', 'ad_keywords', 'seotitle', 'alt_thumbnail_url')
        self.collection_keys = ('created_at', 'code', 'name',
                'sequence', 'max_elements', 'productaffiliatesection_id',
                'last_modified_time', 'collection_type_code',
                'exclusivity', 'id')
        self.content_layout_keys = ('code', 'items',
                'last_modified_time', 'collection_id', 'id')
        self.content_layout_item_keys = (
                'content_item_type_code', 'content_item_state_code',
                'sequence', 'headline', 'abstract',
                'productaffiliatesection_id', 'slug', 'subheadline',
                'last_modified_time', 'contentitem_id', 'id')

    def test_get_content_item(self):
        data = self.p2p.get_content_item(self.content_item_slug)
        for k in self.content_item_keys:
            self.assertIn(k, data.keys())

    def test_get_collection(self):
        data = self.p2p.get_collection(self.collection_slug)
        for k in self.collection_keys:
            self.assertIn(k, data.keys())

    def test_get_collection_layout(self):
        data = self.p2p.get_collection_layout(self.collection_slug)
        for k in self.content_layout_keys:
            self.assertIn(k, data.keys())

        for k in self.content_layout_item_keys:
            self.assertIn(k, data['items'][0].keys())

    def test_multi_items(self):
        content_item_ids = [58253183, 56809651, 56810874, 56811192, 58253247]
        data = self.p2p.get_multi_content_items(ids=content_item_ids)
        for k in self.content_item_keys:
            self.assertIn(k, data[0].keys())

    def test_many_multi_items(self):
        cslug = 'chicago_breaking_news_headlines'
        clayout = self.p2p.get_collection_layout(cslug)
        ci_ids = [i['contentitem_id'] for i in clayout['items']]

        self.assertTrue(len(ci_ids) > 25)

        data = self.p2p.get_multi_content_items(ci_ids)
        self.assertTrue(len(ci_ids) == len(data))
        for k in self.content_item_keys:
            self.assertIn(k, data[0].keys())

    def test_cache(self):
        self.p2p.cache = DictionaryCache()
        content_item_ids = [58253183, 56809651, 56810874, 56811192, 58253247]
        data = self.p2p.get_multi_content_items(ids=content_item_ids)
        data = self.p2p.get_content_item(self.content_item_slug)
        stats = self.p2p.cache.get_stats()
        self.assertEqual(stats['content_item_gets'], 6)
        self.assertEqual(stats['content_item_hits'], 1)

    def test_fancy_collection(self):
        data = self.p2p.get_fancy_collection(
            self.collection_slug, with_collection=True)

        for k in self.content_layout_keys:
            self.assertIn(k, data.keys())

        for k in self.collection_keys:
            self.assertIn(k, data['collection'].keys())

        for k in self.content_layout_item_keys:
            self.assertIn(k, data['items'][0].keys())

        for k in self.content_item_keys:
            self.assertIn(k, data['items'][0]['content_item'].keys())

    @unittest.skip("Uhhh... not committing my password")
    def test_auth(self):
        self.username = ''
        self.password = ''

        self.badpassword = 'password'

        self.token = 'whatisthis?'

        with self.assertRaises(P2PAuthError) as err:
            userinfo = authenticate(
                username=self.username,
                password=self.badpassword)

        self.assertEqual(err.exception.message,
                         'Incorrect username or password')

        userinfo = authenticate(
            username=self.username, password=self.password)

        #pp.pprint(userinfo)

        self.assertEqual(type(userinfo), dict)


if __name__ == '__main__':
    unittest.main()

