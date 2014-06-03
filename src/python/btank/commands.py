#-*-coding:utf-8-*-
"""
@package btank.commands
@brief Contains various utilities to interact with tank

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
# from __future__ import unicode_literals
# NO: tank needs strings for the most part, and we convert explicitly
# from butility.future import str

__all__ = ['SetupTankProject']

import sys
from contextlib import contextmanager

from butility import (DictObject,
                      Path)

from bapp import ApplicationSettingsMixin
from bkvstore import YAMLStreamSerializer
import tank
from tank.deploy.tank_commands import setup_project
import tank.platform.constants as constants

from .schema import setup_project_schema
from .utility import platform_tank_map



class SetupTankProject(ApplicationSettingsMixin):
    """Should run a reaction to a newly created Shotgun project and sets it up to work with btank.
    As opposed to the default implementation, we will make it use our own, pre-existing shotgun connection,
    and use kvstore and environmental information.

    This implementation is not complete as it needs to learn about project locations, which are non-standard
    right in shotgun so wa can't know about it. See subclass interface for requirements.
    """
    __slots__ = ()

    _schema = setup_project_schema


    # -------------------------
    ## @name Configuration
    # @{

    ## The subdirectory relative to the project root at which tank should be located at
    ## it will be a 'shallow' copy, using the studio installation
    tank_subtree = 'tank'

    ## -- End Configuration -- @}


    # -------------------------
    ## @name Subclass Interface
    # @{

    def _project_storage_names(self, sg, log, project):
        """@return [local_storage_name, ...]
        A list of local-storage names associated with the project. 
        Those are conigured in 'Site Preferences -> File Management'
        The first one, usually called 'primary', is used to store all tank configuration subsequently created.
        The will be used to to fill in information about your project roots
        @param project a DictObject of all available project information, as returned from shotgun"""
        return [constants.PRIMARY_STORAGE_NAME]

    def _project_folder_name(self, sg, log, project):
        """The name of the directory matching the project.
        @param project a DictObject of all available project information, as returned from shotgun"""
        return project.name

    def _project_config_uri(self, sg, log, settings, project):
        """@return a tank-project-setup digestable URI to the configuration it should use."""
        return settings.studio_configuration_uri


    ## -- End Subclass Interface -- @}


    # -------------------------
    ## @name Utilities
    # @{

    @contextmanager
    def _tank_monkey_patch(self):
        """Make sure tank doens't get into our way.
        As the tank executable is intercepted, and actually calling a wrapped and preconfigured executable,
        the special way of tank handling its bootstrapping is not required.
        So lets shut it off
        """
        fun_name = '_get_current_core_file_location'
        prev_fun = getattr(setup_project, fun_name, None)
        assert prev_fun, "tank code base changed - monkey patcher needs a review !"

        def return_locations():
            # well, maybe not in order get the auto-installation going. No problem putting it back in though ... 
            msg = 'btank makes this obsolete'
            return dict((p, msg) for p in ('Windows', 'Darwin', 'Linux'))
        # end
            
        setattr(setup_project, fun_name, return_locations)
        yield
        setattr(setup_project, fun_name, prev_fun)
        # end do or undo

    def _sanitize_settings(self, settings):
        """Assure we have all required values actually set, and return possibly sanitized values"""
        missing = list()
        for required_setting in ('studio_configuration_uri', 'studio_bootstrapper_path'):
            if not settings[required_setting]:
                missing.append(required_setting)
            # end
        # end for each required setting

        if missing:
            raise ValueError("Need value for settings at %s" % ','.join(('%s.%s' % (setup_project_schema.key(), m))
                                                                                    for m in missing))
        # end

        if not settings.studio_bootstrapper_path.isfile():
            raise ValueError("Bootstrapper at '%s' was not accessible - it must be visible"
                             " to the machine setting up tank" % settings.studio_bootstrapper_path)
        # end assert it exists

        return settings

    def _resolve_local_storage_names(self, sg, log, names):
        """@return a dict('name' : {'linux_path' : str', 'mac_path' : str, 'windows_path' : str}) 
        with all the given LocalStorage names"""
        storages = sg.find('LocalStorage', list(), ['code', 'linux_path', 'mac_path', 'windows_path'])
        res = dict((s.pop('code'), s) for s in storages)
        return res

    def _multi_platform_project_tree(self, storage_names, storage_dict, project_folder_name):
        """@return a dict('linux_path' : Path, 'mac_path' : Path,'windows_path' : Path) to directories on disk which 
        should contain the given project, based on the information in the storage_dict.
        Usually, you pick a storage name, and return the information in the storage dict"""
        name = storage_names[0]
        try:
            s = storage_dict[name]
        except KeyError:
            raise AssertionError("local storage named '%s' didn't exist - create it in shotgun and retry" % name)
        # end catch possible user errors

        for platform, path in s.items():
            s[platform] = Path(path) / project_folder_name
        # end convert to path 
        return s

    ## -- End Utilities -- @}


    # -------------------------
    ## @name Interface
    # @{

    def handle_project_setup(self, sg, log, project_id):
        """Deal with tank in order to get a new project setup accordingly.
        @param sg a shotgun connection
        @param log a logger
        @param project_id integer ID of the project to create
        @return a tank instance, ready for use (useful for creating directories for instance)
        """
        settings = self._sanitize_settings(self.settings_value())
        project = DictObject(sg.find_one( 'Project',
                                          [['id', 'is', project_id]],
                                          sg.schema_field_read('Project', None).keys()))

        # Resolve all roots
        project_folder_name = self._project_folder_name(sg, log, project)
        assert project_folder_name, "Need a project folder"
        storage_names = self._project_storage_names(sg, log, project)
        assert storage_names, "Didn't find any storage"
        storage_roots = self._resolve_local_storage_names(sg, log, storage_names)
        assert storage_roots, "Would have expected at least one storage root"

        # we simply use the first storage as the one keeping the project
        project_roots = self._multi_platform_project_tree(storage_names, storage_roots, project_folder_name)
        tank_conftree = lambda p: project_roots[p] / self.tank_subtree

        # setup parameters
        # Note that the storage roots will just remain unchanged until everything was created
        # We will post-process the roots.yml to match what's configured for the project
        params = dict(project_id          = project_id,
                      project_folder_name = str(project_folder_name),
                      config_uri          = str(self._project_config_uri(sg, log, settings, project)),
                      config_path_mac     = str(tank_conftree('mac_path')),
                      config_path_linux   = str(tank_conftree('linux_path')),
                      config_path_win     = str(tank_conftree('windows_path')))

        # For the next step to work, tank really wants the project directory to exist. Fair enough
        tank_os_name = platform_tank_map[sys.platform]
        project_os_root = project_roots['%s_path' % tank_os_name]
        try:
            project_os_root.mkdir()
        except OSError as err:
            raise OSError("Require write permissions on '%s'" % project_os_root.dirname())
        # end

        # nothing useful in return
        cmd = tank.get_command('setup_project')
        cmd.set_logger(log)
        with self._tank_monkey_patch():
            cmd.execute(params)
        # end assure monkey-patch gets undone


        # Interestingly, and good for us, these default file paths that it expects are hard-coded in many places
        # This kind of forces it to be stable. This would feel better to have an official function to do it ... .
        tank_os_root = Path(params['config_path_%s' % tank_os_name])

        roots_file = tank_os_root / 'config' / 'core' / 'roots.yml'
        assert roots_file.isfile(), "Didn't find roots file at '%s'" % roots_file

        try:
            YAMLStreamSerializer().serialize(storage_roots, open(roots_file, 'w'))
        except Exception as err:
            raise AssertionError("Failed to re-write roots file at '%s' with error: %s" % (roots_file, err))
        # end handle exceptions

        # Finally, setup the tank configuration to use the bwrapper
        raise NotImplementedError("todo")

    ## -- End Interface -- @}

    

# end class SetupTankProject
