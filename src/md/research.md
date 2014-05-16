# About Tank


## Coding and Software Organization

+ tk-core by now has a good test suite !
- Haven't seen tests in any app or hook. Testing is done manually, and in conjunction with the duplicated code portion, will eventually lead to undetected bugs.
+ TDs can reload code in-app, it's nice for them as they are not used to test-driven workflows anyway.
+ docs are nicely written and [good looking](https://toolkit.shotgunsoftware.com/entries/23783911)
- **sinful**: Main app's bundle logic with GUI, making it impossible to reproduce their logic in non-gui mode. The latter is neat for automation.
- Non test-driven development is encouraged by providing means to reload code while the application is running. This is probably what led to tanks major sin, see top of the document.
- Probably as some kind of workaround, required frameworks (if provided by tank) can't just be imported, but need a custom method to be called. They also have non-python compatible characters in their names, like dashes ... (maybe there is a way to convert them to their python names procedurally).
    - This makes deriving hooks from one another special too - you can inherit from the hook you are overriding, but someone else can't inherit from you as there is exactly one level of overrides for hooks.
    - There is a special syntax which allows multi-inheritance, which greatly re-invents the wheel. Inside of the hook, it's very abstract what your base actually is, and even worse, can change without the code knowing. Another form of redundancy.
- Hooks can access the parent app through `self.parent`, which doesn't help in isolating them.
- Tk-core is special, and typically shared. Can be localized, which makes it a standalone copy based on some other copy.
- Even hooks are defined in yaml, which is degenerating what can actually be done in a programming language. When extending implementation, its more powerful to use language facilities (i.e. types, delegate-patterns, events, plugin systems). They are supposed to be lightweight, but calling them is super expensive, even for python.
- Docs are separated from the code repositories. This means, they easily get out of sync with what's implemented, as the developer has to break out of the normal dev-environment. What's worse is that contributors can't make fixes while they are reading.
- it looks very expensive to use frameworks, as they are instantiated and loaded just for you. Even though it might be good for avoiding shared state and components affecting each other, I doubt it's really what you want.
- (plenty of code I would want to override is on module level, which forces me to monkey patch every single function. If it would be a class level method, only the class would need monkey patching, or instantiation. The latter would be the desired way.) - I don't think I will override framework loading.
- As they don't have a wrapper, they workaround this with dirty sys.path hacks. This makes their structure and way of working so much more complex ... it's not OK. There is a lot of code dancing around this fact !
    - this is also why there is lots of magic involved, and lots of assumptions about the folder structure. That's quite bad, as you will never guess why it's doing what it's doing (i.e. 'config/core/templates.yml' is special and used to find out if the core is 'localized')
- The more I dig into the code, the more redundancy I notice. There are 9 rather simmilar usages of the 'install_location.yml', building a path to it in 'config/core'. Argh, it gets worse the more you look ! They get paid by the line of codes they make, now it's clear.
+ different 'pipeline configurations' allow to do sandboxes/local testing. If configuration is linked up with git, it's actually maintainable.
+ can be started from existing pipelines, such that tank is clean enough not to do much on import. It relies on a `tk` singleton.
+ The code does a lot of error checking, especially when reading external files, which are unreliable by definition.



## `tank` commandline tool

- tank command subcommands are well documented online, but non-standard (e.g. no usage). The reason for this is that tank is parsing it's commandline arguments itself ... doing worse than what can be done with standard libraries. It's annoying not to get a list of available commands, but to have to [look them up online](https://toolkit.shotgunsoftware.com/entries/24024798-Administering-and-Configuring-Sgtk).
- tank commandline tools are based on a lot of interaction, querying the user for input. This actively discourages their integration into scripts, and kind of misses the target group
- Text files created by setup_project are executable for some reason



## Templates and Folders Creation

- **sinful**: to me it looks like the template system and the 'path schema' in the project configuration are different things. One is used for general paths when doing 'create paths ...' from shotgun or the commandline, the other is used in path templates for apps. This redundancy can make both go out of sync easily !! Really ? Of course they do it to have a simple way to copy skeletons automatically. But what are skeletons worth if they are not customized to the project ? It's a sin, as the path creation system should make sure paths and names are always right !
- path template system configuration is redundant, and inflexible (proof). You are forced to repeat yourself. There is a way ('inclusion'), but what's less redundant than a tree ?
- path inference needs to know the ‘type’ of path you look at. The 'type' is the template name. This means you can't 
- capitalization in dict keys [fields] for path template system (used to differentiate shotgun entity types [context fields] from custom template fields manipulated by apps). Capitalization shouldn't be important, but it is as it is used to match shotgun entity names.
- app-configuration is one per file. Overrides are done redundantly per environment. It's a general issue though if no central cascading tree is used (like kvstore)
- good: versions in yaml have ‘v’ prefix to make sure they become string, not float, even without quoting them. Actually, it's not done like that in real configuration files, so it seems redundant.
+ They warn the user when launching the toolkit with so far untested versions of the host application.
+ path template validation. `bsemantic` does this in test-cases, but something similar must exist to make it failsafe/easy to use. To not be forced to put everything into yaml, the system could collect plugins that support a certain interface, and call their generators to see if a particular context can work.
+ deferred path creation is a good, as it will create directories only when the asset is actually worked on. My way of doing it would be to respond to particular changes though, so the directory and basesetup is created when the task is assigned or set to in-progress. Nonetheless, I see the point.
+ template system can be used for paths and strings
+ multi-root configuration is possible, and easy to configure, but verbose as everything.
+ It's possible to centralize configuration while maintaining the ability to make overrides by using configuration includes
    + it's possible to use information from the context in these paths for substitution (similar to what seems to work in many places where paths are involved)
- **sinful** Tank is using a `path_cache.db`, which maps local paths to the entities they represent. This is a huge problem, as it can easily go out of sync with what's actually on the filesystem. When that happens, think start to fail. Besides, sqlite is used on a shared space, which is guaranteed to [fail in concurrent situations](http://sqlite.org/faq.html#q5).


## Configuration System

- Upgrade config files on schema change
    - Even though I think there should be viable defaults, this is not always possible. Generally one should refrain from introducing changes that break an application if a piece of information doesn't exist. Instead, the application should deal with it. It's good to have a facility that can handle these updates though.
    - Upgrading means rewriting, which would probably drop comments ... .
- Redundant per context configuration (aka environments) (see what's good as a partial remediation to this issue)
    - This seems like a workaround to a 'single-file' configuration system paradigm.
    - you are forced to repeat yourself when configuring apps (-maintainability, +complexity)
    - there are ways to centralize the configuration using git, or to make inclusions, which can reduce the impact of this issue. Still it's just not as good as having a base and pulling in overrides.
- environment configuration files are non-sparse, which means a lot of text that just says 'default' as value. Whenever someone adds a new attribute/property in the engine/app configuration, your configuration files will not see it anyway, and thus be 'sparse' unintentionally. This leaves you with unnecessarily verbose configuration that I dislike already.
+ Provided the 'semantic configuration file names' feature for environments is dynamic, configuration selection by context is something `bcore` doesn't do right now. This runtime feature could be implemented easily though, provided we have context information. Done in the 'pick_environment' hook - the equivalent would be done in a custom Application (for runtime changes) or a delegate for pre-runtime changes. The latter is more powerful as the entire program configuration can be adjusted properly.
+ yaml-configurable schemas for pretty much everything. bapp could make that possible, after all it's just a KeyValueStoreSchema from settings
+ very declarative when it comes to what code requires to work, e.g. which environment code expects. In `bcore`, there is no such thing as code specific to a particular environment will have a package requirement to the needed package, will be a plugin that implements an interface. The latter is abstract.
+ As required framework versions are specified per application, it's easy to have one application which prevents anything to come up. In `bcore`, this check is left to the code (and to the one writing configuration files) - but the code will only recognize the version issue when the applications is launched. Chances are that it isn't even called. However, `bcore` isn't able to determine if packages have incompatible requirements, in terms of the version they need.
+ Automatic shotgun schema upgrades - engines or apps in need for a particular field will be sure to have it.
+ at least environment variables can be used to specify hooks, `{$EVAR}/path/to/hook.py`. That will make customizations so much easier, considering bprocess will be used to set everything up.
+ there is a 'dict' value type, which allows one level of nesting for values, effectively. But not more.
+ tank has more meta-data for its schema's than the kvstore. The latter wants it that way, yet `bproperties` could be used to one day get more meta-data for schema values. After all GUIs will want to have that.
- Configuration is handled manually by default, and even though there are tools to help managing it, by default there is not RCS. This is inherently dangerous on sites that have many developers. `push_configuration` for instance replaces the desired target configuration with the one you are seeing, making a zip backup of the previous configuration files. The docs say nothing how to roll back using one of these, or how to verify that no one else edited them prior to that.
+ studio level base configuration can be put into git, and then used as base from which to clone when creating new configurations. Interestingly, this doesn't seem to include environments at all, at least not according to the docs. What is it worth without it ? Oh, one more example later and it seems it can do it that way. Good. Well, trying it shows that he can also copy a file path, and doesn't get that this is actually a git repository. Nonetheless, this can be fixed after the fact (by putting the repo) using a path of the form described at `tank/deploy/git_descriptor.py:34`.
    - It's actually exactly the same as what's done with `tk-config-default` or `tk-config-multiroot`



## Application Launcher

- can only launch packaged programs on OSX, like _/Applications/Nuke8.0v4/Nuke8.0v4.app_, whereas _/Applications/Nuke8.0v4/Nuke8.0v4.app/Nuke8.0v4_ doesn't work (but works on commandline)
- it takes about 5s until the application even starts to load when launched from the shotgun web gui



## Workflow

- In order to obtain shot folders, one has to perform an action manually. What you want is to set the status of the shot to something indicating it can now be handled, and have the system create the paths for you. However, folder creation is automatically done when launching an application.
- It seems by default, new files have no name, so user is free to choose. This needs customization, but might be intended for the default configuration.
    - You have to use 'Shotgun Save As ...' in order to land save in right folder 
    - For some reason, it doesn't allow '_-' by default (??)
+ Context can dynamically change, see 'Work Files App', or 'pick_environment' hook



## Engines

* Not all engines support `TANK_FILE_TO_OPEN`, they simply don't implement it, but delete the variable from the environment.


# Insights

## Configuration and Structure

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

### BUNDLE Configuration

A [bundle](https://toolkit.shotgunsoftware.com/entries/22275546-How-to-write-Apps#The%20Template%20Starter%20App) is identified exclusively through it's manifest, `info.yml`. It's well documented, and handled by tank entirely. You won't have to touch it unless you are an app developer.

It's worth nothing though that the `tk-core` bundle has special wrapper scripts at `BUNDLE/setup/root_binaries/tank[.bat]` which are copied to the PROJECT configuration whenever a new project is setup. They are called by the shotgun web GUI, see _How Shotgun Web integrates with Tank_.

### TANK_STUDIO Configuration and Installation

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


### PROJECT Configuration

This seems to be a more hard-coded location, as it is always in the PROJECT root, no matter where you install the tank configuration to. It hosts the following files

* `PROJECT/tank/cache/path_cache.db`
    - Contains a mapping between the project-relative path on disk and the entity with meta-data. From there, tank knows what to do with the file.
    - It's heavily used, and really needs to be fast.
    - Written whenever an asset is touched, each token of a path that corresponds to an Entity is listed there. A shot like 'shots/<sequence>/<shot>' leaves its sequence entity there, as well as its shot entity.
    - **If it gets lost or is corrupted, tank will be rather blind**
* `PROJECT/tank/config/tank_configs.yml`
    - Contains the project's TANK configuration locations for all platforms as absolute paths.
    - It doesn't look like environment variables are resolved when handling the data, which makes it hard to impossible to make it relocatable.

### TANK_PROJECT Configuration

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

### SHOTGUN Configuration

The `PipelineConfiguration` entity contains the project's `TANK_PROJECT` root paths for all platforms, and allows the shotgun web gui to find the `tank` executable at `TANK_PROJECT/tank` to obtain tank related information and work with the file system.

In conjunction with the shotgun plugin (formerly java plugin), this allows shotgun to execute arbitrary files and obtain their standard output (at least) and exit code. This is used to populate right-click menues with configured launchers, and to execute tank commands on the user's machine.

## How Shotgun Web integrates with Tank

The shotgun plugin is able to execute files, and that's it. This capability is used to launch the project-specific tank executable. This one is known thanks to the 'primary' (or whichever) PipelineConfiguration entity associated with the project.

This command is a boostrapper which loads tk-core and uses it for evaluating the configuration, returning values interpreted by java script (?).

Those are typical invocation the gui frontend does, including their return values

```bash
${config}/tank shotgun_cache_actions Asset shotgun_mac_asset.txt
# writes the specified text file - apparently configuration loading is slow enough to require
# a speed up. This is something to think about when bringing in own tools,  
# who should be fast too
${config}/tank shotgun_get_actions shotgun_mac_asset.txt shotgun_asset.yml
# Runs in 0.017 seconds, bash only
> launch_nuke$Launch Nuke$$False
> show_in_filesystem$Show in File System$$True
> launch_photoshop$Launch Photoshop$$False
> preview_folders$Preview Create Folders$$True
> create_folders$Create Folders$$True
> launch_screeningroom$Show in Screening Room$$False
> launch_maya$Launch Maya$$False
${config}/tank shotgun_run_action launch_nuke Task 2517
# launches nuke, after redirecting the call to tank_cmd_login.sh, which is similar to tank_cmd.sh
# but uses a different shebang. Copy-past at its finest.
# In the end it launches tank like so (after setting the PYTHONPATH accordingly)
# /System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python [...]/dependencies/lib/tank/studio/install/core/scripts/tank_cmd.py [...]/dependencies/lib/tank/studio shotgun_run_action launch_maya Task 2517 --pc=[...]/PROJECT/etc/tank
# It is refusing to use the CWD for anything (as a native context for instance)
# This command takes exactly 7s due to various shotgun queries, until it finally launches nuke
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


## The `tank` command startup sequence

As called by the web gui, or from the commandline

* scripts located in `STUDIO/install/core/[scripts|setup]`
* call sequence: `TANK_PROJECT/tank[.bat]` -> `TANK_STUDIO/install/core/scripts/tank_cmd[.bat|_login.sh|.sh]` -> `TANK_STUDIO/install/core/scripts/tank_cmd.py`

Note that the TANK_STUDIO/tank startup sequence is similar, but determines by *the presence or absence of files* what kind of installation it is. For example, the presence of the `TANK_STUDIO/config/core/templates.yml` indicates a project installation, and maybe even that it is localized.

## Tank Context and how engines start up

In order to bring contextual information to the application, tank can use various ways. Generally, it can do it by path, and by entity.

When launching something from the built-in launchers, the context is set using a pickled dict, containing entity data.

### Environment Variables

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



# Interesting - for evaluation

* Direct and deferred path creation (once in shotgun, once at app start ??)
* path inference (obtain fields from path) if template is known
* context keeps asset association/shotgun data link
* department/process related app configurations are determined as such, whereas `bcore` uses different wrapper configurations (which allow to do more, effectively, see package.include). It’s called *environment*
* core-> engines-> apps -> hooks
    * engines are application specific, and seem to be brought up by core
    * apps are engine plugins, hooks are app plugins
    * frameworks are used by apps or engines
    * apps can use other apps, which makes them kind of an executable framework.
* app location configuration parameter should allow it to be local (but only so if kvstore resolution is used). Their configuration could in fact be coming from a kvstore, schemas will not overlap.
* core hooks allow to choose environments, or make fundamental business logic decisions (e.g. *PIPELINE_CONFIG/core/hooks/pick_environment.py*)
* tank does 'app' configuration at runtime (and makes them available), whereas bprocess is doing it before runtime. Both would combine well, so there might be no need to use bprocess for anything app related.
* 'shotgun_entitytype.yaml' environment file to configure in-browser RMB menus
* pipeline configurations are entities in shotgun, created by the API, pointing to the tank location on a per-project basis. This is where sandboxes are setup. They might support environment variables.
* `sg_connection` studio hook in config/core allows to return custom connection types ... oh actually it's adjusting the connection settings - crowed too soon.


![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)



# BTank and Tank

* `TODO`: write about the setup I am building and why, and how it's done. This could move into the readme, possibly. Write note about studio level configuration, and how it works.

# Goals

+ Install it within the standard dependencies assembly, initially there might be no way around the redundant configuration issue. After all, tank must be able to find its manifest files.
+ separate studio configuration from installation location, maybe just using symlinks
* Make it use kvstore (if configuration turns out to be too redundant, especially with paths)
* Make it use bsemantic

* use own sg connection implementation (from bshotgun)
* make it use bprocess when starting applications, especially the shotgun plugin to get browser support

