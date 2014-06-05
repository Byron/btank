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
from copy import deepcopy
from contextlib import contextmanager

from butility import (DictObject,
                      Path)

from bkvstore import YAMLStreamSerializer
import tank
from tank.deploy.tank_commands import setup_project
import tank.platform.constants as constants

from .utility import (platform_tank_map,
                      link_bootstrapper)
from .utility.patch import PatchSet
from butility.compat import StringIO


class SetupTankProject(object):
    """Should run a reaction to a newly created Shotgun project and sets it up to work with btank.
    As opposed to the default implementation, we will make it use our own, pre-existing shotgun connection,
    and use kvstore and environmental information.

    This implementation is not complete as it needs to learn about project locations, which are non-standard
    right in shotgun so wa can't know about it. See subclass interface for requirements.
    """
    __slots__ = ()


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

        s = deepcopy(s)
        for platform, path in s.items():
            s[platform] = Path(path) / project_folder_name
        # end convert to path 
        return s

    ## -- End Utilities -- @}


    # -------------------------
    ## @name Interface
    # @{

    def handle_project_setup(self, sg, log, project, tank_config_uri, posix_bootstrapper=None, 
                                                                         windows_bootstrapper=None):
        """Deal with tank in order to get a new project setup accordingly.
        @param sg a shotgun connection
        @param log a logger
        @param project a DictObject with all available project information as retrieved from shotgun
        @param tank_config_uri a tank-compatible URI to the configuration it should obtain
        @param posix_bootstrapper if not None, an accessible location to the bootstrapper, which knows 
        the 'tank' package
        @param windows_bootstrapper see posix_bootstrapper. One of the two must exist
        @return the location at which tank was installed, it is the pipeline configuration root, and contains the tank 
        executable
        """
        assert posix_bootstrapper or windows_bootstrapper, "One bootstrapper path must be set at least"

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
        params = dict(project_id          = project.id,
                      project_folder_name = str(project_folder_name),
                      config_uri          = str(tank_config_uri),
                      config_path_mac     = str(tank_conftree('mac_path')),
                      config_path_linux   = str(tank_conftree('linux_path')),
                      config_path_win     = str(tank_conftree('windows_path')))

        # For the next step to work, tank really wants the project directory to exist. Fair enough
        tank_os_name = platform_tank_map[sys.platform]
        project_os_root = project_roots['%s_path' % tank_os_name]
        project_os_root.mkdir()

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

        # Setup bootstrappers for posix and the rest
        for posix, (path, ext) in enumerate(((windows_bootstrapper, '.py'), (posix_bootstrapper, ''))):
            if not path:
                continue
            link_bootstrapper(path, tank_os_root / ('btank'+ext), posix=posix)
        # end for each os name

        # Finally, setup the tank configuration to use our bootstrapper
        if not PatchSet(stream=StringIO(self.root_programs_patch)).apply(root=tank_os_root):
            raise AssertionError("Couldn't apply patch to root programs - they must have changed too much")
        # end handle patch

        return tank_os_root

    ## -- End Interface -- @}

    # -------------------------
    ## @name Resources
    # @{

    ## See original patch source file at etc/patches/btank-interception.patch
    root_programs_patch = \
r"""--- tank	2014-06-01 16:35:00.000000000 +0200
+++ tank	2014-05-27 14:46:24.000000000 +0200
@@ -1,4 +1,4 @@
-#!/usr/bin/env bash
+#!/bin/bash --login
 # Copyright (c) 2013 Shotgun Software Inc.
 # 
 # CONFIDENTIAL AND PROPRIETARY
@@ -54,7 +54,9 @@
 
 
 # if we have a local install of the core, this is the script to dispatch to
-LOCAL_SCRIPT="$SELF_PATH/install/core/scripts/tank_cmd.sh"
+# BTANK: go straight for the wrapper, it is relocatable and handles all the cases
+LOCAL_SCRIPT="$SELF_PATH/btank"
+exec $LOCAL_SCRIPT $@
 
 # when called from shotgun, we reroute to a special script which uses a login shell shebang.
 if [ -n "$1" ] && ( [ "$1" = "shotgun_run_action" ] || [ "$1" = "shotgun_cache_actions" ] ); then
--- tank.bat	2014-06-01 16:35:00.000000000 +0200
+++ tank.bat	2014-06-03 11:22:09.000000000 +0200
@@ -53,6 +53,17 @@
 for /f %%G in (%PARENT_CONFIG_FILE%) do (SET PARENT_LOCATION=%%G)
 IF NOT EXIST "%PARENT_LOCATION%" GOTO NO_PARENT_LOCATION
 
+rem -- BTANK: go straight for the wrapper, it is relocatable and handles all the cases
+rem -- yes, I brutally copy-paste code from tank_cmd.bat to not have to deal with .bat any more than needed
+rem -- ARGH: how many lines of code just to do the equivalent of a one-liner in bash ? Please, die out, Windows, don't fight it
+set INTERPRETER_CONFIG_FILE=%PARENT_LOCATION%\config\core\interpreter_Windows.cfg
+IF NOT EXIST "%INTERPRETER_CONFIG_FILE%" GOTO NO_INTERPRETER_CONFIG
+for /f "tokens=*" %%G in (%INTERPRETER_CONFIG_FILE%) do (SET PYTHON_INTERPRETER=%%G)
+IF NOT EXIST %PYTHON_INTERPRETER% GOTO NO_INTERPRETER
+%PYTHON_INTERPRETER% "%SELF_PATH%\btank.py" %*
+exit /b %ERRORLEVEL%
+rem -- ----SHOULD NEVER REACH THIS POINT------------------------------------------------
+
 rem -- all good, execute tank script in parent location
 call %PARENT_LOCATION%\tank.bat %* --pc=%SELF_PATH%
 
@@ -99,5 +110,10 @@
 echo Cannot find parent location defined in file %PARENT_CONFIG_FILE%!
 exit /b 1
 
+:NO_INTERPRETER_CONFIG
+echo "Cannot find interpreter configuration file %INTERPRETER_CONFIG_FILE%!"
+exit /b 1
 
-
+:NO_INTERPRETER
+echo "Could not find interpreter %PYTHON_INTERPRETER% specified in configuration file!"
+exit /b 1
\ No newline at end of file
"""

    ## -- End Resources -- @}

# end class SetupTankProject
