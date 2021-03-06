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

from butility import Path
from sgtk import Hook
from sgtk import loader

from bprocess.bootstrap import Bootstrapper


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

def link_bootstrapper(source, destination, posix=True, symlink_source=None, append=True, enforce_winlink_entry=False):
    """Setup wrapper files for all platforms in the given destination_tree
    @param source the original wrapper's Path, absolute or relative
    usually something like .../bin/posix/anyname.
    It SHOULD be readable by the current program, as it may be copied to the destination in case symlinks are 
    not supported.
    @destination full path to the new wrapper location, the directory must exist. It should contain the .py
    extension on windows for usability
    @param posix if True, we will create a symlink (requires posix compatible filesystems), otherwise
    we will make it work without.
    However, if the symlink creation fails, we will resort to using  a 'winlink' on posix systems as well.
    @param symlink_source if unset, it defaults to source. Otherwise, if the platform creating the symlink 
    is not the platform using them, the path to compute the symlink can be explicitly provided.
    It's the path used to reach the source bootstrapper from destination, and you want to use this if the 
    symlink should be relative. The latter can be computed as well, but it's difficult in a multi-platform scenario,
    so we keep things explicit here
    @param append if True, and if a windows compatible symlink is created, we will append to the file. This is useful
    if different platforms have different (possibly absolute) locations at which to find their bootstrapper.
    @param enforce_winlink_entry if True, the pseudo symlink file used on smb or windows shares is always written
    with the respective symlink_source, which is useful if the process has a posix filesystem, which is shared as 
    smb to others which renders symbolic links working, but not unreadable.
    This is only relevant for posix bootstrapper links
    @return newly and actually created location of destination"""
    source = Path(source)
    destination = Path(destination)
    symlink_source = symlink_source or source

    def make_winlink(copy=True):
        """create a file-based symlink"""
        (destination.dirname() / Bootstrapper.boot_info_file).write_text(str(symlink_source + '\n'), append=append)
        if copy:
            source.copyfile(destination)
    # end utility

    if os.name == 'posix' and posix:
        try:
            symlink_source.symlink(destination)
            if enforce_winlink_entry:
                make_winlink(copy=False)
            # end handle enforce winlink
        except OSError:
            # In this case, even on linux we may have to use fake symlinks. To us, it doesn't matter really
            make_winlink()
        # end handle no link possible
    else:
        make_winlink()
    # end on windows, we cannot make the symlink

    return destination
    
