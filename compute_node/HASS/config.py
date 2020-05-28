# This tools only for python2.X
# if u need the python3 version get in
# Github/..../BagusYusuf
#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import os
import ConfigParser as configparser


class config(object):
    _config_file = None

    @staticmethod
    def basicConfiguration(file_path):
        if not os.path.exists(file_path):
            raise Exception("File not found")

        config._config_file = configparser.ConfigParser()
        config._config_file.read(file_path)

    @staticmethod
    def getConfiguration(section, detail=None, default=None):
        if config._config_file is None:
            raise Exception("Configuration not set")

        if default is not None:
            returnValue = default

        if detail:
            try:
                returnValue = config._config_file.get(section, detail)
            except Exception as e:
                if default is not None:
                    return default
                else:
                    raise Exception(e)

            return returnValue

        return config._config_file.get(section)

    @staticmethod
    def getRawConfiguration():
        if config._config_file is None:
            raise Exception("Configuration not set")
        return config._config_file


def basicConfiguration(file_path):
    return config.basicConfiguration(file_path)


def getConfiguration(section, detail=None):
    return config.getConfiguration(section, detail)


def get(section, detail=None, default=None):
    return config.getConfiguration(section, detail, default)


def getint(section, detail=None, default=None):
    return int(get(section, detail, default))


def getRawConfiguration():
    return config.getRawConfiguration()
