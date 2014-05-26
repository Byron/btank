# Configuration and Structure

It looks like tank is literally spitting them everywhere. Generally we differentiate between `studio`, `project` and `localized` configuration types, as well as per-bundle configuration, and configuration within shotgun itself.

Let's define some abstract root paths, which are used when denoting any paths

* `BUNDLE`
    - A bundle is anything that tank deals with, like `tk-core`, _engines_ or _apps_. Note that hooks are no bundles, but just single python files
* `TANK_STUDIO`
    - points to the studio configuration, usually at /mnt/software/tank/studio
* `PROJECT`
    - points to the project data directory, e.g. at /mnt/projects/myproject
* `TANK_PROJECT`
    - points to the per-project configuration/installation of tank, e.g. PROJECT/etc/tank . Typically, this points to PROJECT/tank, which is also why tank duplicates its folder structure partially.
* `SHOTGUN`
    - Is merely a marker to indicate we are looking at data in the studios shotgun instance

Everything written in the following is based on my knowledge so far, obtained through reverse-engineering.

## BUNDLE Configuration

A [bundle](https://toolkit.shotgunsoftware.com/entries/22275546-How-to-write-Apps#The%20Template%20Starter%20App) is identified exclusively through it's manifest, `info.yml`. It's well documented, and handled by tank entirely. You won't have to touch it unless you are an app developer.

It's worth nothing though that the `tk-core` bundle has special wrapper scripts at `BUNDLE/setup/root_binaries/tank[.bat]` which are copied to the PROJECT configuration whenever a new project is setup. They are called by the shotgun web GUI, see _How Shotgun Web integrates with Tank_.

## TANK_STUDIO Configuration and Installation

By default, the TANK_STUDIO root only contains basic configuration that will rarely change, and an installation of `tk-core` (a single version), and all `required` _engines_ and _apps_. The term `required` means that tank will automatically install what's needed based on PROJECT configuration when the first one is initialized. As most people start out with the `tk-config-default` one, they will end up with about 625MB on disk. The data is quite redundant, so git compresses it down to 150MB. The _engines_ and _apps_ may exist in various versions in parallel, which allows you to switch between them safely.

`tk-core` maintains its own installation, organizing its bundles like so:

```
TANK_STUDIO/install/BUNDLE_TYPE/SOURCE    /BUNDLE_NAME/VERSION/
TANK_STUDIO/install/engines    /app_store/tk-maya     /v0.4.1
```

The core itself is located at `TANK_STUDIO/install/core`.

Therefore, core doesn't support versions, as it has to serve as an entry point that needs to be known very well. In theory, I believe multi-version cores can be implemented even with the current version, but consistent upgrade paths might be difficult to achieve if people jump between versions.

A fresh installation places the studio configuration into `TANK_STUDIO/config/core`, which contains the following files

* `app_store.yml`
    - Looks to me like a shotgun instance with information about where to download things. I didn't dig into it as it's not relevant for me right now.
* `install_location.yml`
    - Contains three paths, each with an *absolute* path of the installation directory. The code handling it *doesn't* resolve environment variables, which makes it difficult to make it location independent.
    - I will have to dig into the code more and try things before I can tell how it's possible to circumvent these 'hardcoded' paths for more location independence.
* `shotgun.yml`
    - Looks unsurprisingly similar to the `app_store.yml`, providing login information for the studio's shotgun instance.
* `interpreter_[Darwin|Linux|Windows].cfg
    - They contain just one line: the path to the system's python interpreter on the respective platform. It's read by the phase 2 tank bootstrapper (`tank_cmd[_login].sh`) to find the interpreter to use for launching `tank_cmd.py`. See 'The `tank` command startup sequence'


## PROJECT Configuration

This seems to be a more hard-coded location, as it is always in the PROJECT root, no matter where you install the tank configuration to, and is required for tank to find its context from any path within the project. To do that, it will search upwards from a given project path and try to find a 'tank' directory, which will be used to find the pipeline configuration for that project, and complete the bootstrapping process.

It hosts the following files

* `PROJECT/tank/cache/path_cache.db`
    - Contains a mapping between the project-relative path on disk and the entity with meta-data. From there, tank knows what to do with the file.
    - It's heavily used, and really needs to be fast.
    - Written whenever an asset is touched, each token of a path that corresponds to an Entity is listed there. A shot like 'shots/<sequence>/<shot>' leaves its sequence entity there, as well as its shot entity.
    - **If it gets lost or is corrupted, tank will be rather blind**
* `PROJECT/tank/config/tank_configs.yml`
    - Contains the project's TANK configuration locations for all platforms as absolute paths.
    - It doesn't look like environment variables are resolved when handling the data, which makes it hard to impossible to make it relocatable.

## TANK_PROJECT Configuration

This is a big one, as it keeps plenty of interesting caches and configuration files and shows that tank tries really hard to be somewhat pseudo relocatable. Primarily it masks that the actual installation is in the TANK_STUDIO root.

The caches are located at `TANK_PROJECT/cache`

* `cache/shotgun_<platform_short>_<entity_type>.txt`
    - A cache created by the shotgun command, and for the phase 1 bootstrapper scripts to be able to quickly return launcher information on a per-platform per-entity-type basis. Their contents is a digest of what was contained in the studio configuration. The latter needs to be interpreted by the python code, which tends to be quite slow compared to bare bash.
    - The `tank[.bat]` phase one wrapper will check for these queries and return the cache if possible. Otherwise it hands over to phase 2, which reaches python to do the work just once.
    - Whenever there is a page-reload, the cache is refreshed, which also ensures configuration changes are picked up quickly. It also means that one of there are plenty of expensive calls while browsing (python is the slow part)
* `BUNDLE_NAME`
    - pretty much a dump for bundles (apps, frameworks, engines) with free-form cache data underneath
    - commonly used  as icon and image cache, to save expensive lookups from the web. This could also mean the cache goes out of date unless some sort of TTL is implemented.

The second largest part is the `TANK_PROJECT/install` directory, which superficially looks like the `TANK_STUDIO/install` location. Except for it's all fake to simulate some expected structure for some scripts that should work there and in the actual `TANK_STUDIO/install` location.

The interesting files are in `TANK_PROJECT/install/core`

* `core_[Darwin|Linux|Windows].cfg`
    - A file with just a single line being an absolute path to the `TANK_STUDIO` location.
    - Interpreted by the scripts explained below
* `python/[sgtk|tank]/__init__.py`
    - A great example for how marketing decisions force programmers to introduce redundancy and even more complexity: `tank` was renamed to `sgtk` when it went from alpha to beta. Using some tricks, old code can still use `tank` internally, whereas new code can use `sgtk`
    - a so called `proxy wrapper` which loads the files mentioned above, and manipulates the `sys.path` and **TANK_CURRENT_PC** environment variable to call home, the actual implementation at `TANK_STUDIO`. The latter can then determine where it is coming from using the said environment variable, reading config files and so on.

Now we enter the heart of the configuration, `TANK_PROJECT/config`. It noteworthy that it is a bundle, which means that it can be 'installed' with git and versioned. It's part of the 'evolving configuration' paradigm, and can be replaced by other, possibly pre-made, configurations 'relatively' easily. Those could be `tk-config-default` or `tk-config-multi-root`.

The `config` bundle can be supposedly be used by apps and frameworks to grab icons, hooks and configuration files. However, I believe it's primarily used by `tk-core` and then given to other bundles through APIs. Didn't dig into that though.

* `info.yml`
    - Shows it's a bundle, but I am not sure if it used that way.
* `after_project_create.py`
    - I don't actually know why a hook was dropped there, outside of it's native habitat, the `hooks` folder.

As most of the contents is well described in the official docs, I will focus on the files interesting to the `tank` startup. Let's look at `TANK_PROJECT/config/core`. All files not mentioned here are the same as in `TANK_STUDIO/config/core`

* `install_location.yml`
    - It's a reflection of the information in the `primary` pipeline configuration entity of the respective project, containing multi-platform paths to `TANK_PROJECT`
    - It's a somewhat redundant copy of `PROJECT/tank/config/tank_configs.yml`, and environment variables in paths are not resolved when it's handled.
* `pipeline_configuration.yml`
    - It's the reverse of the `install_location.yml`, containing the entity information for querying the PipelineConfiguration entity which in turn contains path information similar to `install_location.yml`, next to other web gui related stuff.
* `roots.yml`
    - Contains multi-platform paths similar to the SHOTGUN information regarding it's primary **Local File Storage** .
    - It's keyed to that multiple **Local File Storage** roots can be cached there, and I believe it's used when resolving templates and when using the path schema for creating folders and skeletons.

## SHOTGUN Configuration

The `PipelineConfiguration` entity contains the project's `TANK_PROJECT` root paths for all platforms, and allows the shotgun web gui to find the `tank` executable at `TANK_PROJECT/tank` to obtain tank related information and work with the file system.

In conjunction with the shotgun plugin (formerly java plugin), this allows shotgun to execute arbitrary files and obtain their standard output, standard error and exit code. This is used to populate right-click menues with configured launchers, and to execute tank commands on the user's machine.

# How Shotgun Web integrates with Tank

The shotgun plugin is able to execute files, and that's it. This capability is used to launch the project-specific tank executable. This one is known thanks to the 'primary' (or whichever) PipelineConfiguration entity associated with the project.

This command is a boostrapper which loads tk-core and uses it for evaluating the configuration, returning values interpreted by java script (?).

Those are typical invocation the gui frontend does, including their return values

```bash
${config}/tank shotgun_cache_actions Asset shotgun_mac_asset.txt
ins writes the specified text file - apparently configuration loading is slow enough to require
 a speed up. This is something to think about when bringing in own tools,  
 who should be fast too
${config}/tank shotgun_get_actions shotgun_mac_asset.txt shotgun_asset.yml
 Runs in 0.017 seconds, bash only
> launch_nuke$Launch Nuke$$False
> show_in_filesystem$Show in File System$$True
> launch_photoshop$Launch Photoshop$$False
> preview_folders$Preview Create Folders$$True
> create_folders$Create Folders$$True
> launch_screeningroom$Show in Screening Room$$False
> launch_maya$Launch Maya$$False
${config}/tank shotgun_run_action launch_nuke Task 2517
 launches nuke, after redirecting the call to tank_cmd_login.sh, which is similar to tank_cmd.sh
 but uses a different shebang. Copy-past at its finest.
 In the end it launches tank like so (after setting the PYTHONPATH accordingly)
 /System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python [...]/dependencies/lib/tank/studio/install/core/scripts/tank_cmd.py [...]/dependencies/lib/tank/studio shotgun_run_action launch_maya Task 2517 --pc=[...]/PROJECT/etc/tank
 It is refusing to use the CWD for anything (as a native context for instance)
 This command takes exactly 7s due to various shotgun queries, until it finally launches nuke
```

Conclusions are

* the project tank executable needs to be as fast as possible
    - It blocks the web-frontend, which waits with drawing until command returns.
    - If our own wrapper can easily be integrated by adjusting the studio installation's tank command at _install/core/scripts/tank_cmd.py_
* The python command itself is extremely slow at launching applications, probably due to various shotgun queries it does in the process.
    - It takes quite unacceptable 7s in my tests to commence launching any application.
        + tank itself is initialized after 0.22s (`tk = tank.tank_from_path(pipeline_config_root)`)
        + a context is available (from entity) after 0.8s (`ctx = tk.context_from_entity(entity_type, entity_ids[0])`)
        + an engine is available after 2.7s (`e = engine.start_shotgun_engine(tk, entity_type, ctx)`)
        + executes the actual command, which returns after a whopping 7s (`e.execute_command(action_name)`)
* On the setup I work with (sluggish smb-share, mounted on OSX), the wrapper takes 3s to launch anything, which brings overall application startup time to 10s
    - However, I believe that the information that ends up in the application is nearly entirely known, which makes filling out the data easy. Combined with an sql read cache, startup can be done in 3.5s or less, with the bcore in charge of course.


# The `tank` command startup sequence

As called by the web gui, or from the commandline

* scripts located in `STUDIO/install/core/[scripts|setup]`
* call sequence: `TANK_PROJECT/tank[.bat]` -> `TANK_STUDIO/install/core/scripts/tank_cmd[.bat|_login.sh|.sh]` -> `TANK_STUDIO/install/core/scripts/tank_cmd.py`

Note that the TANK_STUDIO/tank startup sequence is similar, but determines by *the presence or absence of files* what kind of installation it is. For example, the presence of the `TANK_STUDIO/config/core/templates.yml` indicates a project installation, and maybe even that it is localized.

# Tank Context and how engines start up

In order to bring contextual information to the application, tank can use various ways. Generally, it can do it by path, and by entity.

When launching something from the built-in launchers, the context is set using a pickled dict, containing entity data.

## Environment Variables

* tk-core is their entry point and must be in the PYTHONPATH, e.g. '[...]/studio/install/core/python'
* `TANK_CURRENT_PC`
    - '/Volumes/raid_V/pipelinetest2014/etc/tank'
* `TANK_CONTEXT`
    - pickle of `{ '_pc_path': '[...]/PROJECT/etc/tank',
         'additional_entities': [],
         'entity': {'id': 887, 'name': 'bob', 'type': 'Asset'},
         'project': {'id': 638, 'name': 'PROJECT', 'type': 'Project'},
         'step': None,
         'task': None,
         'user': None}`        
* `TANK_ENGINE`, like 'tk-maya' . The latter is only important for bootstrapping, of course this can be done by an own facility as well. In the end, you 
* `TANK_FILE_TO_OPEN` - a file that should be opened right away. Warning: depends on the engine's implementation, maya deferres for instance, which will be troublesome in batch mode. But who needs batch mode ;).


