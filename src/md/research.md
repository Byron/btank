## Tank - What’s bad

* Upgrade config files on schema change
    - Even though I think there should be viable defaults, this is not always possible. Generally one should refrain from introducing changes that break an application if a piece of information doesn't exist. Instead, the application should deal with it. It's good to have a facility that can handle these updates though.
* Redundant per entity type configuration (aka environments)
    - This seems like a workaround to a 'single-file' configuration system paradigm.
* Tk-core is special, and typically shared
* path - asset association is stored in a shared sqlite database (known for inconsistency on network shares)
* path template system configuration is redundant, and inflexible (proof)
* path inference needs to know the ‘type’ of path you look at
* capitalisation in dict keys [fields] for path template system (used to differentiate shotgun entity types [context fields] from custom template fields manipulated by apps)

## Tank - What’s good
* docs
* versions in yaml have ‘v’ prefix to make sure they become string, not float, even without quoting them
* tk-core by now has a good test suite !

## Interesting - for evaluation
* Direct and deferred path creation (once in shotgun, once at app start ??)
* path inference (obtain fields from path)
* context keeps asset association/shotgun data link
* department/process related app configurations are determined as such, whereas bcore uses different wrapper configurations (which allow to do more, effectively, see package.include). It’s called *environment*
* core-> engines-> apps -> hooks
    * engines are application specific, and seem to be brought up by core
    * apps are engine plugins, hooks are app plugins
* app location configuration parameter should allow it to be local (but only so if kvstore resolution is used). Their configuration could in fact be coming from a kvstore, schemas will not overlap.
* core hooks allow to choose environments, or make fundamental business logic decisions (e.g. *PIPELINE_CONFIG/core/hooks/pick_environment.py*)

## Goals at first glimpse
* Make it use kvstore
* Make it us bsemantic
* use own sg connection implementation (from bshotgun)
* make it use bprocess when starting applications, especially the shotgun plugin to get browser support