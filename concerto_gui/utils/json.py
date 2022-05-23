# Copyright (C) 2022 Concerto SIEM. All Rights Reserved.
# Author: Maxime Rebon <maxime.rebon@gmail.com>

# Copyright (C) 2016-2020 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
#
# This file is part of the Prewikka program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import datetime
import json

from concerto_gui.compat import with_metaclass

_TYPES = {}


class _JSONMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        nclass = super(_JSONMetaClass, cls).__new__(cls, clsname, bases, attrs)

        _TYPES[nclass.__name__] = nclass

        return nclass


class _JSONObject(object):
    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def __jsonobj__(self):
        return {"__concerto_gui_class__": (self.__class__.__name__, self.__json__())}


class JSONObject(with_metaclass(_JSONMetaClass, _JSONObject)):
    pass


class ConcertoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__jsonobj__"):
            return obj.__jsonobj__()

        elif hasattr(obj, "__json__"):
            return obj.__json__()

        elif isinstance(obj, datetime.datetime):
            return text_type(obj)

        elif isinstance(obj, collections.abs.Iterable):
            return list(obj)

        return json.JSONEncoder.default(self, obj)


# The following class has been adapted from simplejson
#
class ConcertoHTMLJSONEncoder(ConcertoJSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.
    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """

    def encode(self, o):
        # Override JSONEncoder.encode because it has hacks for
        # performance that make things more complicated.
        chunks = self.iterencode(o, True)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(self, o, _one_shot=False):
        chunks = super(ConcertoHTMLJSONEncoder, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk


def _object_hook(obj):
    cls = obj.get("__concerto_gui_class__")
    if cls:
        return _TYPES[cls[0]].from_json(cls[1])

    return obj


def load(*args, **kwargs):
    return json.load(*args, object_hook=_object_hook, **kwargs)


def loads(*args, **kwargs):
    return json.loads(*args, object_hook=_object_hook, **kwargs)


def dump(*args, **kwargs):
    if "cls" not in kwargs:
        kwargs["cls"] = ConcertoJSONEncoder

    return json.dump(*args, **kwargs)


def dumps(*args, **kwargs):
    if "cls" not in kwargs:
        kwargs["cls"] = ConcertoJSONEncoder

    return json.dumps(*args, **kwargs)
