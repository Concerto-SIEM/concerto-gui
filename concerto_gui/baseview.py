# Copyright (C) 2022 Concerto SIEM. All Rights Reserved.
# Author: Maxime Rebon <maxime.rebon@gmail.com>

# Copyright (C) 2004-2020 CS GROUP - France. All Rights Reserved.
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

import base64
import collections
import string

from concerto_gui import error, history, hookmanager, mainmenu, resource, response, template, utils, view


CSS_FILES = (
    "concerto_gui/css/jquery-ui.min.css",
    "concerto_gui/css/bootstrap.min.css",
    "concerto_gui/css/select2.min.css",
    "concerto_gui/css/select2-bootstrap.min.css",
    "concerto_gui/css/jquery-ui-timepicker-addon.min.css",
    "concerto_gui/css/font-awesome.min.css",
    "concerto_gui/css/ui.jqgrid.min.css",
    "concerto_gui/css/ui.multiselect.min.css"
)

JS_FILES = (
    "concerto_gui/js/json.js",
    "concerto_gui/js/jquery.js",
    "concerto_gui/js/jquery-ui.min.js",
    "concerto_gui/js/bootstrap.min.js",
    "concerto_gui/js/select2.full.min.js",
    "concerto_gui/js/functions.js",
    "concerto_gui/js/ajax.js",
    "concerto_gui/js/underscore-min.js",
    "concerto_gui/js/jquery-ui-timepicker-addon.min.js",
    "concerto_gui/js/ui.multiselect.js",
    "concerto_gui/js/jquery.jqgrid.min.js",
    "concerto_gui/js/commonlisting.js"
)


_BASEVIEW_TEMPLATE = template.ConcertoTemplate(__name__, 'templates/baseview.mak')


class BaseView(view._View):
    view_endpoint = "baseview.render"
    view_layout = None

    @view.route("/<path:path>/ajax_parameters_update", methods=["PUT", "PATCH"])
    def ajax_parameters_update(self, path):
        viewobj, vkw = env.viewmanager.get_view_by_path(path)
        viewobj.process_parameters()

        if viewobj.view_menu:
            view.GeneralParameters(viewobj, env.request.web.arguments)

        return response.ConcertoResponse(code=204)

    @view.route("/download/<int:id>/<filename>")
    @view.route("/download/<int:id>/<filename>/inline", defaults={"inline": True})
    @view.route("/download/<path:user>/<int:id>/<filename>")
    @view.route("/download/<path:user>/<int:id>/<filename>/inline", defaults={"inline": True})
    def download(self, user=None, id=None, filename=None, inline=False):
        if user and user != env.request.user.name:
            raise error.ConcertoUserError(_("Permission Denied"), message=_("Missing permission to access the specified file"), code=403)

        fd = open(utils.mkdownload.get_filename(id, filename, user), "rb")
        filename = base64.urlsafe_b64decode(filename.encode("utf8")).decode("utf8")

        return response.ConcertoDownloadResponse(fd, filename=filename, inline=inline)

    @view.route("/mainmenu")
    @view.route("/mainmenu/<datatype>")
    def mainmenu(self, datatype=None):
        kwargs = {}
        if datatype:
            kwargs["criteria_type"] = datatype

        return response.ConcertoResponse({"type": "content", "target": "#main_menu_ng", "content": mainmenu.HTMLMainMenu(**kwargs)})

    @staticmethod
    def _get_help_language(lang, default=None):
        for i in ("en", "fr"):
            if i in lang.lower():
                return i

        return default

    @staticmethod
    def _get_server():
        url = utils.url.urlparse(env.config.general.get("help_location"))
        if not url.netloc and not url.scheme and not url.path.startswith('/'):  # relative url
            return '/' + url.geturl()

        return url.geturl()

    @view.route("/help/<path:path>")
    def help(self, path=None):
        server = string.Template(self._get_server())

        lang = None
        if env.request.user:
            userl = env.request.user.get_property("language")
            if userl:
                lang = self._get_help_language(userl)

        if not lang:
            lang = self._get_help_language(env.config.general.default_locale, "en")

        return response.ConcertoRedirectResponse(server.safe_substitute(lang=lang, path=path))

    @view.route("/logout")
    def logout(self):
        try:
            env.session.logout(env.request.web)
        except:
            # logout always generate an exception to render the logout template
            pass

        return response.ConcertoRedirectResponse(env.request.parameters.get("redirect", env.request.web.get_baseurl()))

    @view.route("/history/<form>/save", methods=["POST"])
    def history_save(self, form):
        if "query" in env.request.parameters:
            history.save(env.request.user, form, env.request.parameters["query"])

        return response.ConcertoResponse()

    @view.route("/history/<form>/get", methods=["POST"])
    def history_get(self, form):
        queries = history.get(env.request.user, form)
        return response.ConcertoResponse(queries)

    @view.route("/history/<form>/delete", methods=["POST"])
    def history_delete(self, form):
        query = env.request.parameters["query"] if "query" in env.request.parameters else None
        history.delete(env.request.user, form, query)

        return response.ConcertoResponse()

    def _prepare(self, dataset):
        # FIXME: move theme management to a plugin !
        if env.request.user:
            theme = env.request.user.get_property("theme", default=env.config.general.default_theme)
            lang = env.request.user.get_property("language", default=env.config.general.default_locale)
        else:
            theme = env.config.general.default_theme
            lang = env.config.general.default_locale

        _HEAD = collections.OrderedDict((resource.CSSLink(link), True) for link in CSS_FILES)
        _HEAD[resource.CSSLink("concerto_gui/css/themes/%s.css" % theme)] = True
        _HEAD.update((resource.JSLink(link), True) for link in JS_FILES)

        # The jqgrid locale files use only two characters for identifying the language (e.g. pt_BR -> pt)
        _HEAD[resource.JSLink("concerto_gui/js/locales/jqgrid/grid.locale-%s.js" % lang[:2])] = True
        _HEAD[resource.JSLink("concerto_gui/js/locales/select2/%s.js" % lang[:2])] = True

        for contents in filter(None, hookmanager.trigger("HOOK_LOAD_HEAD_CONTENT")):
            _HEAD.update((i, True) for i in contents)

        _BODY = collections.OrderedDict()
        for contents in filter(None, hookmanager.trigger("HOOK_LOAD_BODY_CONTENT")):
            _BODY.update((i, True) for i in contents)

        if not dataset:  # In case of error, we use the exception dataset
            dataset = _BASEVIEW_TEMPLATE.dataset()

        self._setup_dataset_default(dataset)
        dataset["document"].head_content = _HEAD
        dataset["document"].body_content = _BODY
        dataset["document"].lang = lang[:2]
        dataset["toplayout_extra_content"] = filter(None, hookmanager.trigger("HOOK_TOPLAYOUT_EXTRA_CONTENT"))

        return dataset.render()

    def respond(self, dataset=None, code=None):
        return response.ConcertoResponse(self._prepare(dataset), code=code)
