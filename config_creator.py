#!/usr/bin/python

import subprocess
import sys
import os
import hashlib
import pprint
import argparse
import readline
import shlex
import fnmatch
import copy

#try:
#    import FoundationPlist as plistlib
#except ImportError:
#    import plistlib
import FoundationPlist as plistlib


# Imagr Config Plist class

class ImagrConfigPlist():
    workflowComponentTypes = {  'image' : {'url':'http'}, 
                                'package' : { 'url' : 'http', 'first_boot' : True },
                                'computername' : { 'use_serial' : False, 'auto' : False },
                                'script' : { 'content' : '#!/bin/bash', 'first_boot' : True },
                                'eraseVolume' : { 'name' : 'Macintosh HD', 'format' : 'Journaled HFS+' },
                                'partition' : { 'map' : 'GPTFormat', 'partitions' : [ { 'format_type' : 'Journaled HFS+', 'name' : 'Macintosh HD', 'size' : '100%', 'target' : True } ] }
                             }
    
    def __init__(self, path):
        if os.path.exists(path):
            self.internalPlist = plistlib.readPlist(path)
        else:
            self.internalPlist = { 'password':'', 'workflows':[] }
        self.plistPath = path
    
    def synchronize(self):
        """Writes the current plist to disk"""
        plistlib.writePlist(self.internalPlist, self.plistPath)
    
    def findWorkflowIndexByName(self, name):
        """Return the workflow index that matches a given name"""
        index = 0
        for workflow in self.internalPlist.get('workflows'):
            if workflow.get('name') == name:
                return index
            index += 1
    
    def findWorkflowNameByIndex(self, index):
        """Return the workflow name that matches a given index"""
        return self.internalPlist['workflows'][index]['name']

    def replaceWorkflowByName(self, newWorkflow, name):
        """Replace the workflow (dict) that matches a given name with new workflow"""
        for workflow in self.internalPlist.get('workflows'):
            if workflow.get('name') == name:
                workflow = newWorkflow
    
    # Workflow-related functions that are not subcommands    
    def getWorkflowComponentTypes(self):
        """Returns a list of possible workflowComponentTypes"""
        return self.workflowComponentTypes.keys()
    
    def getWorkflowNames(self):
        """Returns a list of names of workflows in the plist"""
        nameList = list()
        for workflow in self.internalPlist['workflows']:
            nameList.append(str(workflow['name']))
        return nameList
    
    # Workflow subcommands
    def display_workflows(self, args):
        """Displays a pretty-print list of workflows"""
        #args is basically ignored
        if len(args) != 0:
            print >> sys.stderr, 'Usage: display-workflows'
            return 22 # Invalid argument
        workflows = list()
        for workflow in self.internalPlist.get('workflows'):
            workflows.append(workflow)
        for i, elem in enumerate(self.internalPlist['workflows']):
            print '\n{0}:\n{1}'.format(i, elem)
        return 0
    
    def add_workflow(self, args):
        """Adds a new workflow to the list of workflows at index. Index defaults to end of workflow list"""
        p = argparse.ArgumentParser(prog='add-workflow', 
                                    description='''add-workflow NAME --index INDEX
            Adds a new workflow with NAME to workflow list. If INDEX is specified,
            workflow is added at that INDEX, otherwise added to end of list.''')
        p.add_argument('name',
                    metavar='NAME',
                    help='''quoted name of new workflow''')
        p.add_argument('--index',
                    metavar='INDEX',
                    help='''where in the component list the task will go - defaults to end of list''',
                    default = False)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        # validate that the name isn't being reused
        for tempworkflow in self.internalPlist.get('workflows'):
            if tempworkflow['name'] == arguments.name:
                print >> sys.stderr, 'Error: name is already in use. Workflow names must be unique.'
                return 22
        if arguments.index == False: #this means one wasn't specified
            index = len(self.internalPlist['workflows'])
        else:
            index = int(arguments.index)
        workflow = dict()
        workflow['name'] = arguments.name
        workflow['description'] = ''
        workflow['restart_action'] = 'none'
        workflow['bless_target'] = False
        workflow['components'] = list()
        self.internalPlist['workflows'].insert(index, workflow)
        self.show_workflow(args)
        return 0
    
    def remove_workflow(self, args):
        """Removes workflow with given name or index from list"""
        p = argparse.ArgumentParser(prog='remove-workflow', 
                                    description='''remove-workflow WORKFLOW NAME OR INDEX
            Removes workflow WORKFLOW from workflow list.''')
        p.add_argument('workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    )
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
        try:
            del self.internalPlist['workflows'][key]
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        print "Removed workflow '%s' from list." % arguments.workflow
        print "Remaining workflows:"
        pprint.pprint(self.getWorkflowNames())
        return 0
    
    def show_workflow(self, args):
        """Shows a workflow with a given name or index"""
        p = argparse.ArgumentParser(prog='show-workflow', 
                                    description='''show-workflow WORKFLOW NAME OR INDEX
            Displays the contents of WORKFLOW.''')
        p.add_argument('workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    )
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
        try:
            print "Workflow '%s':" % arguments.workflow
            pprint.pprint(self.internalPlist['workflows'][key])
        except (IndexError, TypeError):
            # If it gets here, no workflow by that name or index was found.
            print >> sys.stderr, 'No workflow found at %s: ' % arguments.workflow
            return 22
        return 0
    
    # Password subcommands
    def show_password(self, args):
        """Returns the password hash"""
        #args is basically ignored
        if len(args) != 0:
            print >> sys.stderr, 'Usage: show-password'
            return 22 # Invalid argument
        print self.internalPlist.get('password')
        return 0
    
    def new_password(self, args):
        """Sets a new password"""
        p = argparse.ArgumentParser(prog='new-password', 
                                    description='''new-password PASSWORD
            Sets a new PASSWORD to configuration plist.''')
        p.add_argument('password',
                    metavar='PASSWORD',
                    help='''new password''')
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        self.internalPlist['password'] = hashlib.sha512(str(arguments.password)).hexdigest()
        self.show_password([])
        return 0
    
    # RestartAction subcommands
    def set_restart_action(self, args):
        """Sets a restart action for the given workflow"""
        p = argparse.ArgumentParser(prog='set-restart-action', 
                                    description='''set-restart-action --workflow WORKFLOW --restart RESTART
            Sets a restart action for WORKFLOW to RESTART. If --restart is not specified, it defaults to \'none\'.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--restart',
                    metavar='RESTART',
                    help='''restart action to use: restart, shutdown, or none''',
                    choices=['restart', 'shutdown', 'none'],
                    default = 'none')
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            self.internalPlist['workflows'][key]['restart_action'] = arguments.restart
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0
    
    # Bless subcommands
    def set_bless_target(self, args):
        """Sets bless to True or False for the given workflow"""
        p = argparse.ArgumentParser(prog='set-bless-target', 
                                    description='''set-bless-target --workflow WORKFLOW --no-bless
            Sets the bless_target option for WORKFLOW to False. By default, bless is true.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--no-bless',
                    help='''sets bless_target value to False''',
                    action='store_false')
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            self.internalPlist['workflows'][key]['bless_target'] = arguments.no_bless
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0
    
    # Description subcommands
    def set_description(self, args):
        """Sets description for the given workflow"""
        p = argparse.ArgumentParser(prog='set-description', 
                                    description='''set-description --workflow WORKFLOW --desc DESCRIPTION
            Sets the description for WORKFLOW to DESCRIPTION.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--desc',
                    metavar='DESCRIPTION',
                    help='''description for workflow''',
                    required = True)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            self.internalPlist['workflows'][key]['description'] = arguments.desc
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0
    
    # Component subcommands
    def display_components(self, args):
        """Displays a list of components for a given workflow"""
        p = argparse.ArgumentParser(prog='display-components', 
                                    description='''display-components WORKFLOW NAME OR INDEX
            Displays the components of WORKFLOW.''')
        p.add_argument('workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    )
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
        try:
            for i, elem in enumerate(self.internalPlist['workflows'][key]['components']):
                print '{0}: {1}'.format(i, elem)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        return 0
    
    def remove_component(self, args):
        """Removes a component at index from workflow"""
        p = argparse.ArgumentParser(prog='remove-component', 
                                    description='''remove-component --workflow WORKFLOW NAME OR INDEX --component INDEX
            Remove the component at INDEX from WORKFLOW.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required=True)
        p.add_argument('--component',
                    metavar='INDEX',
                    help='''index of component from list''',
                    type=int,
                    required=True)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
        try:
            del self.internalPlist['workflows'][key]['components'][arguments.component]
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        return 0
    
    def add_image_component(self, args):
        """Adds an Image task at index with URL for a workflow. If no index is specified, defaults to end"""
        p = argparse.ArgumentParser(prog='add-image-component', 
                                    description='''add-image-component --workflow WORKFLOW --url URL --index INDEX
            Adds an Image task to the component list of the WORKFLOW from URL. If INDEX is specified,
            task is added at that INDEX, otherwise added to end of list.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--url',
                    metavar='URL',
                    help='''URL of image to apply''',
                    required = True)
        p.add_argument('--index',
                    metavar='INDEX',
                    help='''where in the component list the task will go - defaults to end of list''',
                    default = False)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        imageComponent = self.workflowComponentTypes['image'].copy()
        imageComponent['url'] = arguments.url
        imageComponent['type'] = 'image'
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            if arguments.index == False: #this means one wasn't specified
                index = len(self.internalPlist['workflows'][key]['components'])
            else:
                index = int(arguments.index)
            # Check here to make sure we only have one image component per workflow
            for component in self.internalPlist['workflows'][key]['components']:
                if component.get('type') == 'image':
                    print >> sys.stderr, 'Error: only one image task allowed per workflow.'
                    return 21
            self.internalPlist['workflows'][key]['components'].insert(index, imageComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0
    
    def add_package_component(self, args):
        """Adds a Package task at index with URL, first_boot for workflow"""
        p = argparse.ArgumentParser(prog='add-package-component',
                                    description='''add-package-component --workflow WORKFLOW --url URL --no-firstboot --index INDEX
            Adds a Package task to the component list of the WORKFLOW from URL at first boot. If --no-firstboot is specified, the package is installed 'live' instead.
            If INDEX is specified, task is added at that INDEX, otherwise added to end of list.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--url',
                    metavar='URL',
                    help='''URL of image to apply''',
                    required = True)
        p.add_argument('--no-firstboot',
                    help='''sets first_boot value for package to False''',
                    action='store_false')
        p.add_argument('--index',
                    metavar='INDEX',
                    help='''where in the component list the task will go - defaults to end of list''',
                    default = False)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        packageComponent = self.workflowComponentTypes['package'].copy()
        packageComponent['url'] = arguments.url
        packageComponent['first_boot'] = arguments.no_firstboot
        packageComponent['type'] = 'package'
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            if arguments.index == False: #this means one wasn't specified
                index = len(self.internalPlist['workflows'][key]['components'])
            else:
                index = int(arguments.index)
            self.internalPlist['workflows'][key]['components'].insert(index, packageComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0
    
    def add_computername_component(self, args):
        """Adds a ComputerName task at index with use_serial and auto for workflow"""
        p = argparse.ArgumentParser(prog='add-computername-component',
                                    description='''add-computername-component --workflow WORKFLOW --use-serial --auto --index INDEX
            Adds a ComputerName task to the component list of the WORKFLOW. If --user-serial is specified, the computer's serial number is chosen as default.
            If --auto is specified, the computer's serial number will be used and not allow overriding.
            If INDEX is specified, task is added at that INDEX, otherwise added to end of list.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--use-serial',
                    help='''use the computer's serial number as the default name''',
                    action='store_true')
        p.add_argument('--auto',
                    help='''enforce using the computer's serial number as the default name''',
                    action='store_true')
        p.add_argument('--index',
                    metavar='INDEX',
                    help='''where in the component list the task will go - defaults to end of list''',
                    default = False)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        computerNameComponent = self.workflowComponentTypes['computername'].copy()
        computerNameComponent['use_serial'] = arguments.use_serial
        computerNameComponent['auto'] = arguments.auto
        computerNameComponent['type'] = 'computer_name'
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            if arguments.index == False: #this means one wasn't specified
                index = len(self.internalPlist['workflows'][key]['components'])
            else:
                index = int(arguments.index)
            self.internalPlist['workflows'][key]['components'].insert(index, computerNameComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0
    
    def add_script_component(self, args):
        """Adds a Script component at index with content for workflow"""
        p = argparse.ArgumentParser(prog='add-script-component',
                                    description='''add-script-component --workflow WORKFLOW --content CONTENT --no-firstboot --index INDEX
            Adds a Script task to the component list of the WORKFLOW at first boot. CONTENT must be a path to a file.
            If --no-firstboot is specified, the package is installed 'live' instead of at first boot.
            If INDEX is specified, task is added at that INDEX, otherwise added to end of list.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--content',
                    metavar='CONTENT',
                    help='''path to a file containing a script''',
                    required = True)
        p.add_argument('--no-firstboot',
                    help='''sets first_boot value for package to False''',
                    action='store_false')
        p.add_argument('--index',
                    metavar='INDEX',
                    help='''where in the component list the task will go - defaults to end of list''',
                    default = False)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        try:
            fileobject = open(os.path.expanduser(arguments.content), mode='r', buffering=1)
            data = fileobject.read()
            fileobject.close()
        except (OSError, IOError):
            print >> sys.stderr, "Error: Couldn't read %s" % arguments.content
            return 22 #Invalid argument
        scriptComponent['content'] = data
        scriptComponent['first_boot'] = arguments.no_firstboot
        scriptComponent['type'] = 'script'
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            if arguments.index == False: #this means one wasn't specified
                index = len(self.internalPlist['workflows'][key]['components'])
            else:
                index = int(arguments.index)
            self.internalPlist['workflows'][key]['components'].insert(index, scriptComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0

    def add_erase_component(self, args):
        """Adds an eraseVolume component at index with content for workflow"""
        p = argparse.ArgumentParser(prog='add-erase-component',
                                    description='''add-erase-component --workflow WORKFLOW --name NAME --format FORMAT --index INDEX
            Adds an eraseVolume task to the component list of the WORKFLOW. 
            NAME is the name of the newly formatted volume. Defaults to "Macintosh HD".
            FORMAT is the format of the volume. Defaults to "Journaled HFS+".
            If INDEX is specified, task is added at that INDEX, otherwise added to end of list.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--name',
                    metavar='NAME',
                    help='''name of volume - defaults to "Macintosh HD"''',
                    default = 'Macintosh HD')
        p.add_argument('--format',
                    metavar='FORMAT',
                    help='''format of volume - defaults to "Journaled HFS+"''',
                    default = 'Journaled HFS+')
        p.add_argument('--index',
                    metavar='INDEX',
                    help='''where in the component list the task will go - defaults to end of list''',
                    default = False)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        eraseComponent = self.workflowComponentTypes['eraseVolume'].copy()
        eraseComponent['name'] = arguments.name
        eraseComponent['format'] = arguments.format
        eraseComponent['type'] = 'eraseVolume'
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            if arguments.index == False: #this means one wasn't specified
                index = len(self.internalPlist['workflows'][key]['components'])
            else:
                index = int(arguments.index)
            self.internalPlist['workflows'][key]['components'].insert(index, eraseComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0

    def add_partition_component(self, args):
        """Adds a Partition component at index with content for workflow"""
        p = argparse.ArgumentParser(prog='add-erase-component',
                                    description='''add-partition-component --workflow WORKFLOW --map MAP --names NAMES --formats FORMATS --sizes SIZES --target NAME --index INDEX
            Adds a Partition task to the component list of the WORKFLOW. 
            MAP is the partition map of the disk. Defaults to "GPTFormat" (GUID).
            NAMES, FORMATS, and SIZES are lists of volumes to create, in order, with specific names, formats, and sizes.
            If INDEX is specified, task is added at that INDEX, otherwise added to end of list.''')
        p.add_argument('--workflow',
                    metavar='WORKFLOW NAME OR INDEX',
                    help='''quoted name or index number of target workflow''',
                    choices=self.getWorkflowNames() + [str(s) for s in range(len(self.internalPlist['workflows']))],
                    required = True)
        p.add_argument('--map',
                    metavar='MAP',
                    help='''partition map of disk - defaults to "GPTFormat"''',
                    default = 'GPTFormat')
        p.add_argument('--names',
                    metavar='NAMES',
                    nargs = '+',
                    help='''names of volumes to create, in order''',
                    required = True)
        p.add_argument('--formats',
                    metavar='FORMATS',
                    nargs = '+',
                    help='''formats of volumes to create, in order''',
                    required = True)
        p.add_argument('--sizes',
                    metavar='SIZES',
                    nargs = '+',
                    help='''sizes of volumes to create, in order''',
                    required = True)
        p.add_argument('--target',
                    metavar='NAME',
                    help='''this volume will be set as the target for future actions in the workflow''',
                    required = True)
        p.add_argument('--index',
                    metavar='INDEX',
                    help='''where in the component list the task will go - defaults to end of list''',
                    default = False)
        try:
            arguments = p.parse_args(args)
        except argparse.ArgumentError, errmsg:
            print >> sys.stderr, str(errmsg)
            return 22 # Invalid argument
        except SystemExit:
            return 22
        partitionComponent = self.workflowComponentTypes['partition'].copy()
        partitionComponent['map'] = arguments.map
        partitionComponent['type'] = 'partition'
        partitionList = list()
        thePartition = dict()
        print "IT BEGINS"
        print "Names: %s" % arguments.names
        print "Formats: %s" % arguments.formats
        print "Sizes: %s" % arguments.sizes
        for i in range(0,len(arguments.names)):
            print "Starting %s" % i
            thePartition = dict()
            thePartition['name'] = arguments.names[i]
            thePartition['format_type'] = arguments.formats[i]
            thePartition['size'] = arguments.sizes[i]
            print "Current partition: %s" % thePartition
            partitionList.append(thePartition)
            print "Partition list: %s" % partitionList
        partitionComponent['partitions'] = partitionList
        try:
            key = int(arguments.workflow)
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(arguments.workflow)
            name = [ arguments.workflow ]
        try:
            if arguments.index == False: #this means one wasn't specified
                index = len(self.internalPlist['workflows'][key]['components'])
            else:
                index = int(arguments.index)
            self.internalPlist['workflows'][key]['components'].insert(index, partitionComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % arguments.workflow
            return 22
        self.show_workflow(name)
        return 0


# Generic helper functions for autocomplete, stolen from Munki manifestutil

def tab_completer(text, state):
    """Called by the readline lib to calculate possible completions"""
    array_to_match = None
    if readline.get_begidx() == 0:
        # since we are at the start of the line
        # we are matching commands
        array_to_match = 'cmds'
        match_list = CMD_ARG_DICT.get('cmds', {}).keys()
    else:
        # we are matching args
        cmd_line = readline.get_line_buffer()[0:readline.get_begidx()]
        cmd = shlex.split(cmd_line)[-1]
        array_to_match = CMD_ARG_DICT.get('cmds', {}).get(cmd)
        if array_to_match:
            match_list = CMD_ARG_DICT[array_to_match]
        else:
            array_to_match = CMD_ARG_DICT.get('options', {}).get(cmd)
            if array_to_match:
                match_list = CMD_ARG_DICT[array_to_match]
            else:
                array_to_match = 'options'
                match_list = CMD_ARG_DICT.get('options',{}).keys()

    matches = [item for item in match_list
                   if item.upper().startswith(text.upper())]
    try:
        return matches[state]
    except IndexError:
        return None

def setUpTabCompleter():
    """Starts our tab-completer when running interactively"""
    readline.set_completer(tab_completer)
    if sys.platform == 'darwin':
        readline.parse_and_bind ("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

def help(args):
    '''Prints available subcommands'''
    print "Available sub-commands:"
    subcommands = CMD_ARG_DICT['cmds'].keys()
    subcommands.sort()
    for item in subcommands:
        print '\t%s' % item
    return 0

def handleSubcommand(args, plist):
    '''Does all our subcommands'''
    # strip leading hyphens and
    # replace embedded hyphens with underscores
    # so '--add-pkg' becomes 'add_pkg'
    # and 'new-manifest' becomes 'new_manifest'
    subcommand = args[0].lstrip('-').replace('-', '_')

    # special case the exit command
    if subcommand == 'exit':
       # we'll do something special here
       plist.synchronize()
       sys.exit(0)

    if subcommand == 'help':
        return help(args)

    try:
        # find function to call by looking in the ImagrConfigPlist name table
        # for a function with a name matching the subcommand
        subcommand_function = getattr(plist, subcommand)
        return subcommand_function(args[1:])
    except (TypeError, KeyError, AttributeError), errmsg:
#        print >> sys.stderr, 'Unknown subcommand: %s: %s' % (subcommand, errmsg)
        print >> sys.stderr, 'Unknown subcommand: %s' % subcommand
        help(args)
        return 2


# global variable
CMD_ARG_DICT = {}

def main():
    global CMD_ARG_DICT
    parser = argparse.ArgumentParser()
    parser.add_argument("plist", help="Path to a plist to edit. Will create if it doesn't exist.")
    plistArgs = parser.parse_args()
    
    if os.path.exists(plistArgs.plist):
        try:
            configPlist = ImagrConfigPlist(plistArgs.plist)
        except Exception, errmsg:
            print >> sys.stderr, 'Could not read plist %s because: %s' % (plistArgs.plist, errmsg)
            sys.exit(-1)
    else:
        # file does not exist, we'll save it on exit
        configPlist = ImagrConfigPlist(plistArgs.plist)
    
    # List of commands mapped to data types that they'll autocomplete with
    cmds = {
        'new-password':         'workflows',     # new-password <password>
        'show-password':        'workflows',     # show-password
        'add-workflow':         'workflows',    # add-workflow <name>
        'display-workflows':    'workflows',    # display-workflows
        'show-workflow':        'workflows',    # show-workflow <workflow>
        'remove-workflow':      'workflows',    # remove-workflow <workflow>
        'set-restart-action':   'workflows',    # set-restart-action <workflow> <restart> 
        'set-bless-target':     'workflows',    # set-bless-target <workflow> <t/f> 
        'set-description':      'workflows',    # set-description <workflow> <desc>
        'add-image-component':  'workflows',    # add-image-component <workflow> <index> <url>
        'add-package-component':  'workflows',    # add-package-component <workflow> <index> <url> <first_boot t/f>
        'add-computername-component':  'workflows',    # add-image-component <workflow> <index> <use_serial t/f> <auto t/f>
        'add-script-component':  'workflows',    # add-image-component <workflow> <index> <content> <first_boot t/f>
        'add-erase-component':  'workflows',
        'add-partition-component':  'workflows',
        'remove-component':     'components',   # remove-component <index> <workflow>
        'display-components':   'components',   # display-components <workflow>
        'exit':                 'default',
        'help':                 'default',
        } 
    CMD_ARG_DICT['cmds'] = cmds

    CMD_ARG_DICT['default'] = []
    CMD_ARG_DICT['workflows'] = configPlist.getWorkflowNames()
    CMD_ARG_DICT['components'] = configPlist.getWorkflowComponentTypes()

    setUpTabCompleter()
    print 'Entering interactive mode... (type "help" for commands)'
    while 1:
        try:
            cmd = raw_input('> ')
        except (KeyboardInterrupt, EOFError):
            # React to Control-C and Control-D
            print # so we finish off the raw_input line
            sys.exit(0)
        args = shlex.split(cmd)
        #print "Args: %s" % args
        handleSubcommand(args, configPlist)

if __name__ == '__main__':
    main()
