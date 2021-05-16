# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module
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
