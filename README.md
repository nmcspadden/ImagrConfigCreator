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

For more information on what these arguments represent, consult the [Imagr documentation](https://github.com/grahamgilbert/imagr/wiki/Workflow-Config).

`exit` - **Changes are only saved when you exit. Ctrl-C or Ctrl-D will NOT save the plist.**

Password related:  

* `show-password` - shows the existing password hash.
* `new-password PASSWORD` - sets the password to the hash of "PASSWORD".

Workflow related:

* `display-workflows` - displays an indexed list of all workflows found in the plist.
* `show-workflow NAME OR INDEX` - displays the contents of a workflow by "name" or at "index".  If the name contains spaces, it must be quoted - i.e. 'My Workflow'.
* `add-workflow NAME --index INDEX` - adds a new workflow with "name" to the list at 'index' location. If no index is specified, the workflow is added to the end of the list.
* `remove-workflow NAME OR INDEX` - deletes the workflow from the list by "name" or at "index".

Per-Workflow settings related:

* `set-restart-action --workflow NAME OR INDEX --restart ACTION` - sets the RestartAction for a workflow by "name" or at "index" to "action". "action" must be either `restart`, `shutdown`, or `none`. If "action" is not specified, `none` is chosen by default. By default, this is `none`.
* `set-bless-target --workflow NAME OR INDEX --no-bless` - sets the Bless_Target for a workflow by "name" or at "index" to "False". By default, the bless_target option for a workflow is True.
* `set-description --workflow NAME OR INDEX --desc DESCRIPTION` - sets the Description for a workflow by "name" or at "index" to "Description". "Description" should be quoted. By default, this is blank.

Component related:

* `display-components NAME OR INDEX` - displays the list of components for a workflow by "name" or at "index".
* `remove-component --workflow NAME OR INDEX --component INDEX` - removes a component from the list at index "component" for a workflow by "name" or at "index".
* `add-image-component --workflow NAME OR INDEX --url URL --index INDEX` - adds an Image task to the component list at "index" for a workflow by "name" or at "index". If "index" is not specified, task is added to the end of the component list. "URL" should be a URL. Only one image task is allowed per workflow.
* `add-package-component --workflow NAME OR INDEX --url URL --no-firstboot --index INDEX` - adds a Package task to the component list at "component index" for a workflow by "name" or at "index". "URL" should be a URL. By default, this package will be installed at first boot, unless "--no-firstboot" is specified. If "component index" is not specified, task is added to the end of the component list. 
* `add-computername-component --workflow NAME OR INDEX --use-serial --auto --index INDEX` - adds a ComputerName task to the component list at "component index" for a workflow by "name" or at "index". If "use-serial" is specified, the serial number will be the default computer name choice. If "auto" is specified, the serial number will be forced as the computer name and not allow overriding. If "component index" is not specified, task is added to the end of the component list. 
* `add-script-component --workflow NAME OR INDEX --content CONTENT --no-firstboot --index INDEX` - adds a Script task to the component list at "component index" for a workflow by "name" or at "index". "CONTENT" should be a valid path to a script that will be parsed and added to the plist. By default, this package will be installed at first boot, unless "--no-firstboot" is specified. If "component index" is not specified, task is added to the end of the component list. 

## Examples

```
$ ./config_creator.py new_imagr_config.plist
Entering interactive mode... (type "help" for commands)
> add-workflow 'First Image'
Workflow 'First Image':
{'bless_target': False,
 'components': [],
 'description': '',
 'name': 'First Image',
 'restart_action': 'none'}
> add-image-component --workflow 'First Image' --url 'http://server/image.dmg'
Workflow 'First Image':
{'bless_target': False,
 'components': [{'type': 'image', 'url': 'http://server/image.dmg'}],
 'description': '',
 'name': 'First Image',
 'restart_action': 'none'}
> add-package-component --workflow 'First Image' --url 'http://server/munki.pkg' 
Workflow 'First Image':
{'bless_target': False,
 'components': [{'type': 'image', 'url': 'http://server/image.dmg'},
                {'first_boot': True,
                 'type': 'package',
                 'url': 'http://server/munki.pkg'}],
 'description': '',
 'name': 'First Image',
 'restart_action': 'none'}
> add-script-component --workflow 'First Image' --content 'test_postinstall_script.sh' --no-firstboot
Workflow 'First Image':
{'bless_target': False,
 'components': [{'type': 'image', 'url': 'http://server/image.dmg'},
                {'first_boot': True,
                 'type': 'package',
                 'url': 'http://server/munki.pkg'},
                {'content': '#!/bin/bash\necho "<"\necho "{{target_volume}}"\n/usr/bin/touch "{{target_volume}}/some_file"',
                 'first_boot': False,
                 'type': 'script'}],
 'description': '',
 'name': 'First Image',
 'restart_action': 'none'}
> exit

```

Resulting plist:
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>password</key>
	<string></string>
	<key>workflows</key>
	<array>
		<dict>
			<key>bless_target</key>
			<false/>
			<key>components</key>
			<array>
				<dict>
					<key>type</key>
					<string>image</string>
					<key>url</key>
					<string>http://server/image.dmg</string>
				</dict>
				<dict>
					<key>first_boot</key>
					<true/>
					<key>type</key>
					<string>package</string>
					<key>url</key>
					<string>http://server/munki.pkg</string>
				</dict>
				<dict>
					<key>content</key>
					<string>#!/bin/bash
echo "&lt;"
echo "{{target_volume}}"
/usr/bin/touch "{{target_volume}}/some_file"</string>
					<key>first_boot</key>
					<false/>
					<key>type</key>
					<string>script</string>
				</dict>
			</array>
			<key>description</key>
			<string></string>
			<key>name</key>
			<string>First Image</string>
			<key>restart_action</key>
			<string>none</string>
		</dict>
	</array>
</dict>
</plist>
```