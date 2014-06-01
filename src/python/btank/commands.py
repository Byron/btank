#-*-coding:utf-8-*-
"""
@package btank.commands
@brief Contains various utilities to interact with tank

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from butility.future import str

__all__ = ['SetupTankProject']

from butility import abstractmethod

from tank.depliy.tank_commands.setup_project import SetupProjectAction

from .schema import setup_project_schema


class SetupTankProject(SetupProjectAction, ApplicationSettingsMixin):
    """Should run a reaction to a newly created Shotgun project and sets it up to work with btank.
    As opposed to the default implementation, we will make it use our own, pre-existing shotgun connection,
    and use kvstore and environmental information.

    This implementation is not complete as it needs to learn about project locations, which are non-standard
    right in shotgun so wa can't know about it. See subclass interface for requirements.
    """
    __slots__ = ()

    _schema = setup_project_schema


    # -------------------------
    ## @name Subclass Interface
    # @{

    @abstractmethod
    def _project_location(self, sg, log, project_id):
        """@return a Path object to this hosts root for all projects, like '/mnt/projects'"""
        raise NotImplementedError("to be iplemented in subclass")

    ## -- End Subclass Interface -- @}

    # -------------------------
    ## @name Interface
    # @{

    def handle_project_setup(self, sg, log, project_id):
        """Deal with tank in order to get a new project setup accordingly.
        @param sg a shotgun connection
        @param log a logger
        @param project_id integer ID of the project to create
        """
        pass
    
    ## -- End Interface -- @}

    

# end class SetupTankProject
