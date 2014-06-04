#-*-coding:utf-8-*-
"""
@package btank.tests.base
@brief general tank/btank testing utilities

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str

__all__ = ['TankTestCase', 'with_tank_sandbox']

from butility.tests import TestCase
from butility import (Path,
                      wraps)
from bshotgun.tests import ShotgunConnectionMock
from mock import patch

# ==============================================================================
## @name Utiltiies
# ------------------------------------------------------------------------------
## @{

# end class ShotgunConnectionMock

# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

def with_tank_sandbox(fun):
    """Imprison tank and make sure it cannot communicate to the outside world.
    The shotgun connection it receives will be a shotgun mock, which is provided to 
    the wrapped method as well as last argument.

    The mock has to be filled with infomration by you, depending on your requirements.
    In any case, possibly applied monkey patches will be undone.
    """
    def no_way(*args, **kwargs):
        raise AssertionError("You can't get out of the prison")
    # end

    sg_mock = ShotgunConnectionMock()

    def make_mock(*args, **kwargs):
        return sg_mock
    # end

    @wraps(fun)
    def outer(*args, **kwargs):
        args = list(args)
        args.append(sg_mock)
        return fun(*args, **kwargs)
    # end

    tsg = 'tank.util.shotgun'
    return patch.multiple(tsg, create_sg_app_store_connection=no_way, 
                               create_sg_connection=make_mock)(outer)

# end with_tank_sandbox


## -- End Decorators -- @}


# It's setting up just one work space - for now we just follow this example and live with tests that possibly
# influence each other.
# For now, we don't need it ... we could even consider using our own SetupTankProject as a fixture creator
##############################################
# tank_test.tank_test_base.setUpModule()
##############################################

class TankTestCase(TestCase):
    """Provides a fully mocked tank, see tk-core/tests/python/tank_test/example_tests.py for more"""
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

# end class TankTestCase

