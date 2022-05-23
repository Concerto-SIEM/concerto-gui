# Copyright (C) 2022 Concerto SIEM. All Rights Reserved.
# Author: Maxime Rebon <maxime.rebon@gmail.com>

# Copyright (C) 2014-2020 CS GROUP - France. All Rights Reserved.
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

import uuid

from concerto_gui import error, localization, pluginmanager, resource
from concerto_gui.utils import cache

RED_STD = "E78D90"
ORANGE_STD = "F5B365"
YELLOW_STD = "D4C608"
GREEN_STD = "B1E55D"
BLUE_STD = "93B9DD"
GRAY_STD = "5C5C5C"

COLORS = (BLUE_STD, GREEN_STD, YELLOW_STD, ORANGE_STD, RED_STD,
          "C6A0CF", "5256D3", "A7DE65", "F2A97B", "F6818A", "B087C6", "66DC92")


class RendererException(Exception):
    pass


class RendererNoDataException(RendererException):
    def __str__(self):
        return _("No data to display.")


class RendererItem(object):
    __slots__ = ["values", "series", "links", "_tuple"]

    def __init__(self, values=0, series=None, links=None):
        self._tuple = values, series, links

        self.values = values
        self.series = series
        self.links = links

    def __getitem__(self, i):
        return self._tuple[i]


class RendererUtils(object):
    _nexist_color = (_("n/a"), GRAY_STD)

    def __init__(self, options):
        self._color_map_idx = 0
        self._color_map = options.get("names_and_colors")

    def get_label(self, series):
        if self._color_map and len(series) == 1:
            return _(self._color_map.get(series[0], self._nexist_color)[0])

        return ", ".join(localization.format_value(s) for s in series)

    @cache.request_memoize("renderer_color")
    def get_color(self, series, onecolor=False):
        if self._color_map and len(series) == 1:
            color = self._color_map.get(series[0], self._nexist_color)[1]
            if color:
                return color

        color = COLORS[self._color_map_idx % len(COLORS)]

        if not onecolor:
            self._color_map_idx += 1

        return color


class RendererBackend(pluginmanager.PluginBase):
    pass


class RendererPluginManager(pluginmanager.PluginManager):
    _default_backends = {}

    def __init__(self, autoupdate=False):
        self._backends = pluginmanager.PluginManager("concerto_gui.renderer.backend", autoupdate=autoupdate)
        pluginmanager.PluginManager.__init__(self, "concerto_gui.renderer.type", autoupdate=autoupdate)

        for typ, backend in env.config.renderer_defaults.items():
            self._default_backends[typ] = backend

        self._renderer = {}

    def _init_callback(self, plugin):
        self._renderer.setdefault(plugin.renderer_backend, {})[plugin.renderer_type] = plugin

        if plugin.renderer_type not in self._default_backends:
            self._default_backends[plugin.renderer_type] = plugin.renderer_backend

    def get_types(self):
        return self._default_backends.keys()

    def has_backend(self, wanted_backend, wanted_type=None):
        if wanted_backend not in self._renderer:
            return False

        if wanted_type is None:
            return True

        return set(wanted_type).issubset(self._renderer[wanted_backend])

    def get_backends(self, wanted_type):
        for backend, typedict in self._renderer.items():
            if wanted_type in typedict:
                yield backend

    def get_backends_instances(self, wanted_type):
        for backend in self.get_backends(wanted_type):
            yield self._renderer[backend][wanted_type]

    def get_default_backend(self, wanted_type):
        return self._default_backends.get(wanted_type)

    def _setup_renderer(self, type, renderer):
        renderer = renderer or self.get_default_backend(type)

        if renderer is None:
            raise error.ConcertoUserError(N_("Renderer error"),
                                          N_("No backend supporting render type '%s'", type))

        if renderer not in self._renderer:
            raise error.ConcertoUserError(N_("Renderer error"),
                                          N_("No backend named '%s'", renderer))

        if type not in self._renderer[renderer]:
            raise error.ConcertoUserError(N_("Renderer error"),
                                          N_("Backend '%(backend)s' does not support render type '%(type)s'",
                                             {'backend': renderer, 'type': type}))

        return renderer

    def update(self, type, data, renderer=None, **kwargs):
        renderer = self._setup_renderer(type, renderer)
        return self._renderer[renderer][type].update(data, **kwargs)

    def render(self, type, data, renderer=None, **kwargs):
        renderer = self._setup_renderer(type, renderer)

        classname = kwargs["class"] = "-".join((renderer, type))
        cssid = kwargs["cssid"] = "-".join((classname, text_type(uuid.uuid4())))

        try:
            data = self._renderer[renderer][type].render(data, **kwargs)
            htmls = resource.HTMLSource('<div id="%s" class="renderer-elem %s">%s</div>'
                                        % (cssid, classname, data.get("html", "")))

            return {"html": htmls, "script": resource.HTMLSource(data.get("script", ""))}
        except RendererException as e:
            htmls = resource.HTMLSource('<div id="%s" class="renderer-elem renderer-elem-error %s"><div class="text-center-vh">%s</div></div>'
                                        % (cssid, classname, text_type(e)))

            return {"html": htmls, "script": None}
