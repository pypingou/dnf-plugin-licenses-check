# licenses_check
# Automatically check the licenses of the packages that are being pulled and fail
# to install any packages that are licensed under licenses considered not acceptable.
#
# Copyright (C) 2024 Pierre-Yves Chibon
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from __future__ import absolute_import
from __future__ import unicode_literals
from dnf.i18n import ucd
from dnfpluginscore import _, logger

import dnf
import dnf.cli
import os
import shutil
import subprocess
from configparser import ConfigParser


def parse_config(config_file):
    conf = ConfigParser()
    conf.read(config_file)
    main= {"allowed_packages":{}, "blocked_licenses":{}}

    if not conf.has_section("main"):
        raise KeyError("Missing section 'main'")
    if conf.has_option("main", "allowed_packages"):
        main["allowed_packages"] = set(
            [i.strip() for i in conf.get("main", "allowed_packages").split(",")]
        )
    if conf.has_option("main", "blocked_licenses"):
        main["blocked_licenses"] = set(
            [i.strip() for i in conf.get("main", "blocked_licenses").split(",")]
        )

    return main


class LicensesCheck(dnf.Plugin):

    def __init__(self, base, cli):
        super(LicensesCheck, self).__init__(base, cli)
        self.base = base
        self.logger = logger
        self.conf = {}

    def pre_config(self):

        config_files = []
        config_path = self.base.conf.pluginconfpath[0]

        default_config_file = os.path.join(config_path, "licenses_check.conf")
        # would use appdirs, but that would mean a new dependency
        vendor_config_file = "/usr/share/dnf/plugins/licenses_check.vendor.conf"

        if os.path.isfile(default_config_file):
            config_files.append(default_config_file)

        if os.path.isfile(vendor_config_file):
            conf = parse_config(vendor_config_file)
        else:
            conf = parse_config(default_config_file)

        self.conf = conf

    def resolved(self):
        for pkg in list(self.base.transaction.install_set):
            for blicense in self.conf["blocked_licenses"]:
                if blicense.lower() in pkg.license.lower() \
                        and pkg.name not in self.conf["allowed_packages"]:
                    raise dnf.exceptions.Error(
                        f"Package {pkg.name} has a license not allowed: {pkg.license}"
                    )

