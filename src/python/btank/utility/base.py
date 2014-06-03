#-*-coding:utf-8-*-
"""
@package btank.utility
@brief Various utilities for use with tank

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['core_hook_type', 'platform_tank_map', 'link_bootstrapper']

import inspect

import sys
import os

from butility import (Path,
                      octal)
from sgtk import Hook
from sgtk import loader


## Maps sys.platform to names used in tank and shotgun.
platform_tank_map = dict(darwin = 'mac',
                         linux  = 'linux',
                         linux2 = 'linux',
                         win32  = 'windows')

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

def link_bootstrapper(source, destination, posix=True):
    """Setup wrapper files for all platforms in the given destination_tree
    @param source the original wrapper's Path, absolute or relative
    usually something like .../bin/posix/anyname
    @destination full path to the new wrapper location, the directory must exist. It shouldn't use an extension,
    as we will set it accordingly in non-posix mode
    @param posix if True, we will create a symlink (requires posix), if false, we will make it work without and 
    adjust the file extension, if there is none
    @return newly and actually created location of destination"""
    source = Path(source)
    destination = Path(destination)
    if os.name == 'posix' and posix:
        source.symlink(destination)
        destination.chmod(octal('0555'))
    else:
        if not destination.ext():
            destination += '.py'
        # end 
        (destination.dirname() / '.bprocess_path').write_text(str(source))
        source.copyfile(destination)
    # end on windows, we cannot make the symlink

    return destination
    
