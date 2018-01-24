"""
  ______                __   _____ __        __
 /_  __/________ ______/ /__/ ___// /_____ _/ /______
  / / / ___/ __ `/ ___/ //_/\__ \/ __/ __ `/ __/ ___/
 / / / /  / /_/ / /__/ ,<  ___/ / /_/ /_/ / /_(__  )
/_/ /_/   \__,_/\___/_/|_|/____/\__/\__,_/\__/____/

"""
VERSION = (0, 5, 0, 'final', 0)

__title__ = 'django-trackstats'
__version_info__ = VERSION
__version__ = '.'.join(map(str, VERSION[:3])) + ('-{}{}'.format(
    VERSION[3], VERSION[4] or '') if VERSION[3] != 'final' else '')
__author__ = 'Raymond Penners'
__license__ = 'MIT'
__copyright__ = 'Copyright 2018 Raymond Penners and contributors'
