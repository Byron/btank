#-*-coding:utf-8-*-
"""
@package btank-plugins.shotgun-events
@brief Plugins for using the shotgun event engine

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str
__all__ = ['TankProjectEventEnginePlugin']


import bapp
from sgevents import (EventEnginePlugin,
                      with_event_application)

from butility import DictObject
from btank.schema import setup_project_schema
from btank.commands import SetupTankProject


class TankProjectEventEnginePlugin(EventEnginePlugin, bapp.plugin_type()):
    """Create a new tank project whenever a shotgun project is created.

    We are using the KVStore for configuration of required values.
    """
    __slots__ = ()

    # -------------------------
    ## @name Configuration
    # @{
    
    ## The events we want to register to
    # dict('APPLICATION_ENTITYTYPE_ACTION', [attribute, ...]|None,)
    # see https://github.com/shotgunsoftware/python-api/wiki/Event-Types for more information
    # This one get's all events
    event_filters = {'Shotgun_Project_New' : list()}

    ## additional configuration we retrieve
    setup_project_schema = setup_project_schema

    ## The delegate to actually create a new project
    SetupTankProjectType = SetupTankProject

    ## -- End Configuration -- @}


    # -------------------------
    ## @name Utilities
    # @{

    def _sanitize_settings(self, settings):
        """Assure we have all required values actually set, and return possibly sanitized values"""
        missing = list()
        for required_setting in ('configuration_uri', 'bootstrapper'):
            if not settings[required_setting]:
                missing.append(required_setting)
            # end
        # end for each required setting

        if missing:
            raise ValueError("Need value for settings at %s" % ','.join(('%s.%s' % (setup_project_schema.key(), m))
                                                                                    for m in missing))
        # end

        if any(map(lambda p: not p.isfile(), settings.bootstrapper.values())):
            raise ValueError("Bootstrapper at any of '%s' was not accessible - it must be visible"
                             " to the machine setting up tank" % (', '.join(settings.bootstrapper.values())))
        # end assert it exists

        return settings
    
    ## -- End Utilities -- @}


    # -------------------------
    ## @name Subclass Interface
    # @{

    def _project_config_uri(self, sg, log, settings, project):
        """@return a tank-project-setup digestable URI to the configuration it should use."""
        return settings.configuration_uri

    def _bootstrapper_paths(self, sg, log, settings, project):
        """@return [posix_path, windows_path] of Paths to bootstrappers to use when creating the given project.
        They must be returned in that order, and either of them may be None to drop support for that platform"""
        bs = settings.bootstrapper
        return bs.posix_path, bs.windows_path

    ## -- End Subclass Interface -- @}

    # -------------------------
    ## @name Interface
    # @{
    
    @with_event_application
    def handle_event(self, app, shotgun, log, event):
        settings = self._sanitize_settings(app.context().settings().value_by_schema(self.setup_project_schema))
        project = DictObject(shotgun.find_one( event.entity.type,
                                          [['id', 'is', event.entity.id]],
                                          shotgun.schema_field_read(event.entity.type, None).keys()))

        config_uri = self._project_config_uri(shotgun, log, settings, project)
        pp, wp = self._bootstrapper_paths(shotgun, log, settings, project)

        self.SetupTankProjectType().handle_project_setup(shotgun, log, project, config_uri, pp, wp)

    ## -- End Interface -- @}

# end class TankProjectEventEnginePlugin
