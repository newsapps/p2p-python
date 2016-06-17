# Python wrapper for P2P Content Services

## Connection configuration

Configuration settings. Set these values in your environment or your Django settings.

    P2P_API_KEY = your_p2p_api_key
    P2P_API_URL = url_of_p2p_endpoint
    P2P_API_DEBUG = plz  # display an http log
    P2P_PRESERVE_EMBEDDED_TAGS = False # set to false to fix encoding issues with special characters

    # Optional
    P2P_IMAGE_SERVICES_URL = url_of_image_services_endpoint

To get a connection object based on these settings:

    from p2p import get_connection
    p2p = get_connection()

Or you can create a connection object manually. You'll want to do this in order to enable caching.

    from p2p import P2P, cache
    p2p = P2P(
        url='url_of_p2p_endpoint',
        auth_token='your_p2p_api_key',
        debug=False or True,
        image_services_url='url_of_image_services_endpoint',
        cache=cache.DictionaryCache(),
        preserve_embedded_tags=False or True
    )

## Testing

To run tests:

    $ python setup.py test


## Methods on the connection object

### Content items

#### `create_content_item(content_item)`

Create a new content item.

Takes a single dictionary representing the new content item. Refer to the P2P API docs for the content item field names.

#### `create_or_update_content_item(content_item)`

Attempts to update a content item, if it doesn't exist, attempts to create it.

#### `update_content_item(content_item, slug=None)`

Update a single content item.

Takes a single dictionary representing the content_item to be updated. Refer to the P2P API docs for the content item field names.

By default this function uses the value of the 'slug' key from the dictionary to perform the API call. It takes an optional `slug` parameter in case the dictionary does not contain a 'slug' key or if the dictionary contains a changed slug. Alternatively, an ID can be passed to the slug parameter.

#### `get_content_item(slug, query=None, force_update=False)`

Gets a single content item by slug or ID.

Takes an optional `query` parameter which is a dictionary containing parameters to pass along in the API call. See [query parameters](#query-parameters).

Use the parameter `force_update=True` to update the cache for this item and query.

#### `get_fancy_content_item(slug, query=None, related_items_query=None, force_update=False)`

Get a content item and its related items.

#### `get_multi_content_items(ids, query=None, force_update=False)`

Get a bunch of content items at once. We need to use the content items ids to use this API call.

The API only allows 25 items to be requested at once, so this function breaks the list of ids into groups of 25 and makes multiple API calls.

Takes an optional `query` parameter which is a dictionary containing parameters to pass along in the API call. See [query parameters](#query-parameters).

#### `delete_content_item(slug)`

Delete the content item out of p2p. Provide the slug of the content item you'd like to delete.

#### `junk_content_item(slug)`

Sets a content item to junk status. Provide the slug of the content item you'd like to junk.

#### `hide_right_rail(slug)`

Hide the right rail from an HTML story. Provide the slug of the content item you'd like to update.

#### `show_to_robots(slug)`

Add metadata to the item so it is seen by robots and remove any noindex and nofollow tags. Provide the slug of the content item you'd like to update.

#### `hide_to_robots(slug)`

Add metadata to the item so it is hidden from robots using the noindex and nofollow tags. Provide the slug of the content item you'd like to update.

#### `get_thumb_for_slug(slug, force_update=False)`

Get information on how to display images associated with this slug.


### Topics

#### `add_topic(topic_id, slug=None)`

Adds a topic to a story. Provide the slug of the content item you'd like to update.

#### `remove_topic(topic_id, slug=None)`

Remove a topic from a story. Provide the slug of the content item you'd like to update.


### Search

#### `search(params)`

Searches P2P for content items. Refer to the P2P API docs for parameter reference.


### Collections

#### `get_collection(code, query=None, force_update=False)`

Get the data for this collection. To get the items in a collection, use get_collection_layout.

#### `create_collection(data)`

Create a new collection. Takes a single argument which should be a dictionary of collection data.

Example:

    p2p.create_collection({
        'code': 'my_new_collection',
        'name': 'My new collection',
        'section_path': '/news/local',
        // OPTIONAL PARAMS
        'collection_type_code': 'misc',  # default 'misc'
        'last_modified_time': date,  # defaults to now
        'product_affiliate_code': 'chinews'  # default to instance setting
    })

#### `delete_collection(code)`

Delete a collection

#### `override_layout(code, content_item_slugs)`

Override collection layout using a list of slugs.

#### `push_into_collection(code, content_item_slugs)`

Push a list of content item slugs onto the top of a collection.

#### `suppress_in_collection(code, content_item_slugs, affiliates=[])`

Suppress a list of slugs in the specified collection.

#### `remove_from_collection(code, content_item_slugs)`

Remove a list of content items from the specified collection.

#### `insert_position_in_collection(code, slug, affiliates=[])`

Insert a content item into a collection at position 1.

#### `get_collection_layout(code, query=None, force_update=False)`

Get the layout of a collection.

Takes an optional `query` parameter which is a dictionary containing parameters to pass along in the API call. See [query parameters](#query-parameters).

#### `get_fancy_collection(code, with_collection=False, limit_items=25, content_item_query=None, collection_query=None, include_suppressed=False, force_update=False)`

Make a few API calls to fetch all possible data for a collection and its content items. Returns a collection layout with extra 'collection' key on the layout, and a 'content_item' key on each layout item.


### Related items

#### `push_into_content_item(slug, content_item_slugs)`

Push a list of content item slugs onto the top of the related items list for a content item.

#### `remove_from_content_item(slug, content_item_slugs)`

Remove related items from a content item. Specify the slug of the content item and a list of related items you'd like to remove.

#### `insert_into_content_item(slug, content_item_slugs, position=1)`

Insert a list of content item slugs into the related items list for a content item, starting at the specified position.

#### `append_into_content_item(slug, content_item_slugs)`

Convenience function to append a list of content item slugs to the end of the related items list for a content item.

### Embedded items

#### `push_embed_into_content_item(slug, content_item_slugs, size="S")`

Push a list of content item slugs onto the top of the embedded items list for a content item.

An optional `size` parameter can be provided to set the display size of the embeds:

    client.push_embed_into_content_item(
        ['slug-1', 'slug-2', 'slug-3'],
        size='L'
    )

Alternatively accepts a list of dictionaries to specify per-item sizes:

    client.push_embed_into_content_item([
        dict(slug='slug-1', size='S'),
        dict(slug='slug-2', size='L'),
        dict(slug='slug-3', size='L'),
    ])

#### `remove_embed_from_content_item(slug, content_item_slugs)`

Remove embedded items from a content item. Specify the slug of the content item and a list of related items you'd like to remove.


### Sections

#### `get_section(path, query=None, force_update=False)`

Get the collections that are on a section page.

#### `get_section_configs(path, query=None, force_update=False)`

Get the metadata configuration of a section page.

#### `get_fancy_section(path, force_update=False)`

Get both the collections and metadata of a section.


### Navigation

#### `get_nav(collection_code, domain=None)`

Get a dictionary of text and links for a navigation collection.

### Query parameters

See the [P2P API docs](http://content-api.p2p.tribuneinteractive.com/docs) for details on the ["common"](http://content-api.p2p.tribuneinteractive.com/docs/common_parameters) and ["filter"](http://content-api.p2p.tribuneinteractive.com/docs/content_item_filter) query parameters.

### Exceptions

The wrapper scans API responses for known errors to raise relevant Python exceptions.

 * `P2PException` - Base class for other exceptions and fallback when an unknown error occurs.
 * `P2PSlugTaken` - Raised when creating a content item or changing a slug of an existing item.
 * `P2PNotFound` - Raised when getting a content item that doesn't exist or otherwise can't be found.
 * `P2PUniqueConstraintViolated` - Raised when adding a content item into a collection that is already present in the collection.
 * `P2PEncodingMismatch` - Raised when invalid characters are passed in.  P2P's API currently only supports the latin-1 character set.
 * `P2PUnknownAttribute`
 * `P2PInvalidAccessDefinition`
 * `P2PSearchError` - Raised when P2P's solr search fails.
 * `P2PRetryableError` - A base exception for errors we retry on failure.
 * `P2PForbidden` - Raised when the request is refused due to rate limit throttling or invalid credentials are supplied. (Inherits from `P2PRetryableError`)
 * `P2PTimeoutError` - Raised when when you hit P2P times out on its end. (Inherits from `P2PRetryableError`)

If you encounter unknown errors that you'd like to document, add it [here](p2p/errors.py) and parse it in the [`_check_for_errors` method](p2p/__init__.py#L1039).
