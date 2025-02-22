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

import markupsafe

from concerto_gui.utils import json


class Markup(markupsafe.Markup):
    __slots__ = ()

    @classmethod
    def escape(cls, value):
        if value is None:
            return Markup()

        return markupsafe.escape(value)


def escape(value):
    return Markup.escape(value)


def escapejs(value):
    value = json.dumps(value, cls=json.ConcertoHTMLJSONEncoder)

    if "__concerto_gui_class__" in value:
        value = "_concerto_gui_revive(%s)" % value

    return Markup(value)
