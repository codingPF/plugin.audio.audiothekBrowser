# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
"""


def init():
    global LOGGER
    global SETTINGS
    global ADDONCLASS


def initAddon(aAddon):
    global ADDONCLASS
    ADDONCLASS = aAddon


def initLogger(aLogger):
    global LOGGER
    LOGGER = aLogger


def initSettings(aSettings):
    global SETTINGS
    SETTINGS = aSettings
