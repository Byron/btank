#-*-coding:utf-8-*-
"""
@package btank.tests.test_base
@brief general tests for btank

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
# Can't use this, as dict lookups don't work the same way. Mixing is not a good idea here ... 
# This stays python 2 !
# from __future__ import unicode_literals
# from butility.future import str
__all__ = []

import os
import logging
from copy import deepcopy

from mock import Mock

from .base import TankTestCase
import bapp
from butility.tests import with_rw_directory
from butility import (DictObject,
                      Path,
                      DEFAULT_ENCODING)
from bapp.tests import with_application
from bcontext import ApplyChangeContext

from tank.util import shotgun
import tank.platform.constants as constants

log = logging.getLogger('btank.tests.test_base')


# from * import
from btank.commands import *



class CommandTests(TankTestCase):

    # -------------------------
    ## @name Command Implementation
    # @{

    def _project_storage_names(self, *args):
        return ['primary']

    ## -- End Command Implementation -- @}

    def setUp(self, *args, **kwargs):
        """Make sure shotgun app store connections are mocked as well"""
        super(CommandTests, self).setUp(*args, **kwargs)

        def no_way(*args, **kwargs):
            raise AssertionError("You can't get out of the prison")
        # end
        shotgun.create_sg_app_store_connection = no_way

        # Fix the mock db - it must copy return values, no matter what !
        class CopyDict(dict):
            __slots__ = ()
            
            def __getitem__(self, name):
                return deepcopy(super(CopyDict, self).__getitem__(name))

            def values(self):
                return deepcopy(super(CopyDict, self).values())

        # end class CopyDict


        self._sg_mock_db = CopyDict()

    # -------------------------
    ## @name Utilities
    # @{

    def _setup_bootstrapper_at(self, tree, name):
        """Setup wrapper files for all platforms in the given directory
        @param tree an existing directory to write to
        @param name of the wrapper executable (like 'btank')
        @return (posix_wrapper, windows_wrapper)"""
        import bprocess.bootstrap
        posix_wrapper_location = tree / name
        bootrapper_path = Path(bprocess.bootstrap.__file__)
        if os.name == 'posix':
            bootrapper_path.symlink(posix_wrapper_location)
        else:
            posix_wrapper_location.write_text("Just a dummy, can't do fancy symlinks on windows")
        # end on windows, we cannot make the symlink

        win_wrapper_location = posix_wrapper_location + '.py'
        (tree / '.bprocess_path').write_text(str(bootrapper_path))
        bootrapper_path.copyfile(win_wrapper_location)

        return posix_wrapper_location, win_wrapper_location

    def _default_configuration_tree(self):
        """@return existing Path to the default configuration
        @throws AssertionError if it's not there"""
        config_tree = self.fixture_path('tank-default-config')
        setup_fixtures = self.fixture_path('setup_fixtures')
        if not config_tree.isdir():
            msg = "missing default tank configuration - execute %s and retry" % setup_fixtures
            raise AssertionError(msg)
        # end check dir

        if not (config_tree / 'core' / 'templates.yml').isfile():
            msg = "%s doesn't look like a valid tank configuration - possibly remove and rerun %s" % (config_tree,
                                                                                                      setup_fixtures)
            raise AssertionError(msg)
        # end check sanity

        return config_tree

    ## -- End Utilities -- @}


    @with_rw_directory
    @with_application(from_file=__file__)
    def test_project_setup(self, rw_dir):
        # prepare the mock db - reuse the tank implementation as it's already what tank needs
        project = {      'type': 'Project',
                         'id': 1,
                         'tank_name': None,
                         'name': 'project_name' }

        self._sg_mock_db[('Project', 1)] = project
        self._sg_mock_db[('LocalStorage', 1)] = {'code' : constants.PRIMARY_STORAGE_NAME,
                                                 'mac_path' : rw_dir,
                                                 'linux_path' : rw_dir, 
                                                 'windows_path' : rw_dir}

        sg = self.sg_mock
        sg.server_info = Mock()
        sg.server_info.__getitem__ = Mock(side_effect=[(4, 3, 9)])
        sg.schema_read = Mock(side_effect=[('PublishedFile','PublishedFileType', 'PublishedFileDependency')])

        assert sg.find_one('Project', [['id', 'is', 1]])

        spc = SetupTankProject()
        self.failUnlessRaises(ValueError, spc.handle_project_setup, sg, log, project['id'])

        # provide the required information
        app = bapp.main()
        def required_info(schema, settings):
            # let's just put the bootstrapper to a known location, temporarily
            settings.studio_bootstrapper_path = self._setup_bootstrapper_at(rw_dir, 'btank')[0]
            settings.studio_configuration_uri = self._default_configuration_tree()
        # end

        ApplyChangeContext('project-setup-settings').setup(     app.context(), 
                                                                required_info,
                                                                spc.settings_schema())

        tk = spc.handle_project_setup(sg, log, project['id'])
        assert tk, "expected a valid tank instance as return value"

        
# end class BasicTests
