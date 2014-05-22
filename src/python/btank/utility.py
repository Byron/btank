#-*-coding:utf-8-*-
"""
@package btank.utility
@brief Various utilities for use with tank

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['core_hook_type']

import inspect

import sys
import os

from butility import Path
from sgtk import Hook
from sgtk import loader


def core_hook_type():
    """When executed from a core hook, it will return the BaseType from which your core hook
    should derive from.
    @throws TypeError if a core-hook base type couldn't be found.
    @note this works around an issue with tank being unable to provide base types for core hooks,
    as they are special. Therefore, sgtk.get_hook_baseclass() either returns Hook only, or 
    your own type.
    """
    calling_module = Path(inspect.currentframe().f_back.f_globals['__file__'])
    tank_root = Path(sys.modules[Hook.__module__].__file__).dirname().dirname().dirname()
    base_hook_file = tank_root / 'hooks' / (calling_module.namebase() + '.py')
    return loader.load_plugin(base_hook_file , Hook)
    
