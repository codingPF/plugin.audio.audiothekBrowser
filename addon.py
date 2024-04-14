# -*- coding: utf-8 -*-
"""
The main addon module

SPDX-License-Identifier: MIT

"""

# -- Imports ------------------------------------------------
import resources.lib.main as Main

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    PLUGIN = Main.Main()
    PLUGIN.run()
    del PLUGIN