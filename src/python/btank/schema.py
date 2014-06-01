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


setup_project_schema = KeyValueStoreSchema(root_key, dict('studio_bootstrap_path' : Path,
                                                          'studio_configuration_uri' : str))
