# Imagr Config Creator (CLI)

This interactive script will generate or edit a [workflow plist](https://github.com/grahamgilbert/imagr/wiki/Workflow-Config) for [Imagr](https://github.com/grahamgilbert/imagr).

## Usage

The only command line argument *must* be a path to a plist file. If no plist exists at that location, it will create one (and fail if it can't write to it).

```bash
./config_creator.py /Users/nmcspadden/Desktop/imagr_config.plist
```

```
nmcspadden$ ./config_creator.py imagr_config.plist 
Entering interactive mode... (type "help" for commands)
> help
Available sub-commands:
	add-computername-component
	add-image-component
	add-package-component
	add-script-component
	add-workflow
	display-components
	display-workflows
	exit
	help
	new-password
	remove-component
	remove-workflow
	set-bless-target
	set-description
	set-restart-action
	show-password
	show-workflow
> 
```

### Command list:

Arguments in [brackets] are optional.

For more information on what these arguments represent, consult the [Imagr documentation](https://github.com/grahamgilbert/imagr/wiki/Workflow-Config).

`exit` - **Changes are only saved when you exit. Ctrl-C or Ctrl-D will NOT save the plist.**

Password related:  

* `show-password` - shows the existing password hash.
* `new-password <password>` - sets the password to the hash of "password".

Workflow related:

* `display-workflows` - displays an indexed list of all workflows found in the plist.
* `show-workflow <name or index>` - displays the contents of a workflow by "name" or at "index".  If the name contains spaces, it must be quoted - i.e. 'My Workflow'.
* `add-workflow <name> [<index>]` - adds a new workflow with "name" to the list at 'index' location. If no index is specified, the workflow is added to the end of the list.
* `remove-workflow <name or index>` - deletes the workflow from the list by "name" or at "index".

Per-Workflow settings related:

* `set-restart-action <name or index> <action>` - sets the RestartAction for a workflow by "name" or at "index" to "action". "action" must be either `restart`, `shutdown`, or `none`. If "action" is not specified, `none` is chosen by default. By default, this is `none`.
* `set-bless-target <name or index> <true/false>` - sets the Bless_Target for a workflow by "name" or at "index" to "True" or "False". Values of True are `true`, `True`, `t`, `yes`, or `1`. Anything else is False. By default, this is False.
* `set-description <name or index> <description>` - sets the Description for a workflow by "name" or at "index" to "Description". "Description" should be quoted. By default, this is blank.

Component related:

* `display-components <name or index>` - displays the list of components for a workflow by "name" or at "index".
* `remove-component <name or index> <component index>` - removes a component from the list at "component index" for a workflow by "name" or at "index".
* `add-image-component <name or index> <url> [<component index>]` - adds an Image task to the component list at "component index" for a workflow by "name" or at "index". If "component index" is not specified, task is added to the end of the component list. "URL" should be a URL.
* `add-package-component <name or index> <url> <first boot true/false> [<component index>]` - adds a Package task to the component list at "component index" for a workflow by "name" or at "index". "URL" should be a URL. "First Boot" values of True are `true`, `True`, `t`, `yes`, or `1`. Anything else is False. If "component index" is not specified, task is added to the end of the component list. 
* `add-computername-component <name or index> <use serial true/false> <auto true/false> [<component index>]` - adds a ComputerName task to the component list at "component index" for a workflow by "name" or at "index". "Use Serial" and "auto" values of True are `true`, `True`, `t`, `yes`, or `1`. Anything else is False. If "component index" is not specified, task is added to the end of the component list. 
* `add-script-component <name or index> <path to script> <first boot true/false> [<component index>]` - adds a Script task to the component list at "component index" for a workflow by "name" or at "index". "Path" should be a valid path to a script that will be parsed and added to the plist. "First Boot" values of True are `true`, `True`, `t`, `yes`, or `1`. Anything else is False. If "component index" is not specified, task is added to the end of the component list. 

