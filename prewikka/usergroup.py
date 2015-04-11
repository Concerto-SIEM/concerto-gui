# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
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

import abc, hashlib
from prewikka import config, error, log, localization, env


PERM_IDMEF_VIEW = "IDMEF_VIEW"
PERM_IDMEF_ALTER = "IDMEF_ALTER"
PERM_TICKET_CREATE = "TICKET_CREATE"
PERM_TICKET_ALTER = "TICKET_ALTER"
PERM_TICKET_VIEW = "TICKET_VIEW"
PERM_ADMIN_CONSOLE = "ADMIN_CONSOLE"
PERM_USER_MANAGEMENT = "USER_MANAGEMENT"
PERM_GROUP_MANAGEMENT = "GROUP_MANAGEMENT"
PERM_COMMAND = "COMMAND"
PERM_INTRUSIVE_COMMAND = "INTRUSIVE_COMMAND"
PERM_ASSET_CREATE = "ASSET_GROUP_CREATE"
PERM_ASSET_ALTER = "ASSET_GROUP_ALTER"

ALL_PERMISSIONS = [ PERM_IDMEF_VIEW,
                    PERM_IDMEF_ALTER,
                    PERM_TICKET_CREATE,
                    PERM_TICKET_ALTER,
                    PERM_TICKET_VIEW,
                    PERM_ADMIN_CONSOLE,
                    PERM_USER_MANAGEMENT,
                    PERM_GROUP_MANAGEMENT,
                    PERM_COMMAND,
                    PERM_INTRUSIVE_COMMAND,
                    PERM_ASSET_CREATE,
                    PERM_ASSET_ALTER ]

config = config.Config()
for perm in config.section_permissions:
    if perm not in ALL_PERMISSIONS:
        ALL_PERMISSIONS.append(perm)

ADMIN_LOGIN = "admin"


class PermissionDeniedError(error.PrewikkaUserError):
    def __init__(self, action_name):
        error.PrewikkaUserError.__init__(self, _("Permission Denied"),
                                         _("Access to view '%s' forbidden") % action_name, log_priority=log.WARNING)


_NAMEID_TBL = {}


class NameID(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name=None, nameid=None):
        assert(name or nameid)

        self._id = nameid
        self._name = name

    @property
    def id(self):
        if self._id is None:
            self._id = self._name2id(self._name)

        return self._id

    @property
    def name(self):
        if self._name is None:
            self._name = self._id2name(self._id)

        return self._name

    @abc.abstractmethod
    def _id2name(self, name):
        pass

    def _name2id(self, name):
        md5 = _NAMEID_TBL.get(name)
        if md5:
            return md5

        md5 = _NAMEID_TBL[name] = hashlib.md5(name).hexdigest()
        return md5

    def __eq__(self, other):
        if not other:
            return False

        return self.id == other.id

    def __hash__(self):
        return int(self.id, 16)

    def __str__(self):
        return self.name


class Group(NameID):
    def __init__(self, name=None, groupid=None):
        NameID.__init__(self, name, groupid)

    def _id2name(self, id):
        return env.auth.hasGroup(self)


class User(NameID):
    __sentinel = object()

    def __init__(self, login=None, userid=None):
        NameID.__init__(self, login, userid)
        self._configuration = self._permissions = None

    def _id2name(self, id):
        return env.auth.hasUser(self)

    @property
    def permissions(self):
        if self._permissions is None:
            self._permissions = env.auth.getUserPermissions(self)

        return self._permissions

    @permissions.setter
    def permissions(self, permissions):
        env.auth.setUserPermissions(self, permissions)
        self._permissions = permissions

    @property
    def configuration(self):
        if self._configuration is None:
            self._configuration = env.db.get_properties(self)

        return self._configuration

    def set_locale(self):
        lang = self.get_property("language", default=env.default_locale)
        if lang:
            localization.setLocale(lang)

    def del_property(self, key, view=None):
        if not key:
            self.configuration.pop(view, None)
        else:
            self.configuration.get(view, {}).pop(key, None)

        env.db.del_property(self, key, view=view)

    def del_properties(self, view):
        self.configuration.pop(view, None)
        env.db.del_properties(self, view=view)

    def del_property_match(self, key, view=None):
        viewlist = [view] if view else self.configuration.keys()

        for v in viewlist:
            if not v in self.configuration:
                continue

            for k in self.configuration[v].keys():
                if k.find(key) != -1:
                    self.del_property(k, view=v)

    def get_property_fail(self, key, view=None, default=__sentinel):
        view = self.configuration.get(view, {})

        if default is not self.__sentinel:
            return view.get(key, default)

        return view[key]

    def get_property(self, key, view=None, default=None):
        return self.get_property_fail(key, view, default)

    def set_property(self, key, value, view=None):
        env.db.set_property(self, key, value, view)
        self.configuration.setdefault(view, {})[key] = value

    def has(self, perm):
        if type(perm) in (list, tuple):
            return filter(lambda p: self.has(p), perm) == perm

        return perm in self.permissions
