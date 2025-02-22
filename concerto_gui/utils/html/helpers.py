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

from concerto_gui import csrf, resource


POPOVER_HTML = '<div class="popover popover-menu" role="tooltip"><div class="arrow"></div><div class="popover-content"></div></div>'


def csrftoken():
    return resource.HTMLSource('<input type="hidden" name="%s" value="%s" />' % (csrf.CSRF_POST_KEY, csrf.get_token(env.request.web)))


def selected(condition):
    return "selected" if condition else ""


def checked(condition):
    return "checked" if condition else ""


def disabled(condition):
    return "disabled" if condition else ""


class HTMLProgressBar(resource.HTMLNode):
    def __init__(self, color, progress, text):
        txtspan = resource.HTMLNode('span', text)

        pgdiv = resource.HTMLNode('div', txtspan, **{
            'class': "progress-bar progress-bar-%s progress-bar-striped" % color,
            'aria-valuenow': progress,
            'aria-valuemin': 0,
            'aria-valuemax': 100,
            'style': "width: %s%%" % progress
        })

        resource.HTMLNode.__init__(self, 'div', pgdiv, _class='progress')

    def __jsonobj__(self):
        return {"__concerto_gui_class__": ("HTMLNode", self.__json__())}
