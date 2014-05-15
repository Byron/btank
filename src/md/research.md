## Tank - What's sinful

* Main app's bundle logic with GUI, making it impossible to reproduce their logic in non-gui mode. The latter is neat for automation.

## Tank - What’s not so good

* Upgrade config files on schema change
    - Even though I think there should be viable defaults, this is not always possible. Generally one should refrain from introducing changes that break an application if a piece of information doesn't exist. Instead, the application should deal with it. It's good to have a facility that can handle these updates though.
* Redundant per context configuration (aka environments) (see what's good as a partial remediation to this issue)
    - This seems like a workaround to a 'single-file' configuration system paradigm.
    - you are forced to repeat yourself when configuring apps (-maintainability, +complexity)
* Tk-core is special, and typically shared
* path - asset association is stored in a shared sqlite database (known for inconsistency on network shares)
* path template system configuration is redundant, and inflexible (proof). You are forced to repeat yourself. There is a way ('inclusion'), but what's less redundant than a tree ?
* path inference needs to know the ‘type’ of path you look at
* capitalization in dict keys [fields] for path template system (used to differentiate shotgun entity types [context fields] from custom template fields manipulated by apps)
* app-configuration is one per file. Overrides are done redundantly per environment. It's a general issue though if no central cascading tree is used (like kvstore)
* good: versions in yaml have ‘v’ prefix to make sure they become string, not float, even without quoting them. Actually, it's not done like that in real configuration files, so it seems redundant actually.
* Even hooks are defined in yaml, which is degenerating what can actually be done in a programming language. When extending implementation, its more powerful to use language facilities (i.e. types, delegate-patterns, events, plugin systems). They are supposed to be lightweight, but calling them is super expensive, even for python.
* Non test-driven development is encouraged by providing means to reload code while the application is running. This is probably what led to tanks major sin, see top of the document.
* Probably as some kind of workaround, required frameworks (if provided by tank) can't just be imported, but need a custom method to be called. They also have non-python compatible characters in their names, like dashes ... (maybe there is a way to convert them to their python names procedurally).
    - This makes deriving hooks from one another special too - you can inherit from the hook you are overriding, but someone else can't inherit from you as there is exactly one level of overrides for hooks.
    - There is a special syntax which allows multi-inheritance, which greatly re-invents the wheel. Inside of the hook, it's very abstract what your base actually is, and even worse, can change without the code knowing. Another form of redundancy.
* Hooks can access the parent app through `self.parent`, which doesn't help in isolating them.
* Docs are separated from the code repositories. This means, they easily get out of sync with what's implemented, as the developer has to break out of the normal dev-environment. What's worse is that contributors can't make fixes while they are reading.
* it looks very expensive to use frameworks, as they are instantiated and loaded just for you. Even though it might be good for avoiding shared state and components affecting each other, I doubt it's really what you want.
* (plenty of code I would want to override is on module level, which forces me to monkey patch every single function. If it would be a class level method, only the class would need monkey patching, or instantiation. The latter would be the desired way.) - I don't think I will override framework loading.
* tank commands are well documented, but non-standard (e.g. no usage)
* environment configuration files are non-sparse, which means a lot of text that just says 'default' as value. Whenever someone adds a new attribute/property in the engine/app configuration, your configuration files will not see it anyway, and thus be 'sparse' unintentionally. This leaves you with unnecessarily verbose configuration that I dislike already.
* In order to obtain shot folders, one has to perform an action manually. What you want is to set the status of the shot to something indicating it can now be handled, and have the system create the paths for you.


## Tank - What’s good
* docs
* tk-core by now has a good test suite !
* TDs can reload code in-app.
* Provided the 'semantic configuration file names' feature is dynamic, configuration selection by context is something `bcore` doesn't do right now. This runtime feature could be implemented easily though, provided we have context information. Done in the 'pick_environment' hook - the equivalent would be done in a custom Application (for runtime changes) or a delegate for pre-runtime changes. The latter is more powerful as the entire program configuration can be adjusted properly.
* Context can dynamically change, see 'Work Files App', or 'pick_environment' hook
* yaml-configurable schemas. bapp could make that possible, after all it's just a KeyValueStoreSchema from settings
* path template validation. `bsemantic` does this in test-cases, but something similar must exist to make it failsafe/easy to use. To not be forced to put everything into yaml, the system could collect plugins that support a certain interface, and call their generators to see if a particular context can work.
* different 'pipeline configurations' allow to do sandboxes/local testing
* can be started from existing pipelines (which was expected)
* very declarative when it comes to what code requires to work, e.g. which environment code expects. In `bcore`, there is no such thing as code specific to a particular environment will have a package requirement to the needed package, will be a plugin that implements an interface. The latter is abstract.
* As required framework versions are specified per application, it's easy to have one application which prevents anything to come up. In `bcore`, this check is left to the code (and to the one writing configuration files) - but the code will only recognize the version issue when the applications is launched. Chances are that it isn't even called. However, `bcore` isn't able to determine if packages have incompatible requirements, in terms of the version they need.
* Automatic shotgun schema upgrades - engines or apps in need for a particular field will be sure to have it.
* at least environment variables can be used to specify hooks, `{$EVAR}/path/to/hook.py`. That will make customizations so much easier, considering bprocess will be used to set everything up.
* there is a 'dict' value type, which allows one level of nesting for values, effectively. But not more.
* tank has more meta-data for its schema's than the kvstore. The latter wants it that way, yet `bproperties` could be used to one day get more meta-data for schema values. After all GUIs will want to have that.
* deferred path creation is a good, as it will create directories only when the asset is actually worked on. My way of doing it would be to respond to particular changes though, so the directory and basesetup is created when the task is assigned or set to in-progress. Nonetheless, I see the point.
* template system can be used for paths and strings
* multi-root configuration is possible, and easy to configure, but verbose as everything.
* It's possible to centralize configuration while maintaining the ability to make overrides by using configuration includes
	- it's possible to use information from the context in these paths for substitution (similar to what seems to work in many places where paths are involved)

## Interesting - for evaluation
* Direct and deferred path creation (once in shotgun, once at app start ??)
* path inference (obtain fields from path)
* context keeps asset association/shotgun data link
* department/process related app configurations are determined as such, whereas `bcore` uses different wrapper configurations (which allow to do more, effectively, see package.include). It’s called *environment*
* core-> engines-> apps -> hooks
    * engines are application specific, and seem to be brought up by core
    * apps are engine plugins, hooks are app plugins
* app location configuration parameter should allow it to be local (but only so if kvstore resolution is used). Their configuration could in fact be coming from a kvstore, schemas will not overlap.
* core hooks allow to choose environments, or make fundamental business logic decisions (e.g. *PIPELINE_CONFIG/core/hooks/pick_environment.py*)
* tank does 'app' configuration at runtime (and makes them available), whereas bprocess is doing it before runtime. Both would combine well, so there might be no need to use bprocess for anything app related.
* 'shotgun_entitytype.yaml' environment file to configure in-browser RMB menus
* pipeline configurations are entities in shotgun, created by the API, pointing to the tank location on a per-project basis. This is where sandboxes are setup. They might support environment variables.
* `sg_connection` studio hook in config/core allows to return custom connection types ... oh actually it's adjusting the connection settings - crowed too soon.
* to me it looks like the template system and the 'path schema' in the project configuration are different things. One is used for general paths, the other is used for path templates.

## Goals at first glimpse
* Install it within the standard dependencies assembly, initially there might be no way around the redundant configuration issue. After all, tank must be able to find its manifest files.
* separate studio configuration from installation location, maybe just using symlinks
* Make it use kvstore (if configuration turns out to be too redundant, especially with paths)
* Make it use bsemantic
* use own sg connection implementation (from bshotgun)
* make it use bprocess when starting applications, especially the shotgun plugin to get browser support


## Configuration File Rampage

TODO: Write up about the mess