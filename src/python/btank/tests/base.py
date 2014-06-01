#-*-coding:utf-8-*-
"""
@package btank.tests.base
@brief general tank/btank testing utilities

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str

__all__ = ['TankTestCase']

import tank_test.tank_test_base
from butility.tests import TestCase
from butility import Path


# It's setting up just one work space - for now we just follow this example and live with tests that possibly
# influence each other.
##############################################
tank_test.tank_test_base.setUpModule()
##############################################

class TankTestCase(tank_test.tank_test_base.TankTestBase, TestCase):
    """Provides a fully mocked tank, see tk-core/tests/python/tank_test/example_tests.py for more"""
    __slots__ = ()

    fixture_root = Path(__file__)

# end class TankTestCase

