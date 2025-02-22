# Copyright (C) 2022 Concerto SIEM. All Rights Reserved.
# Author: Maxime Rebon <maxime.rebon@gmail.com>

# Copyright (C) 2019-2020 CS GROUP - France. All Rights Reserved.
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

from concerto_gui import registrar, usergroup


class CLIManager(object):
    def __init__(self):
        self._commands = {}

    def _register(self, command, category, method, permissions, help, **options):
        d = self._commands.setdefault(command, {})
        if category not in d:
            # Avoid replacing methods by the ones from children classes
            d[category] = (method, permissions, help, options)

    def register(self, command, category, method=None, permissions=[], help=None, **options):
        usergroup.ALL_PERMISSIONS.declare(permissions)

        if method:
            self._register(command, category, method, permissions, help, **options)
        else:
            return registrar.DelayedRegistrar.make_decorator("cli", self._register, command, category, permissions=permissions, help=help, **options)

    def unregister(self, command=None, category=None):
        if command and category:
            self._commands[command].pop(category)
        elif command:
            self._commands.pop(command)
        else:
            self._commands = {}

    def get(self, command):
        return self._commands.get(command, {})


cli = CLIManager()
get = cli.get
register = cli.register
unregister = cli.unregister
