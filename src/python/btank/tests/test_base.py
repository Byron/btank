#-*-coding:utf-8-*-
"""
@package btank.tests.test_base
@brief general tests for btank

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str
__all__ = []

from .base import TankTestCase


# Just try utility import
from btank.utility import *


class BasicTests(TankTestCase):
    __slots__ = ()

    def test_base(self):
        # nothing for now
        pass

    

# end class BasicTests
