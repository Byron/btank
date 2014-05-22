#-*-coding:utf-8-*-
"""
@package btank.plugins.bprocess
@brief contains a delegate to deal with tank commandline startup

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['TankDelegate']

import os

import bapp
from butility import Path
from bprocess import process_schema



class TankDelegate(ProcessControllerDelegate, bapp.plugin_type()):
    """process arguments to be suitable for tank.
    Additinoally we can intercept launch commands and execute them ourselves.
    """

    tank_pc_arg='--pc='

    # -------------------------
    ## @name Interface Overrides
    # @{
    
    def pre_start(self, executable, env, args, cwd, resolve):
        executable, env, new_args, cwd = super(TankDelegate, self).pre_start(executable, env, args, cwd, resolve)

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
            actual_executable = self._app.context().settings().value_by_schema(process_schema).executable
            base = actual_executable.dirname()
            assert (base / 'tank').exists(), "Currently '%s' must be right next to the 'tank' executable" % executable
            new_args.append(self.tank_pc_arg + base)
        # end setup context

        return (executable, env, new_args, cwd)

    ## -- End Interface Overrides -- @}
