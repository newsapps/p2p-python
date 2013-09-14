# -*- coding: utf-8 -*-

import argparse
import requests
import json

from __init__ import get_connection

import pprint
pp = pprint.PrettyPrinter(indent=4)


def content_item_cli():
    # Parse options
    commands_description = """%(prog)s"""

    parser = argparse.ArgumentParser(
        usage="%(prog)s get|save|mv [options] slug",
        description=commands_description)
    parser.add_argument("command", choices=('get', 'save', 'mv'),
                        help="Action to take")
    parser.add_argument("slug",
                        help="Slug of the content item to work with.")

    parser.add_argument("-F", "--from-file", dest="body_file",
                        type=argparse.FileType('r'), default='-',
                        help="Load the body from a file")

    # Save
    parser.add_argument("-c", "--type-code", dest="type", default="blurb",
                        help="Set the content item type")
    parser.add_argument("-t", "--title", dest="title",
                        help="Set the content item title")
    parser.add_argument("-s", "--state", dest="state",
                        choices=('live', 'working', 'archived',
                        'pending', 'junk'),
                        help="Set the content item state")

    # Move
    parser.add_argument("--new-slug", dest="new_slug",
                        help="Change the slug")

    # Get
    parser.add_argument("-f", "--field-name", dest="field_name",
                        help="Field to output")

    args = parser.parse_args()

    slug = args.slug
    content_item = dict()

    p2p = get_connection()

    if args.command == 'mv' and args.new_slug:
        content_item['slug'] = args.new_slug
        try:
            p2p.update_content_item(content_item, slug=slug)
            print("Moved '%s' to '%s'" % (slug, content_item['slug']))
        except requests.exceptions.HTTPError, e:
            print(e.message)
            print(e.__dict__['response'].content)

    if args.command == "save":
        content_item = {
            "slug": slug,
            "content_item_type_code": args.type,
            "body": args.body_file.read(),
        }

        if args.state:
            content_item['content_item_state_code'] = args.state

        if args.title:
            content_item['title'] = args.title

        print("Saving '%s'" % content_item['slug'])
        try:
            p2p.create_or_update_content_item(content_item)
            print("Updated '%s'" % content_item['slug'])
        except requests.exceptions.HTTPError, e:
            print(e.message)
            print(e.__dict__['response'].content)

    elif args.command == "get":
        try:
            data = p2p.get_content_item(slug)
            if args.field_name in data:
                print(data[args.field_name])
            else:
                print(json.dumps(data))
        except requests.exceptions.HTTPError, e:
            print(e.message)
            print(e.__dict__['response'].content)
