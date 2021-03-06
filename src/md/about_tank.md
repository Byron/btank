# About Tank


## Coding and Software Organization

- tk-core by now has a test suite - measured coverage is an incredible **43%**
- Haven't seen tests in any app or hook. Testing is done manually, and in conjunction with the duplicated code portion, will eventually lead to undetected bugs.
+ TDs can reload code in-app, it's nice for them as they are not used to test-driven workflows anyway.
+ docs are nicely written and [good looking](https://tank.zendesk.com/entries/23874562)
- **sinful**: Main app's bundle logic with GUI, making it impossible to reproduce their logic in non-gui mode. The latter is neat for automation.
- Non test-driven development is encouraged by providing means to reload code while the application is running. This is probably what led to tanks major sin, see top of the document.
- Probably as some kind of workaround, required frameworks (if provided by tank) can't just be imported, but need a custom method to be called. They also have non-python compatible characters in their names, like dashes ... (maybe there is a way to convert them to their python names procedurally).
    - This makes deriving hooks from one another special too - you can inherit from the hook you are overriding, but someone else can't inherit from you as there is exactly one level of overrides for hooks.
    - As it's special, hook derivation doesn't work for core hooks ! It's clearly a 'special case bug'
    - There is a special syntax which allows multi-inheritance, which greatly re-invents the wheel. Inside of the hook, it's very abstract what your base actually is, and even worse, can change without the code knowing. Another form of redundancy.
    + reloading of all code is possible this way, but requires all in-memory instance to be closed/tossed out before you see an effect.
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
- **sinful** As a python 2 application, it doesn't properly deal with unicode strings. They are better not passed to anything that does type checking, as these usually compare by string, not using isinstance. In short, python 2/3 application will have to be very careful when using the API. However, this issue is more of a problem of python 2 code, than tank per se.
- **sinful**: It's common in tank to create circular references whenever you create a tank instance. That way, long-running processes like daemons will leak memory whenever they use tank. In the case of a shotgun-events daemon, it will create various tank instances for all projects it touches.
This is why daemons should be prepared to crash and respawn whenever they run out of memory.
- In terms of modularity, tank knows `frameworks`, 'engines', and `apps`. Hooks are custom callbacks, one per file in a predefined location. Apps my retrieve instance of other apps, making them appear a little like frameworks, dissolving the arbitrary boundary between them.


## `tank` commandline tool

- tank command subcommands are well documented online, but non-standard (e.g. no usage). The reason for this is that tank is parsing it's commandline arguments itself ... doing worse than what can be done with standard libraries. It's annoying not to get a list of available commands, but to have to [look them up online](https://toolkit.shotgunsoftware.com/entries/24024798-Administering-and-Configuring-Sgtk).
+ implementations of tank commandline tools have an interactive and an API mode, which caters both humans and API users. 
    - However, this seems to be depending on the command, not all can be run in non-interactive mode as it needs special implementation for some reason.
- Text files created by setup_project are executable for some reason



## Templates and Folders Creation

- **sinful**: to me it looks like the template system and the 'path schema' in the project configuration are different things. One is used for general paths when doing 'create paths ...' from shotgun or the commandline, the other is used in path templates for apps. This redundancy can make both go out of sync easily !! Really ? Of course they do it to have a simple way to copy skeletons automatically. But what are skeletons worth if they are not customized to the project ? It's a sin, as the path creation system should make sure paths and names are always right !
    - The implication of this is that you can specify folders structures using conditions that you can't express as templates as these conditions can't be expressed there. This forces you to have complex 'pick_environment' hooks to allow configuring specialized templates. In other words, copy-paste will be required, and your environment configuration will be bloated.
    - It's not possible to create path templates that don't contain a slash, for example to denote the base of a filename which is supposed to be substituted. That way, you are forced to repeat yourself, further adding to the generally perceived redundancy.
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
- **sinful** Tank is using a `path_cache.db`, which maps local paths to the entities they represent. This is a huge problem, as it can easily go out of sync with what's actually on the filesystem. When that happens, think start to fail. Besides, sqlite is used on a shared space, which is guaranteed to [fail in concurrent situations](http://sqlite.org/faq.html#q5). To add insult to injury, it's not a cache, but an index that is required for tank to work. Throw away a cache, and it will be regenerated, throw away an index, and you are in trouble !
+ support for optional fields (`foo[_{optional}]` becomes `foo` if optional field is not present)
- overly complicated filter specification in entity query
+ can refer to entities defined in any parents, somehow it can substitute into _the right thing™_
+ alter folder structure depending on actual shotgun entity data
+ substitution dictionary can actively be filled while traversing the tree, using queries
+ access to linked fields via dot notation during folder creation
+ deferred creation tied to engine startup - can be limited to particular engines
+ can copy contents of entire folders, also conditional depending on presence of entity in context
+ can create symlinks
+ any meta-data can be passed to hooks for their interpretation
+ delegation of any corresponding action, using a hook
+ substitution keys in templates have meta-data on their own, which makes templates more readable
- special key-aliasing is required to support different settings for the same (internal) key name
+ templates are multi-root compatible, requires extended configuration style. Folder schema is multi-root too
+ templates can easily be shared, to link outputs of one application to the inputs of another
+ custom fields can be attached to entities and used as folder names
- tank enforces that each template maps to a unique path. However, it has no understanding of whether the template refers to a directory or file, which is why it enforces 'work-arreas' to not be shared among applications.

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
- install command rewrites your own configuration files. This is always undesirable, as formatting can change considerably. A good system would be to write files containing the required changes based on the current settings, which is consecutively merged in  
- during deferred folder creation, the launch-app (or however starts up the host application) has to unconditionally create folders for a particular entity, which adds a few seconds to the application startup time. If folder creation would be triggered at the time a template is used, and only if the folder leading up to some file doesn't exist, this could be circumvented.
- When creating a new project, the location of that project determined by the project configuration itself, and there is no easy way to override it. Even though it's possible to place the tank configuration anywhere, information about where the project data along with some caches resides is determined solely by the `roots.yml` coming which should be a part of the tank configuration you are using as template. That way, it's difficult to have a standard studio configuration yet to place new projects using it in different shares to balance load.



## Application Launcher

- can only launch packaged programs on OSX, like _/Applications/Nuke8.0v4/Nuke8.0v4.app_, whereas _/Applications/Nuke8.0v4/Nuke8.0v4.app/Nuke8.0v4_ doesn't work (but works on commandline)
- it takes about 5s until the application even starts to load when launched from the shotgun web gui
- app launcher application will alter the current process' environment, which makes it somewhat dangerous to use from within an application (i.e. to start RV from within nuke, in a pipeline-conform way)



## Workflow

- In order to obtain shot folders, one has to perform an action manually. What you want is to set the status of the shot to something indicating it can now be handled, and have the system create the paths for you. However, folder creation is automatically done when launching an application.
- You have to use 'Shotgun Save As ...' in order to land save in right folder 
- For some reason, it doesn't allow '_-' by default (??)
+ Context can dynamically change, see 'Work Files App', or 'pick_environment' hook
- **sinful** operations that alter shotgun and/or write files are not atomic, which means that a failing thumbnail upload can easily make a publish fail right in the end, yet plenty of files have already been written to final location on disk. Inconsistencies are thus actively created by the system.
- It seems that asset publishes inherit the version number of their scene file. If there is a scene file with the same name, it's an error. Most certainly, this can be customized though.
- **sinful**: Apps providing GUI and implementing business logic do not separate the logic from the GUI, which makes it less trivial to publish properly than necessary. The non-gui publish handler for instance makes calls to qt message boxes for instance.


## Engines

* Not all engines support `TANK_FILE_TO_OPEN`, they simply don't implement it, but delete the variable from the environment.

### Nuke Engine

- Publishes take a long time, it seems slower than necessary (not talking about time it takes to upload)
    - 'Checking files' is slow, as well as file copy. 250 files with 6.1 MB total size took about 30 seconds for checking, and 5 for copying (on an SSD)
    - It rerenders the entire sequence to get a movie file, instead of using the required rendered images to generate a movie from these.
    + on the plus side, while uploading the user can keep working on the file.
- image resolutions are configured per app and step, it feels like it should just be one of many possible resolutions, which can be mixed and matched with output specifications.
- The nuke write node has it's own output specifications, which need to come from the configuration. It seems odd, as such a thing influences the entire project, so output specifications or resolutions want to be configured for the entire project, and used in various places. Not having it that way adds to redundancy, which makes it harder to keep configuration consistent.


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


# BTank and Tank

* `TODO`: write about the setup I am building and why, and how it's done. This could move into the readme, possibly. Write note about studio level configuration, and how it works.

![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)


