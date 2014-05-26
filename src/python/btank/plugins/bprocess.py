#-*-coding:utf-8-*-
"""
@package btank.plugins.bprocess
@brief contains a delegate to deal with tank commandline startup

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['TankCommandDelegate', 'TankEngineDelegate']

import os
import sys

import bapp
from butility import Path
from bprocess import process_schema

import logging
log = logging.getLogger('btank.plugins.bprocess')



class TankDelegateCommonMixin(object):
    """Some methods suitable for all delegates implemented here"""
    __slots__ = ()

    # We actually always want this to be enabled
    context_from_path_arguments = True

    # -------------------------
    ## @name Interface
    # @{

    def _actual_executable(self):
        """@return path to the executable originally invoked invoked"""
        return self._app.context().settings().value_by_schema(process_schema).executable
    
    ## -- End Interface -- @}

# end class TankDelegateCommonMixin


class TankCommandDelegate(ProcessControllerDelegate, TankDelegateCommonMixin, bapp.plugin_type()):
    """process arguments to be suitable for tank.
    Additinoally we can intercept launch commands and execute them ourselves.
    """

    tank_pc_arg='--pc='

    # -------------------------
    ## @name Interface Overrides
    # @{
    
    def pre_start(self, executable, env, args, cwd, resolve):
        executable, env, new_args, cwd = super(TankCommandDelegate, self).pre_start(executable, env, args, cwd, resolve)

        # and the second argument must be the tank install root ... lets make it happy
        if len(new_args) > 2 and not os.path.isabs(new_args[1]):
            install_root = Path(new_args[0]).dirname().dirname().dirname()
            assert install_root.basename() == 'install', "Expected first argument '%s' to be tank_cmd.py right in the install root" % new_args[0]
            new_args.insert(1, install_root.dirname())
        # end handle install root

        last_arg = new_args[-1]
        if not last_arg.startswith(self.tank_pc_arg):
            # we assume to be in the right spot, but a check can't hurt until
            # we are able to do more ourselves
            actual_executable = self._actual_executable()
            base = actual_executable.dirname()
            assert (base / 'tank').exists(), "Currently '%s' must be right next to the 'tank' executable" % executable
            new_args.append(self.tank_pc_arg + base)
        # end setup context

        return (executable, env, new_args, cwd)

    ## -- End Interface Overrides -- @}

# end class TankCommandDelegate


class TankEngineDelegate(ProcessControllerDelegate, TankDelegateCommonMixin, bapp.plugin_type()):
    """A delegate to startup any tank engine, using the bootstrapper provided by the multi-launch app.
    The context will be created using tank's own mechanisms.
    """

    __slots__ = '_context_paths'    # paths we have encountered on the commandline, including the actual executable

    def __init__(self, *args, **kwargs):
        """Intiailize our member variables"""
        super(TankEngineDelegate, self).__init__(*args, **kwargs)
        self._context_paths = list()

    def _extract_path(self, arg):
        """intercept paths given on the commandline"""
        path = super(TankEngineDelegate, self)._extract_path(arg)
        if path is not None:
            self._context_paths.append(path)
        # end keep path for later
        return path

    @classmethod
    def _tank_instance(cls, env, paths):
        """@return the initialized tank package that exists at TANK_TREE, and the context path which created
        the instance
        @param env enviornment of the to-be-started process
        @param paths from which to pull the context. They should be sorted from most specialized to to least 
        specialized
        @throws EnvironmentError if we couldn't find it"""
        root = env.get('TANK_TREE')
        if not root:
            raise EnvironmentError("Expected TANK_TREE environment variable to be set")
        root = Path(root) / 'core' / 'python'
        sys.path.append(str(root))
        try:
            import sgtk
        except ImportError as err:
            raise EnvironmentError("Failed to import tank from '%s' with error: %s", root, str(err))
        # end

        for path in paths:
            try:
                return sgtk.tank_from_path(path), path
            except Exception:
                pass
        # end for each path to try

        raise EnvironmentError("Failed to initialize tank from any of the given context paths: %s" % ', '.join(paths))

    def pre_start(self, executable, env, args, cwd, resolve):
        """Place boot-stap environment variables, based on information received from the tank studio installation"""
        executable, env, new_args, cwd = super(TankEngineDelegate, self).pre_start(executable, env, args, cwd, resolve)
        rval = (executable, env, new_args, cwd)

        self._context_paths.append(self._actual_executable())
        self._context_paths.append(cwd)

        try:
            tk, context_path = self._tank_instance(env, sorted(self._context_paths, reverse=True))
        except Exception as err:
            log.error("Failed to instantiate tank - application will come up without it ! Error was: %s", err)
            return rval
        # end ignore exceptions

        # Get the most specific context, initialize an engine with it.
        ctx = tk.context_from_path(context_path)

        # This is dangerous, as we are depending on magic values here
        # TODO: PUT INTO CONFIGURATION !
        try:
            env = tk.pipeline_configuration.get_environment('shotgun_project', ctx)
            dsc = env.get_app_descriptor('tk-shotgun', 'tk-shotgun-launchmaya')
        except Exception as err:
            log.error("Couldn't find location of multi-launchapp with error: %s", err)
            return rval
        # end couldn't find multi-launch app

        return rval

# end class TankEngineDelegate
