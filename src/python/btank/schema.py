#-*-coding:utf-8-*-
"""
@package btank.schema
@brief contains kvstore schemas used throughout the package

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str

__all__ = ['setup_project_schema']

from bkvstore import KeyValueStoreSchema
from butility import Path

root_key = 'btank'


# this is primiarily for posix systems, but should work on windows as well.
setup_project_schema = KeyValueStoreSchema('%s.setup-project' % root_key, 
                                                     dict(bootstrapper = dict(posix_path   = Path,
                                                                              windows_path = Path),
                                                          tank = dict(windows_core_path = Path),
                                                          configuration_uri = str))
