# Copyright (C) 2022 Concerto SIEM. All Rights Reserved.
# Author: Maxime Rebon <maxime.rebon@gmail.com>

# Copyright (C) 2015-2020 CS GROUP - France. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

import pkg_resources

from concerto_gui import hookmanager, resource, template, version, view


# FIXME: this really is a plugin and not a view. See #781

class Warning(view.View):
    plugin_name = "Warning"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Prelude Warning message")
    plugin_htdocs = (("warning", pkg_resources.resource_filename(__name__, 'htdocs')),)

    _template = template.ConcertoTemplate(__name__, "templates/warning.mak")

    @hookmanager.register("HOOK_LOAD_BODY_CONTENT")
    def _toplayout_extra_content(self):
        if env.request.user and not env.request.web.input_cookie.get("warning"):
            env.request.web.add_cookie("warning", "warning", 365 * 24 * 60 * 60)
            return next(hookmanager.trigger("HOOK_WARNING_CONTENT"), [resource.HTMLSource(self._template.render())])
