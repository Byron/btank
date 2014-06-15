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

    def _sanitize_settings(self, settings, log):
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
            log.warn("One of the bootstrappers at '%s' was not accessible - it should be visible"
                     " to the machine setting up tank", ', '.join(settings.bootstrapper.values()))
        # end assert it exists

        if settings.bootstrapper.windows_path and not settings.tank.windows_core_path:
            raise ValueError('tank.windows_core_path needs to be set if the bootstrapper.windows_path is used')
        # end

        return settings
    
    ## -- End Utilities -- @}


    # -------------------------
    ## @name Subclass Interface
    # @{

    def _adjusted_settings(self, sg, log, settings, project):
        """@return a DictObject similar (or the same as) settings, with possibly adjusted values. This is your 
        official call to make changes before the settings are used"""
        return settings

    ## -- End Subclass Interface -- @}

    # -------------------------
    ## @name Interface
    # @{
    
    @with_event_application
    def handle_event(self, app, shotgun, log, event):
        settings = self._sanitize_settings(app.context().settings().value_by_schema(self.setup_project_schema), log)
        project = DictObject(shotgun.find_one( event.entity.type,
                                          [['id', 'is', event.entity.id]],
                                          shotgun.schema_field_read(event.entity.type, None).keys()))

        settings = self._adjusted_settings(shotgun, log, settings, project)
        self.SetupTankProjectType().handle_project_setup(shotgun, log, project, settings)

    ## -- End Interface -- @}

# end class TankProjectEventEnginePlugin
