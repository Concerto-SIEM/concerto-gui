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

import errno
import gc
import os
import socket
import time

import pkg_resources
import prelude
import preludedb
from concerto_gui import (auth, cli, config, database, dataprovider, error, history, hookmanager, link, localization,
                      log, menu, pluginmanager, renderer, resolve, response, siteconfig, usergroup, version, view)

try:
    from threading import Lock
except ImportError:
    from dummy_threading import Lock


_core_cache = {}
_core_cache_lock = Lock()


class Core(object):
    def __init__(self, filename=None, autoupdate=False):
        self.autoupdate = autoupdate
        env.auth = None  # In case of database error
        env.config = config.Config(filename)

        env.config.general.setdefault("default_theme", "concerto")
        env.config.general.setdefault("default_locale", "en_GB")
        env.config.general.setdefault("encoding", "UTF-8")
        env.config.general.setdefault("default_timezone", localization.get_system_timezone())
        env.config.general.reverse_path = env.config.general.get("reverse_path", "").rstrip("/")

        env.log = log.Log(env.config.log)
        env.log.info("Starting Concerto")

        env.dns_max_delay = env.config.general.get_float("dns_max_delay", 0.)

        if env.config.general.get_bool("external_link_new_window", True):
            env.external_link_target = "_blank"
        else:
            env.external_link_target = "_self"

        env.enable_details = env.config.general.get_bool("enable_details", False)

        env.host_details_url = env.config.general.get("host_details_url", "https://www.prelude-siem.com/host_details.php")
        env.port_details_url = env.config.general.get("port_details_url", "https://www.prelude-siem.com/port_details.php")
        env.reference_details_url = env.config.general.get("reference_details_url", "https://www.prelude-siem.com/reference_details.php")

        resolve.init()

        env.menumanager = None
        env.viewmanager = view.ViewManager()
        env.htdocs_mapping.update((("concerto_gui", pkg_resources.resource_filename(__name__, 'htdocs')),))

        self._reload_time = None
        self._reload_count = 0
        try:
            self._concerto_gui_initialized = False
            self._concerto_gui_init_if_needed()
        except:
            pass

    @staticmethod
    def from_config(path=None, threaded=False, autoupdate=False):
        global _core_cache
        global _core_cache_lock

        if not path:
            path = siteconfig.conf_dir + "/concerto_gui.conf"

        with _core_cache_lock:
            if path not in _core_cache:
                _core_cache[path] = Core(path, autoupdate)

        return _core_cache[path]

    def _load_custom_theme(self):
        custom_theme = env.config.interface.get("custom_theme")
        if custom_theme is None:
            return

        if os.path.isdir("%s%s" % (os.path.sep, custom_theme)):
            env.htdocs_mapping.update((("custom", custom_theme),))
        else:
            try:
                env.htdocs_mapping.update((("custom", pkg_resources.resource_filename(custom_theme, 'htdocs')),))
            except ImportError:
                raise config.ConfigValueError(custom_theme, "custom_theme")

    def _concerto_gui_init_if_needed(self):
        if self._concerto_gui_initialized is True:
            return self.reload_plugin_if_needed()

        try:
            self._load_custom_theme()
            self._check_version()
            env.db = database.ConcertoDatabase(env.config.database)
            history.init()
            self._load_plugins()
            self._concerto_gui_initialized = True
        except error.ConcertoError as e:
            self._concerto_gui_initialized = e
        except Exception as e:
            self._concerto_gui_initialized = error.ConcertoError(e, name=_("Initialization error"))
        finally:
            # Needed for Database object
            gc.collect()

        if isinstance(self._concerto_gui_initialized, Exception):
            env.log.log(self._concerto_gui_initialized.log_priority, text_type(self._concerto_gui_initialized))
            self._unregister_plugin_data()
            raise self._concerto_gui_initialized

    def _check_version(self):
        error_type = _("Version Requirement error")
        if not prelude.checkVersion(siteconfig.libprelude_required_version):
            raise error.ConcertoUserError(error_type,
                                          N_("Concerto %(vPre)s requires libprelude %(vLib)s or higher",
                                             {'vPre': version.__version__, 'vLib': siteconfig.libprelude_required_version}))

        elif not preludedb.checkVersion(siteconfig.libpreludedb_required_version):
            raise error.ConcertoUserError(error_type,
                                          N_("Concerto %(vPre)s requires libpreludedb %(vLib)s or higher",
                                             {'vPre': version.__version__, 'vLib': siteconfig.libpreludedb_required_version}))

    def _load_auth_or_session(self, typename, plugins, name, config=config.SectionRoot()):
        if name not in plugins:
            raise error.ConcertoUserError(
                N_("Initialization error"),
                N_("Cannot use %(type)s mode '%(name)s', please contact your local administrator.",
                   {'type': typename, 'name': name})
            )

        obj = plugins[name](config)
        setattr(env, typename, obj)
        obj.init(config)

    def _unregister_plugin_data(self):
        list(hookmanager.trigger("HOOK_PLUGINS_RELOAD"))
        hookmanager.unregister(exclude=["HOOK_PLUGINS_RELOAD"])
        cli.unregister()
        usergroup.ACTIVE_PERMISSIONS = usergroup.Permissions()

    def _load_plugins(self):
        env.pluginmanager = {}
        env.all_plugins = {}

        env.menumanager = menu.MenuManager()
        env.dataprovider = dataprovider.DataProviderManager(autoupdate=self.autoupdate)
        env.dataprovider.load()
        env.linkmanager = link.LinkManager()

        env.plugins = {}
        pluginmanager.SimplePluginManager("concerto_gui.plugins", autoupdate=self.autoupdate).load()

        # Load views before auth/session to find all permissions
        env.viewmanager.load_views(autoupdate=self.autoupdate)

        _AUTH_PLUGINS = pluginmanager.PluginManager("concerto_gui.auth", autoupdate=True)
        _SESSION_PLUGINS = pluginmanager.PluginManager("concerto_gui.session", autoupdate=True)
        cfg = env.config

        if cfg.session:
            self._load_auth_or_session("session", _SESSION_PLUGINS, cfg.session.get_instance_name(), cfg.session)
            if isinstance(env.session, auth.Auth):
                # If the session module is also an auth module, no need to load an auth module
                env.auth = env.session
                if cfg.auth:
                    env.log.error(_("Session '%s' does not accept any authentication module" % cfg.session.get_instance_name()))
            else:
                # If no authentification module defined, we use the session's default auth module
                auth_name = cfg.auth.get_instance_name() if cfg.auth else env.session.get_default_auth()
                self._load_auth_or_session("auth", _AUTH_PLUGINS, auth_name, cfg.auth)
        elif cfg.auth:
            # No session module defined, we load the auth module first
            self._load_auth_or_session("auth", _AUTH_PLUGINS, cfg.auth.get_instance_name(), cfg.auth)
            self._load_auth_or_session("session", _SESSION_PLUGINS, env.auth.get_default_session())
        else:
            # Nothing defined, we use the anonymous module
            self._load_auth_or_session("session", _SESSION_PLUGINS, "anonymous")
            env.auth = env.session

        env.renderer = renderer.RendererPluginManager(autoupdate=self.autoupdate)
        env.renderer.load()
        list(hookmanager.trigger("HOOK_PLUGINS_LOAD"))

    def reload_plugin_if_needed(self):
        if env.db.has_plugin_changed():
            # Some changes happened, and every process has to reload the plugin configuration
            env.log.warning("plugins were activated: triggering reload")
            self._unregister_plugin_data()
            try:
                history.init()
                self._load_plugins()
            finally:
                # Needed for Database object
                gc.collect()

        elif self._reload_count < 10 and (not self._reload_time or time.time() > self._reload_time + 30 * 2**self._reload_count):
            # Reload plugins in error
            self._reload_time = time.time()
            self._reload_count += 1

            for entrypoint in ("concerto_gui.dataprovider.type", "concerto_gui.plugins", "concerto_gui.views"):
                env.pluginmanager[entrypoint].load(reloading=True)

            list(hookmanager.trigger("HOOK_PLUGINS_PARTIAL_RELOAD"))

    def _redirect_default(self, request):
        if env.menumanager.default_endpoint:
            url = url_for(env.menumanager.default_endpoint)
        else:
            # The configured view does not exist. Fall back to "settings/my_account"
            # which does not require any specific permission.
            url = request.get_baseurl() + "settings/my_account"

        return response.ConcertoRedirectResponse(url)

    def _process_static(self, webreq):
        pathkey = webreq.path_elements[0]
        endpath = webreq.path[len(pathkey) + 2:]

        mapping = env.htdocs_mapping.get(pathkey, None)
        if not (mapping and endpath and "." in webreq.path_elements[-1]):
            # There is no mapping, or no path beyond the mapped portion was provided.
            # FIXME: .ext check is not clean: proper way to handle this would be to map statics
            # files to a /static base directory
            return

        path = os.path.abspath(os.path.join(mapping, endpath))
        if not path.startswith(mapping):
            return response.ConcertoResponse(code=403, status_text="Request Forbidden")

        try:
            return response.ConcertoFileResponse(path)
        except OSError:
            return response.ConcertoResponse(code=404, status_text="File not found")

    def _process_dynamic(self, webreq):
        self._concerto_gui_init_if_needed()

        # Some newly loaded plugin from another request may have modified globally loadeds
        # JS/CSS scripts. We thus need to call _process_static() again after _concerto_gui_init_if_needed()
        response = self._process_static(webreq)
        if response:
            return response

        autherr = None
        try:
            env.request.user = env.session.get_user(webreq)
            env.request.user.set_locale()
        except error.ConcertoError as e:
            autherr = e
            pass

        if webreq.path == "/":
            return self._redirect_default(webreq)

        try:
            view_object = env.viewmanager.load_view(webreq, env.request.user)
        except Exception as err:
            raise autherr or err

        if view_object.view_require_session and autherr:
            view_object = autherr

        resolve.process(env.dns_max_delay)
        ret = view_object.respond()
        if env.request.user:
            env.request.user.sync_properties()

        return ret

    def process(self, webreq):
        env.request.init(webreq)

        try:
            response = self._process_static(webreq) or self._process_dynamic(webreq)

        except error.ConcertoException as err:
            response = err.respond()

        except Exception as err:
            response = error.ConcertoError(
                N_("An unexpected condition happened while trying to load %s", webreq.path),
                details=err
            ).respond()

        try:
            webreq.send_response(response)
        except socket.error as e:
            if e.errno != errno.EPIPE:
                raise
        finally:
            env.request.cleanup()
