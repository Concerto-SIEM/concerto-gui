# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


import sys
import os, os.path

import copy

from prewikka import Config, Log, Prelude, Interface


class Core:
    def __init__(self):
        self.content_modules = { }
        self._content_module_names = [ ]
        self._config = Config.Config()
        self.interface = Interface.Interface(self, self._config.get("interface", { }))
        self.log = Log.Log()
        self.prelude = Prelude.Prelude(self._config["prelude"])
        self.auth = None
        self._initModules()
        
    def shutdown(self):
        # Core references objects that themself reference Core, those circular
        # references mean that garbage collector won't destroy those objects.
        # Thus, code that use Core must call the shutdown method (that remove
        # Core references) so that cleanup code (__del__ object methods) will be called
        self.content_modules = None
        self._content_module_names = None
        self._config = None
        self.interface = None
        self.log = None
        self.prelude = None
        self.auth = None
        
    def registerAuth(self, auth):
        self.auth = auth
        
    def _initModules(self):
        base_dir = "prewikka/modules/"
        for mod_name in self._config.getModuleNames():
            try:
                file = base_dir + mod_name + "/" + mod_name
                module = __import__(file)
                module.load(self, self._config.modules.get(mod_name, { }))
            except ImportError:
                print >> sys.stderr, "cannot load module named %s (%s)" % (mod_name, file)
                raise
        
    def process(self, request):
        view = self.interface.process(request)
        
        request.content = view
        request.sendResponse()
