
To aid defining a course of action, it's best to state the problems showing after first evaluation, in order of their perceived gravity.

Solutions should be given in order of their ascending cost - let's try to find cheap solutions for heavy problems.



# Tank as part of an assembly

Tank is meant to be a standalone, and as self-contained as possible. Yet it should be port of an existing software repository and integrate with it. It's auto-update features and self-managing nature must be well understood to determine a good place and way of handling it.

**Solutions**

1.  Treat tank as self-managed unit and integrate it as a whole
    + All tank features for BUNDLE management are preserved, pulling on those that are required by a particular project configuration.The TANK_STUDIO location is tracked as a whole.
    - `tk-core` may exist only in one version for the entire studio, which may be a risk if not handled correctly.
    + requires no additional or special treatment, except for a few git commands.
2.  As 1., but track multiple `tk-core` installations
    - requires a tight bprocess override to work, as tk-core must be put in the path accordingly.
    - possibly requires dynamic adjustment of configuration files tank expects to read to work
    + Allows to choose any tank core version per project, and keeps them available forever in exactly that state.
        - This can also be achieved by localizing tank to the project once it's done
    - requires to maintain and possibly update apps in multiple tank installations
3.  Track tk-core and each BUNDLE as component in an assembly
    - makes all tank management features unusable, and probably requires overrides to make it still find it's BUNDLEs



# Studio and Project Configuration

The studio's configuration should be able to evolve from project to project, and should aid in maintaining and keeping all btank customizations. Fortunately, this is standard-fare, and tank uses git to maintain its standard configuration as a BUNDLE as well.

Project configurations must be derived from the studio configuration, and should be placed right where the project is for consistency, and accessibility. The latter is a somewhat arbitrary choice, but one I prefer for companies that don't have a strong technical background with trained personnel.

**Solutions**

1.  Maintain own configuration BUNDLE and use it when setting up new projects
    + fits perfectly into tanks design, and aligns with the intended use.
    + proven technique, used by tank itself
    + each project clone of the studio configuration is tracked and can be migrated back into the studio configuration using git in any way you can imaging
    + it's safe, and even though its most likely world-writable on the project share, git will always be able to show changes and handle them responsibly.

It makes no sense to think of anything else here, as it would be hacky and have more downsides.



# Process Launching

Tank's implementation is minimal and allows only for setting arguments and environment variables of the process in question. In practice, there is much more to it, such as:

* configure extensions and versions thereof to be used in the host applications, along with their dependencies, recursively
* Handle GUI launches differently from those in a high performance computing environment

**Solutions**

1.  Just specify the bprocess wrapper as program to be launched
    - Add's 3s on an smb share, on top of the 7s tank needs to do anything
    + simple
    - relocation not possible, as environment variables [aren't resolved](https://github.com/shotgunsoftware/tk-multi-launchapp/blob/master/app.py#L194) in the path. Therefore, an absolute paths will have to be specified.
2.  Adjust phase 2 bootstrapper to launch bprocess wrapper for tank itself
    + it's possible to create an 'evolutionary' configuration and adjust the `after_project_create.py` callback (erm, hook), which has enough information to post-process the phase 1 or phase 2 bootstrappers. This would fit well, as tank supports choosing any git-controlled configuration - `btank` could just provide it's own.
    + Full control over environment variables and the tank startup process, which would allow to intercept launch requests entirely and would allow to speed up launching considerable. This is because I think the information tank wants within the host application can easily be obtained under 0.5s, which adds to the 3s the bprocess wrapper needs on a slow SMB share.
    + Tank would become (more) relocatable, as we control the contents of args (`--pc=PATH`) and environment variables (`TANK_CURRENT_PC`). However, it's unclear to what extend the contents of the various other path containing files are affecting it. For some reason I am optimistic about this though.

# Process Launching with Deadline

Deadline is a nice example of an epic fail, considering that it can't execute a script thanks to its .NET (and `mono`) roots. IronPython can't just execute something using built-in kernel functionality, but uses .NET to do it. The latter will only allow, as common on windows, 'real' executables. Therefore, a script that executes just fine with `subprocess.Popen(shell=False)` will not work when started from IronPython.

**Solutions**

1.  Use cxfreeze to create a real bootstrapper executable.
    + `cxfreeze -s --include-modules=__future__,imp,glob,shutil,platform,getpass,cProfile,json,logging.config,urllib2,uuid,distutils.version,sqlite3,code <bootstrapper>`
        - every module from and including `urllib2` is what was required by tank to come up, which in turn is done by the tank specific delegate the bootstrapper should be using (see `btank-plugins/bprocess-delegates.py`)

# Templates and Folder Creation

Tank comes with a system that requires to specify rules in a very verbose and repetitive fashion. There are two systems to maintain, the template system for paths and names, as well as the folder creation system (schema). They are likely to go out of sync at some point, facilitating undefined behavior.

**Solutions**

1.  Use bsemantic-style grammar, and build the folder schema and templates.yml from that
    + one file for specifying everything (either yaml or .py, depending on the desired declaration language). It's really just a more concise description language, without actually using features of bsemantic.
    + Support for tank features bsemantic doesn't have, as arbitrary meta-data can be inserted for use in the generated schema/templates.yml.
    - needs a custom commandline tool and library to implement the transformation, and tank support to figure out which templates actually need to be define in the end. It needs to verify the generated configuration is sufficient.
    + tank is guaranteed to work with it, once verified.
2.  Use bsemantic to specify grammar, and enforce it's use at runtime
    - requires to either change tank code, or heavily monkey-patch it.
    - depending on the amount of required changes, these are likely to break when tk-core changes, or fail subtly which is hard to debug.



# Automation of Common Processes

As tank can't rely on much more infrastructure than python, shotgun, and a storage location, automation can't be it's strong shoe. When looking at some design decisions of important 'apps', like the publisher, it's clear that automation wasn't considered very much.

Nonetheless, it's important to be able to increase tanks usability to allow companies to use shotgun as a front-end for most important operations, which trigger processes that would otherwise be done by IT or other technical personnel.

**Solutions**

1.  Use shotgun-events to react to database changes
    + The shotgun database is something every tank user is guaranteed to have access to, using is a critical part of his workflow.
    - shotgun-events needs a daemon that has to run somewhere - IT support is required for initial setup. After that, it should be maintenance free, except when its own code changes.
    + Plugins can be used to react to any event you can imagine, and customize the experience according to the customers wishes and workflows. These are as simple as creating projects automatically when they leave bidding phase. Plugins need to be very configurable, to allow easy adjustments to different customers.
    - some tank specific operations, like create project, still need research to assure it can be created without user interaction.

I see no other way than using shotgun-events. However, it was proven to be a very well working one.



# Shotgun and Tank are slow due to high round-trip times

For some reason, shotgun-software doesn't think non-US clients deserve their own servers. They are currently hosting everything from the us, leading to request round-trip times of 250ms or more. This makes tank's interaction with shotgun very slow, which is not only annoying, but actively burns money.

This holds true only for instances _not_ hosted in-house, which at the time of writing too expensive for average size facilities.

**Solutions**

1.  Read-fast-write-slow shotgun connection
    + maintain an exact copy of all data within shotgun in an in-house caching database. Reads stay in-house, writes always go to shotgun and to the in-house database.
        - if writes to shotgun fail, the write to the in-house database either has to be reverted, or replayed to shotgun when it is available once again.
        - it will be difficult to speed up all queries, as they might be too complex to exactly simulate results in shotgun. Therefore, only trivial queries of single entities should be considered, which will not speed up all code.
    - a custom implementation of a shotgun connection needs to be used to enabled this functionality. For use in tank, some monkey-patching or overrides will be required. There seems to be no simple way to override a shotgun connection.
        + With wrapper support in bootstrapper phase 1 or 2 (see _Process Launching_), it should be relatively easy to enforce a custom shotgun connection through a custom/overridden tank core implementation.
    - Will need a shotgun-events plugin to record all changes, and write latest data into the in-house caching.
    - Doesn't work for anything not using a shotgun connection, like queries of thumbnails and other imagery. These are done using simple http-gets, which might be harder to intercept and cache. Tank applications maintain their own cache for that reason, so that should be less of an issue.



# High risk of failure due to reliance on internet

Shotgun software performs maintenance regularly at night, which is likely to be well within other people's work time. Even if not, there will always be a render farm that can't get information all of the sudden.

**Solutions**

1.  For User Interaction, use in-house caching database
    - Similar to the 'Read-fast-write-slow shotgun connection', with all benefits and disadvantages. It might just not catch enough queries to make all code work without a real shotgun connection.
    - requires a lot of testing to verify most fundamental workflows, like opening a scene file, still work.
    - in-house caching database might support a 'write-cache', which replays all changes to shotgun when it becomes available. Implementing this reliably seems difficult.
2.  For non-user interaction, don't rely on shotgun at all
    + Whenever something is sent to the farm, provide enough information to know what todo.
    + Write code that doesn't rely on shotgun/tank at all for these operations.
    + Writes to shotgun (directly or using the tank API) should be expected to fail. Handle failures gracefully, ideally transparently by the used shotgun connection, or explicitly. Worst case the files are there, but nobody knows about it. Best case the information about them will be replayed to shotgun when it's back.



# tank-configuration enforces duplication and verbosity, and is generally less powerful than the `bkvstore`

Configuring tank is a drag, and it's terrible to see that even default values have to be specified as such thanks to the 'non-sparse configuration' paradigm. Everything has to be repeated per 'environment', and even in the default configuration, 'tk-config-default', there are more than 10 yaml files with lot's of similar contents. tanks means of reducing redundancy are an afterthought and don't help as much as they should.

The `bkvstore` is capable of keeping all tank configuration, and in the same schema as tank requires it. Tank just has to use it.

**Solutions**

1.  Generate tank environment configuration from `bkvstore` configuration
    + All tank-related configuration can be placed into the `bkvstore`, setting overrides per environment in a manner that allows more efficient specification of values. Traverse the `bkvstore` configuration and generate properly formatted environment configuration for tank to use.
    + no runtime overrides necessary, validation is possible before using the generated configuration, at least to some extend, by tank itself.
    + (plays well with the similar solution for handling schema and templates.yml)

2.  Override tank's standard implementation at runtime
    - Tank has various configuration files, and some of them are accessed very directly, using code copied around in various places. Monkey-patching and overriding the implementation will be very difficult. A first step would be to deduplicate tanks code and to be sure configuration access is unified. Then one could override the respective API and make sure the own implementation is used.
    - This is very difficult to achieve, and it might be easier to re-implement the tank API entirely to support their applications, frameworks and engines. After all, this might just not be worth it.

