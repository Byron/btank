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
__all__ = ['SetupProjectPatcher']

import os
import logging

from mock import (Mock,
                  patch)

from .base import (TankTestCase,
                   with_tank_sandbox)
import bapp
from bapp.tests import with_application
from bkvstore import KeyValueStoreProvider
from butility.tests import with_rw_directory
from butility import (DictObject,
                      Path,
                      DEFAULT_ENCODING)

from tank.deploy.tank_commands import setup_project
import tank.platform.constants as constants
import tank

log = logging.getLogger('btank.tests.test_base')


# from * import
from btank.commands import *
from btank.utility import link_bootstrapper
from btank.schema import setup_project_schema

# This is that ugly because plugins are never supposed to be imported directly, but always 
# through the plugin system. For tests cases, however, we need to work aroud that.
# NOTE: might be worth making their names more pythonic ... 
modname = 'btank-plugins.shotgun-events'
sgevents = __import__(modname, locals(), globals(), [modname])


# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class SetupProjectPatcher(object):
    """Assure that setup project doesn't get out"""
    def __init__(self):
        self.patch = patch('tank.deploy.tank_commands.setup_project._install_environment')
        self.patch.start()

    def __del__(self):
        self.patch.stop()

# end class SetupProjectPatcher

## -- End Utilities -- @}



class CommandTests(TankTestCase):

    # -------------------------
    ## @name Command Implementation
    # @{

    def _project_storage_names(self, *args):
        return ['primary']

    ## -- End Command Implementation -- @}

    # -------------------------
    ## @name Utilities
    # @{

    def _setup_bootstrapper_at(self, tree, name):
        """Setup wrapper files for all platforms in the given directory
        @param tree an existing directory to write to
        @param name of the wrapper executable (like 'btank')
        @return (posix_wrapper, windows_wrapper)"""
        import bprocess.bootstrap
        bootrapper_path = Path(bprocess.bootstrap.__file__).splitext()[0] + '.py'
        # no need for relocatability here ... also good to test that branch, if it was one
        return (link_bootstrapper(bootrapper_path, tree / name, posix=True, relocatable=False), 
                link_bootstrapper(bootrapper_path, tree / (name + '.py'), posix=False, relocatable=False))

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


    @with_application(from_file=__file__)
    @with_rw_directory
    @with_tank_sandbox
    def test_project_setup(self, rw_dir, sg):
        # prepare the mock db - reuse the tank implementation as it's already what tank needs
        project = {      'type': 'Project',
                         'id': 1,
                         'sg_project_folder' : 'project_folder',
                         'sg_project_short_name' : 'testy',
                         'tank_name': None,
                         'name': 'project_name' }

        local_storage = {'code' : constants.PRIMARY_STORAGE_NAME,
                         'mac_path' : str(rw_dir),
                         'linux_path' : str(rw_dir), 
                         'windows_path' : str(rw_dir),
                         'id' : 1,
                         'type' : 'LocalStorage'}
        sg.set_entities([project, local_storage])
        sg.set_server_info(version_tuple=(4, 3, 9))

        for dummy in ('PublishedFile','PublishedFileType', 'PublishedFileDependency'):
            sg.set_entity_schema(dummy, dict())
        # end for each dummmy
        sg.set_entity_schema('Project', dict((k, None) for k in project.keys()))


        stp = SetupTankProject()

        pb, wb = self._setup_bootstrapper_at(rw_dir, 'btank')
        config_uri = self._default_configuration_tree()
        patch_installer = SetupProjectPatcher()
        settings = DictObject({'bootstrapper' : {'posix_path' : pb, 'windows_path' : wb},
                               'configuration_uri': config_uri,
                               'python2' : {'windows_interpreter_path' : 'c:\\foo'}})
        location = stp.handle_project_setup(sg, log, DictObject(project), settings)
        assert location.isdir(), "expected a valid tank instance as return value"


        # If it's correct, folder structure should be doable.
        tk = tank.tank_from_path(location)
        tk.create_filesystem_structure(project['type'], project['id'])


        ##############################
        # Test Event Engine Plugin ##
        ############################
        plugin = sgevents.TankProjectEventEnginePlugin(sg, log)

        ctx = bapp.main().context().push('project-setup-settings')
        ctx.settings().set_value_by_schema(setup_project_schema, settings)

        event = {'entity' : {'type' : 'Project', 'id' : project['id']}}
        event = DictObject(event)

        try:
            plugin.handle_event(sg, log, event)
        except OSError as err:
            assert err.errno == 17, "project directory can't be created as it exists"
        # end

        
# end class BasicTests
