#!/usr/bin/env python

# Copyright (C) 2022 Concerto SIEM. All Rights Reserved.
# Author: Maxime Rebon <maxime.rebon@gmail.com>

# Copyright (C) 2005-2020 CS GROUP - France. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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

from glob import glob
import io
import os
import stat
import subprocess
import sys
import tempfile

from setuptools import Command, setup, find_packages
from setuptools.command.test import test as TestCommand
from distutils.dist import Distribution
from distutils.command.install import install
from distutils.dep_util import newer
from distutils.command.build import build as _build


LIBPRELUDE_REQUIRED_VERSION = "5.2.0"
LIBPRELUDEDB_REQUIRED_VERSION = "5.2.0"


def init_siteconfig(conf_prefix, data_prefix):
    """
    Initialize configuration file (Concerto/siteconfig.py).

    :param str conf_prefix: configuration path
    :param str data_prefix: data path
    """
    configuration = (
        ('tmp_dir', os.path.join(tempfile.gettempdir(), 'concerto_gui')),
        ('conf_dir', os.path.abspath(conf_prefix)),
        ('data_dir', os.path.abspath(data_prefix)),
        ('libprelude_required_version', LIBPRELUDE_REQUIRED_VERSION),
        ('libpreludedb_required_version', LIBPRELUDEDB_REQUIRED_VERSION),
    )

    with open('concerto_gui/siteconfig.py', 'w') as config_file:

        for option, value in configuration:
            config_file.write("%s = '%s'\n" % (option, value))


class MyDistribution(Distribution):
    def __init__(self, attrs):
        try:
            os.remove("concerto_gui/siteconfig.py")
        except:
            pass

        self.conf_files = {}
        self.closed_source = os.path.exists("PKG-INFO")
        Distribution.__init__(self, attrs)


class my_install(install):
    def finalize_options(self):
        # if no prefix is given, configuration should go to /etc or in {prefix}/etc otherwise
        if self.prefix:
            self.conf_prefix = self.prefix + "/etc/concerto_gui"
            self.data_prefix = self.prefix + "/var/lib/concerto_gui"
        else:
            self.conf_prefix = "/etc/concerto_gui"
            self.data_prefix = "/var/lib/concerto_gui"

        install.finalize_options(self)

    def get_outputs(self):
        tmp = [self.conf_prefix + "/concerto_gui.conf"] + install.get_outputs(self)
        return tmp

    def install_conf(self):
        self.mkpath((self.root or "") + self.conf_prefix + "/conf.d")
        for dest_dir, patterns in self.distribution.conf_files.items():
            for pattern in patterns:
                for f in glob(pattern):
                    dest = (self.root or "") + self.conf_prefix + "/" + dest_dir + "/" + os.path.basename(f)
                    if os.path.exists(dest):
                        dest += "-dist"
                    self.copy_file(f, dest)

    def create_datadir(self):
        self.mkpath((self.root or "") + self.data_prefix)

    def install_wsgi(self):
        share_dir = os.path.join(self.install_data, 'share', 'concerto_gui')
        if not os.path.exists(share_dir):
            os.makedirs(share_dir)

        ofile, copied = self.copy_file('scripts/concerto.wsgi', share_dir)

    def run(self):
        os.umask(0o22)
        self.install_conf()
        self.install_wsgi()
        self.create_datadir()
        init_siteconfig(self.conf_prefix, self.data_prefix)
        install.run(self)

        os.chmod((self.root or "") + self.conf_prefix, 0o755)

        if not self.dry_run:
            for filename in self.get_outputs():
                if filename.find(".conf") != -1:
                    continue
                mode = os.stat(filename)[stat.ST_MODE]
                mode |= 0o44
                if mode & 0o100:
                    mode |= 0o11
                os.chmod(filename, mode)


class build(_build):
    sub_commands = [('compile_catalog', None), ('build_custom', None)] + _build.sub_commands


class build_custom(Command):
    @staticmethod
    def _need_compile(template, outfile):
        if os.path.exists(outfile) and not any(newer(tmpl, outfile) for tmpl in template):
            return False

        directory = os.path.dirname(outfile)
        if not os.path.exists(directory):
            print("creating %s" % directory)
            os.makedirs(directory)

        print("compiling %s -> %s" % (template, outfile))
        return True

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        style = os.path.join("concerto_gui", "htdocs", "css", "style.less")

        for less in glob("themes/*.less"):
            css = os.path.join("concerto_gui", "htdocs", "css", "themes", "%s.css" % os.path.basename(less[:-5]))
            if self._need_compile([less, style], css):
                io.open(css, "wb").write(subprocess.check_output(["lesscpy", "-I", less, style]))


class ConcertoTest(TestCommand):
    """
    Custom command test suite with pytest.

    Based on
    https://docs.pytest.org/en/2.7.3/goodpractises.html#integration-with-setuptools-test-commands
    """
    user_options = [
        ('pytest-args=', 'a', 'Arguments to pass to pytest')
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        init_siteconfig('conf', 'tests/downloads')

        import pytest  # import here, cause outside the eggs aren't loaded

        if not isinstance(self.pytest_args, list):
            self.pytest_args = self.pytest_args.split()

        errno = pytest.main(self.pytest_args + ['tests'])
        sys.exit(errno)


class ConcertoCoverage(Command):
    """
    Coverage command.
    """
    user_options = [
        ('run-args=', None, 'Arguments to pass to coverage during run'),
        ('report-args=', None, 'Arguments to pass to coverage for report')
    ]
    description = 'Run tests with coverage.'

    def initialize_options(self):
        self.run_args = []
        self.report_args = []

    def finalize_options(self):
        pass

    def run(self):
        subprocess.call(['coverage', 'run', 'setup.py', 'test'] + self.run_args)
        subprocess.call(['coverage', 'report'] + self.report_args)


setup(
    name="concerto_gui",
    version="5.2.0",
    maintainer="Concerto",
    maintainer_email="concerto-siem@gmail.com",
    url="https://concerto-siem.github.io",
    packages=find_packages(exclude=[
        'tests',
        'tests.*'
    ]),
    setup_requires=[
        'Babel'
    ],
    entry_points={
        'concerto_gui.renderer.backend': [
            'ChartJS = concerto_gui.renderer.chartjs:ChartJSPlugin',
        ],
        'concerto_gui.renderer.type': [
            'ChartJSBar = concerto_gui.renderer.chartjs.bar:ChartJSBarPlugin',
            'ChartJSDoughnut = concerto_gui.renderer.chartjs.pie:ChartJSDoughnutPlugin',
            'ChartJSPie = concerto_gui.renderer.chartjs.pie:ChartJSPiePlugin',
            'ChartJSTimebar = concerto_gui.renderer.chartjs.timeline:ChartJSTimebarPlugin',
            'ChartJSTimeline = concerto_gui.renderer.chartjs.timeline:ChartJSTimelinePlugin',
        ],
        'concerto_gui.dataprovider.backend': [
            'ElasticsearchLog = concerto_gui.dataprovider.plugins.log.elasticsearch:ElasticsearchLogPlugin',
            'IDMEFAlert = concerto_gui.dataprovider.plugins.idmef:IDMEFAlertPlugin',
            'IDMEFHeartbeat = concerto_gui.dataprovider.plugins.idmef:IDMEFHeartbeatPlugin',
        ],
        'concerto_gui.dataprovider.type': [
            'alert = concerto_gui.dataprovider.idmef:IDMEFAlertProvider',
            'heartbeat = concerto_gui.dataprovider.idmef:IDMEFHeartbeatProvider',
            'log = concerto_gui.dataprovider.log:LogAPI',
        ],
        'concerto_gui.plugins': [
        ],
        'concerto_gui.auth': [
            'DBAuth = concerto_gui.auth.dbauth:DBAuth',
        ],
        'concerto_gui.session': [
            'Anonymous = concerto_gui.session.anonymous:AnonymousSession',
            'LoginForm = concerto_gui.session.loginform:LoginFormSession',
        ],
        'concerto_gui.views': [
            'About = concerto_gui.views.about:About',
            'AboutPlugin = concerto_gui.views.aboutplugin:AboutPlugin',
            'AgentPlugin = concerto_gui.views.agents:AgentPlugin',
            'AlertDataSearch = concerto_gui.views.datasearch.alert:AlertDataSearch',
            'AlertStats = concerto_gui.views.statistics.alertstats:AlertStats',
            'CrontabView = concerto_gui.views.crontab:CrontabView',
            'Custom = concerto_gui.views.custom:Custom',
            'FilterPlugin = concerto_gui.plugins.filter:FilterPlugin',
            'HeartbeatDataSearch = concerto_gui.views.datasearch.heartbeat:HeartbeatDataSearch',
            'IDMEFnav = concerto_gui.views.idmefnav:IDMEFNav',
            'LogDataSearch = concerto_gui.views.datasearch.log:LogDataSearch',
            'MessageSummary = concerto_gui.views.messagesummary:MessageSummary',
            'RiskOverview = concerto_gui.views.riskoverview:RiskOverview',
            'Statistics = concerto_gui.views.statistics:Statistics',
            'UserManagement = concerto_gui.views.usermanagement:UserManagement',
            'Warning = concerto_gui.plugins.warning:Warning',
        ],
        'concerto_gui.updatedb': [
            'concerto_gui = concerto_gui.sql',
            'concerto_gui.auth.dbauth = concerto_gui.auth.dbauth.sql',
            'concerto_gui.plugins.filter = concerto_gui.plugins.filter.sql'
        ]
    },
    package_data={
        '': [
            "htdocs/css/*.*",
            "htdocs/css/themes/*.css",
            "htdocs/css/images/*.*",
            "htdocs/fonts/*.*",
            "htdocs/images/*.*",
            "htdocs/js/*.js",
            "htdocs/js/locales/*.js",
            "htdocs/js/locales/*/*.js",
            "htdocs/js/*.map",
            "htdocs/js/locales/*.map",
            "locale/*.pot",
            "locale/*/LC_MESSAGES/*.mo",
            "sql/*.py",
            "templates/*.mak"
        ],
        'concerto_gui.auth.dbauth': ["sql/*.py"],
        'concerto_gui.renderer.chartjs': ["htdocs/js/*.js"],
        'concerto_gui.session.loginform': ["htdocs/css/*.css"],
        'concerto_gui.views.about': ["htdocs/css/*.css", "htdocs/images/*.png"],
        'concerto_gui.views.aboutplugin': ["htdocs/css/*.css"],
        "concerto_gui.views.idmefnav": ["htdocs/yaml/*.yml", "htdocs/graph/*"],
        'concerto_gui.views.riskoverview': ["htdocs/js/*.js"],
        'concerto_gui.views.statistics': ["htdocs/js/*.js", "htdocs/css/*.css"],
        'concerto_gui.views.usermanagement': ["htdocs/js/*.js", "htdocs/css/*.css"],
    },
    scripts=[
        "scripts/concerto-cli",
        "scripts/concerto-crontab",
        "scripts/concerto-httpd"
    ],
    conf_files={
        "": ["conf/concerto_gui.conf", "conf/menu.yml"],
        "conf.d": ["conf/plugins/*.conf"]
    },
    cmdclass={
        'build': build,
        'build_custom': build_custom,
        'coverage': ConcertoCoverage,
        'install': my_install,
        'test': ConcertoTest,
    },
    tests_require=[
        'pytest'
    ],
    distclass=MyDistribution,
    message_extractors={
        'scripts': [
            ('concerto-cli', 'python', None),
            ('concerto-httpd', 'python', None),
            ('concerto-crontab', 'python', None)
        ],
        'concerto_gui': [
            ('**.py', 'python', None),
            ('**/templates/*.mak', 'mako', None)
        ]
    }
)
