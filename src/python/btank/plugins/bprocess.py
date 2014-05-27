#-*-coding:utf-8-*-
"""
@package btank.plugins.bprocess
@brief contains a delegate to deal with tank commandline startup

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['TankCommandDelegate', 'TankEngineDelegate', 'HieroTankEngineDelegate', 'NukeTankEngineDelegate', 
           'MayaTankEngineDelegate']

import os
import sys

import bapp
from butility import (Path,
                      abstractmethod,
                      update_env_path)
from bprocess import process_schema
from bkvstore import KeyValueStoreSchema
from bapp import ApplicationSettingsMixin

import logging
log = logging.getLogger('btank.plugins.bprocess')


# ==============================================================================
## @name Utility Types
# ------------------------------------------------------------------------------
## @{


root_key = 'tank'
tank_engine_schema = KeyValueStoreSchema('%s.engine-delegate' % root_key, 
                                                                {'multi-launchapp-location' : 
                                                                    dict(name = 'tk-multi-launchapp',
                                                                         version = 'v0.2.19',
                                                                         type = 'app_store'),
                                                                  'host_app_name' : str,
                                                                  'entity_type' : str,
                                                                  'entity_id' : int})

tank_command_schema = KeyValueStoreSchema('%s.command-delegate' % root_key, {'app_name' : 
                                                                                dict(prefix = str,
                                                                                     suffix = str)})


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


    @classmethod
    def _sgtk_module(cls, env):
        """@return the sgtk package, as demoninated in the environment
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
        return sgtk
    
    ## -- End Interface -- @}

# end class TankDelegateCommonMixin


## -- End Utility Types -- @}



class TankCommandDelegate(TankDelegateCommonMixin, ProcessControllerDelegate, bapp.plugin_type()):
    """process arguments to be suitable for tank.
    Additinoally we can intercept launch commands and execute them ourselves.
    """

    tank_pc_arg='--pc='
    launch_prefix = 'launch_'

    def _extract_path(self, arg):
        """Handle --pc= arg explicitly, in order to be sure to pick up project configuration at least"""
        if arg.startswith(self.tank_pc_arg):
            arg = arg[len(self.tank_pc_arg):]
        return super(TankCommandDelegate, self)._extract_path(arg)

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
            new_args.append(str(self.tank_pc_arg + base))
        # end setup context

        #######################
        # Process Arguments ##
        #####################
        if len(new_args) > 6 and new_args[3].startswith(self.launch_prefix):
            # now we could go crazy and try to find asset paths in order to provide context to bprocess
            # We could also use the shotgun context in some way, to feed data to our own asset management
            # However, for now using the project itself should just be fine, but this is certainly 
            # to be improved

            # Additinally, what we really want is to start any supported program, and enforce tank support by
            # fixing up delegates. For that, we will create a new process controller, which uses our Application 
            # instance, and the delegate that it defined so far.
            # However, we are currently unable to truly provide the information we have to a new process controller, 
            # unless it's communicated via the context.

            # It should be one of ours (e.g. TankEngineDelegate derivative) if there is tank support, which 
            # requires proper configuration.
            
            # For that to work, we will override the entire start procedure, as in pre-start we can't and should not
            # swap in the entire delegate
            def set_overrides(schema, value):
                value.host_app_name = new_args[3][len(self.launch_prefix):]
                value.entity_type = new_args[4]
                value.entity_id = int(new_args[5])
            # end overrides setter

            # usually, this is done during prepare_context(), but we don't need the controller to react to 
            # context changes and do plenty of extra work
            ctx = self.DelegateContextOverrideType('tank-engine-information').setup(
                                                                                self._app.context().settings(),
                                                                                set_overrides, 
                                                                                tank_engine_schema)
            self._app.context().push(ctx)
            
            # tk = self._sgtk_module(env).tank_from_entity(entity_type, entity_id)
            # ctx = tk.context_from_entity(entity_type, entity_id)
        #end handle particular command mode

        return (executable, env, new_args, cwd)

    def start(self, args, cwd, env, spawn):
        """Check if there is an override for the engine, and launch up a new process controller with our application.
        That way, the originally configured delegate can handle the matter accordinlgy"""
        val = self._app.context().settings().value_by_schema(tank_engine_schema)
        if not val.host_app_name:
            return super(TankCommandDelegate, self).start(args, cwd, env, spawn)
        # end ignore if there is no override

        settings = self._app.context().settings().value_by_schema(tank_command_schema)
        # create a fake executable, which is in the correct project already
        executable = Path(args[0]).dirname() / (settings.app_name.prefix + val.host_app_name + settings.app_name.suffix)
        # We drop args here, as we just assume to have handled them all
        # Let's give it all the args which are obviously ours
        args = [a for a in args if a.startswith(ProcessController.wrapper_arg_prefix)]
        return ProcessController(executable, args=args, cwd = cwd, application = self._app).execute()

    ## -- End Interface Overrides -- @}

# end class TankCommandDelegate


class TankEngineDelegate(TankDelegateCommonMixin, ProcessControllerDelegate, ApplicationSettingsMixin):
    """A delegate to startup any tank engine, using the bootstrapper provided by the multi-launch app.
    The context will be created using tank's own mechanisms.
    """
    __slots__ = '_context_paths'    # paths we have encountered on the commandline, including the actual executable

    _schema = tank_engine_schema

    # -------------------------
    ## @name Subclass Configuration
    # @{

    ## Name of the application, for which to create an engine, like 'maya', or 'photoshop' 
    host_app_name = None

    ## An environment variable which is supposed to be set with the app specific startup directory
    host_app_evar = None
    
    ## -- End Subclass Configuration -- @}

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
        sgtk = cls._sgtk_module(env)

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

        actual_executable = self._actual_executable()
        self._context_paths.append(actual_executable)
        self._context_paths.append(cwd)

        try:
            tk, context_path = self._tank_instance(env, sorted(self._context_paths, reverse=True))
        except Exception as err:
            log.error("Failed to instantiate tank - application will come up without it ! Error was: %s", err)
            return rval
        # end ignore exceptions

        # This is dangerous, as we are depending on magic values here
        settings = self.settings_value()

        # Get the most specific context, and feed it to the engine via env vars
        # We could have entity information from a 'btank' invocation done previously, so try to use that instead
        if settings.entity_type:
            ctx = tk.context_from_entity(settings.entity_type, settings.entity_id)
        else:
            ctx = tk.context_from_path(context_path)
        # end init context

        location_dict = settings['multi-launchapp-location']
        import tank.deploy.descriptor
        try:
            dsc = tank.deploy.descriptor.get_from_location(tank.deploy.descriptor.AppDescriptor.APP, 
                                                           tk.pipeline_configuration,
                                                           location_dict)
        except Exception as err:
            log.error("Couldn't find location of multi-launchapp with error: %s", err)
            return rval
        # end couldn't find multi-launch app

        if ctx.project is None:
            log.error("Couldn't obtain a valid tank context from path '%s' - tank is disabled", context_path)
            return rval
        # end verify context isn't empty

        # prepare the tank environment
        import tank.context
        env['TANK_CONTEXT'] = tank.context.serialize(ctx)

        host_app_name = self._host_app_name(actual_executable)
        if settings.host_app_name and settings.host_app_name != host_app_name:
            log.error("host application name passed by 'tank' commandline '%s' didn't match host application "
                      "reported by delegate '%s' - tank disabled - please check your configuration", 
                      settings.host_app_name, host_app_name)
            return rval
        # end verify application name
        env['TANK_ENGINE'] = 'tk-' + host_app_name

        startup_path = Path(dsc.get_path()) / 'app_specific' / host_app_name / 'startup'
        if not startup_path.isdir():
            log.error("No engine startup configuration found at '%s' - tank will be disabled", startup_path)
            return rval
        # end handle startup dir

        try:
            self.prepare_tank_engine_environment(startup_path, new_args, env)
        except Exception as err:
            # just log the exception
            log.error("Failed to configure '%s' tank engine with error: %s - tank is disabled", 
                        host_app_name, err)
        # end ignore exception
        
        return rval

    # -------------------------
    ## @name Subclass Interface
    # @{

    def _host_app_name(self, executable):
        """@return the name of the host application the engine we configure is for
        @param executable the name of the executable originally launched
        @note subtypes should implement the host_app_name class member variable"""
        if self.host_app_name is not None:
            return self.host_app_name

        # guess it - this would work fine in many cases, but shouldn't be the default
        log.debug("Guessing tank engine from application name '%s' - if it doesn't work, set a tank delegate", executable)
        return executable.namebase()

    def prepare_tank_engine_environment(self, startup_tree, args, env):
        """Alter given args or env in place in order to make the launched application.
        @param startup_tree Path to the root of the host application specific startup directory in the
        tk-multi-launchapp. It is already verified to exist
        @param args list of program arguments
        @param env dict with environment variables - already containing the tank engine specific ones
        @throws any exception to disable tank
        @default implementation will just prepend the startup directory to the configured host_app_evar variable"""
        if self.host_app_evar is not None:
            update_env_path(self.host_app_evar, startup_tree, append = False, environment = env)
        else:
            raise NotImplementedError("Either set the 'host_app_evar' class member, or implement this method")
        # end handle evar

    ## -- End Subclass Interface -- @}

# end class TankEngineDelegate



# ==============================================================================
## @name Application Specific Tank Delegates
# ------------------------------------------------------------------------------
## @{

class HieroTankEngineDelegate(TankEngineDelegate, bapp.plugin_type()):
    __slots__ = ()

    host_app_name = 'hiero'
    host_app_evar = 'HIERO_PLUGIN_PATH'

# end class HieroTankEngineDelegate


class NukeTankEngineDelegate(TankEngineDelegate, bapp.plugin_type()):
    __slots__ = ()

    host_app_name = 'nuke'
    host_app_evar = 'NUKE_PATH'
        
# end class NukeTankEngineDelegate


class MayaTankEngineDelegate(TankEngineDelegate, bapp.plugin_type()):
    __slots__ = ()

    host_app_name = 'maya'
    host_app_evar = 'PYTHONPATH'

# end class NukeTankEngineDelegate


## -- End Application Specific Tank Delegates -- @}

