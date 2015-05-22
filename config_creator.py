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

#try:
#    import FoundationPlist as plistlib
#except ImportError:
#    import plistlib
import FoundationPlist as plistlib

# Stolen from Munki/makepkginfo

def readfile(path):
    '''Reads file at path. Returns a string.'''
    try:
        fileobject = open(os.path.expanduser(path), mode='r', buffering=1)
        data = fileobject.read()
        fileobject.close()
        return data
    except (OSError, IOError):
        print >> sys.stderr, "Couldn't read %s" % path
        return ""

# Helper

def stringToBool(theString):
    return theString.lower() in ("yes", "true", "t", "1")

# Imagr Config Plist class

class ImagrConfigPlist():
    workflowComponentTypes = {  'image' : {'url':'http'}, 
                                'package' : { 'url' : 'http', 'first_boot' : True },
                                'computername' : { 'use_serial' : False, 'auto' : False },
                                'script' : { 'content' : '#!/bin/bash', 'first_boot' : True }
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
    
    # Component-type subcommands
    def list_types(self, args):
        if len(args) != 0:
            print >> sys.stderr, 'Usage: display-workflows'
            return 22 # Invalid argument
        pprint.pprint(self.workflowComponentTypes)
        return 0
    
    # Workflow-related functions that are not subcommands    
    def getWorkflowComponentTypes(self):
        """Returns a list of possible workflowComponentTypes"""
        return self.workflowComponentTypes.keys()
    
    def getWorkflowNames(self):
        """Returns a list of names of workflows in the plist"""
        nameList = list()
        for workflow in self.internalPlist['workflows']:
            nameList.append(workflow['name'])
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
        if len(args) < 1 or len(args) > 2:
            print >> sys.stderr, 'Usage: add-workflow <workflowName> [<index>]'
            return 22
        index = len(self.internalPlist['workflows'])
        if len(args) == 2:
            index = int(args[1])
        # validate that the name isn't being reused
        for workflow in self.internalPlist.get('workflows'):
            if workflow['name'] == args[0]:
                print >> sys.stderr, 'Error: name is already in use. Workflow names must be unique.'
                return 22
        workflow = dict()
        workflow['name'] = args[0]
        workflow['description'] = ''
        workflow['restart_action'] = 'none'
        workflow['bless_target'] = False
        workflow['components'] = list()
        self.internalPlist['workflows'].insert(index, workflow)
        self.show_workflow(args[0:1])
        return 0
    
    def remove_workflow(self, args):
        """Removes workflow with given name or index from list"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: remove-workflow <workflowName or index>'
            return 22
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
        try:
            del self.internalPlist['workflows'][key]
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        self.display_workflows([])
        return 0
    
    def show_workflow(self, args):
        """Shows a workflow with a given name or index"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: show-workflow <workflowName or index>'
            return 22
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
        try:
            pprint.pprint(self.internalPlist['workflows'][key])
        except (IndexError, TypeError):
            # If it gets here, no workflow by that name or index was found.
            print >> sys.stderr, 'No workflow found at %s: ' % args[0]
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
        if len(args) != 1:
            print >> sys.stderr, 'Usage: new-password <password>'
            return 22
        self.internalPlist['password'] = hashlib.sha512(str(args[0])).hexdigest()
        self.show_password([])
        return 0
    
    # RestartAction subcommands
    def set_restart_action(self, args):
        """Sets a restart action for the given workflow"""
        if len(args) > 2 or len(args) == 0:
            print >> sys.stderr, 'Usage: set-restart-action <workflowName or index> <action>'
            return 22
        if len(args) == 1:
            action = 'none'
        if len(args) == 2:
            if args[1] not in ['restart', 'shutdown', 'none']:
                print >> sys.stderr, 'Usage: set-restart-action must have \'restart\', \'shutdown\', or \'none\''
                return 22
            action = args[1]
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
            name = [ args[0] ]
        try:
            self.internalPlist['workflows'][key]['restart_action'] = action
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        self.show_workflow(name)
        return 0
    
    # Bless subcommands
    def set_bless_target(self, args):
        """Sets bless to True or False for the given workflow"""
        if len(args) != 2:
            print >> sys.stderr, 'Usage: set-bless-target <workflowName or index> <True/False>'
            return 22
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
            name = [ args[0] ]
        try:
            self.internalPlist['workflows'][key]['bless_target'] = stringToBool(args[1])
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        self.show_workflow(name)
        return 0
    
    # Description subcommands
    def set_description(self, args):
        """Sets description for the given workflow"""
        if len(args) != 2:
            print >> sys.stderr, 'Usage: set-description <workflowName or index> <description>'
            return 22
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
            name = [ args[0] ]
        try:
            self.internalPlist['workflows'][key]['description'] = args[1]
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        self.show_workflow(name)
        return 0
    
    # Component subcommands
    def display_components(self, args):
        """Displays a pretty-print list of components for a given workflow"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: display_components <workflowName or index>'
            return 22
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
        try:
            for i, elem in enumerate(self.internalPlist['workflows'][key]['components']):
                print '{0}: {1}'.format(i, elem)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        return 0
    
    def remove_component(self, args):
        """Removes a component at index from workflow"""
        if len(args) != 2:
            print >> sys.stderr, 'Usage: remove-component <workflowName or index> <index>'
            return 22
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
        try:
            del self.internalPlist['workflows'][key]['components'][int(args[1])]
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        return 0
    
    def add_image_component(self, args):
        """Adds an Image task at index with URL for a workflow. If no index is specified, defaults to end"""
        if len(args) < 2:
            print >> sys.stderr, 'Usage: add-image-component <workflowName or index> <url> [<index>]'
            return 22
        imageComponent = self.workflowComponentTypes['image']
        imageComponent['url'] = args[1]
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
            name = [ args[0] ]
        try:
            index = len(self.internalPlist['workflows'][key]['components'])
            if len(args) == 3:
                index = int(args[2])
            self.internalPlist['workflows'][key]['components'].insert(index, imageComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        self.show_workflow(name)
        return 0
    
    def add_package_component(self, args):
        """Adds a Package task at index with URL, first_boot for workflow"""
        if len(args) < 3:
            print >> sys.stderr, 'Usage: add-package-component <workflowName or index> <url> <first_boot t/f> [<index>]'
            return 22
        packageComponent = self.workflowComponentTypes['package']
        packageComponent['url'] = args[1]
        packageComponent['first_boot'] = stringToBool(args[2])
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
            name = [ args[0] ]
        try:
            index = len(self.internalPlist['workflows'][key]['components'])
            if len(args) == 4:
                index = int(args[3])
            self.internalPlist['workflows'][key]['components'].insert(index, packageComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        self.show_workflow(name)
        return 0
    
    def add_computername_component(self, args):
        """Adds a ComputerName task at index with use_serial and auto for workflow"""
        if len(args) < 3:
            print >> sys.stderr, 'Usage: add-computername-component <workflowName or index> <use_serial t/f> <auto t/f> [<index>]'
            return 22
        computerNameComponent = self.workflowComponentTypes['computername']
        computerNameComponent['use_serial'] = stringToBool(args[1])
        computerNameComponent['auto'] = stringToBool(args[2])
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
            name = [ args[0] ]
        try:
            index = len(self.internalPlist['workflows'][key]['components'])
            if len(args) == 4:
                index = int(args[3])
            self.internalPlist['workflows'][key]['components'].insert(index, computerNameComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
            return 22
        self.show_workflow(name)
        return 0
    
    def add_script_component(self, args):
        """Adds a Script component at index with content for workflow"""
        if len(args) < 3:
            print >> sys.stderr, 'Usage: add-script-component <workflowName> <path to script> <first_boot t/f> [<index>]'
            return 22
        scriptComponent = self.workflowComponentTypes['script']
        scriptComponent['content'] = readfile(args[1])
        scriptComponent['first_boot'] = stringToBool(args[2])
        try:
            key = int(args[0])
            # If an index is provided, it can be cast to an int
            name = self.findWorkflowNameByIndex(key)
        except ValueError:
            # A name was provided that can't be cast to an int
            key = self.findWorkflowIndexByName(args[0])
            name = [ args[0] ]
        try:
            index = len(self.internalPlist['workflows'][key]['components'])
            if len(args) == 4:
                index = int(args[3])
            self.internalPlist['workflows'][key]['components'].insert(index, scriptComponent)
        except (IndexError, TypeError):
            print >> sys.stderr, 'Error: No workflow found at %s' % args[0]
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
        print >> sys.stderr, 'Unknown subcommand: %s: %s' % (subcommand, errmsg)
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
        configPlist = ImagrConfigPlist()
    
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
        'remove-component':     'components',   # remove-component <index> <workflow>
        'display-components':   'components',   # display-components <workflow>
        'list-types':           'components',   
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
            configPlist.synchronize()
            sys.exit(0)
        args = shlex.split(cmd)
        #print "Args: %s" % args
        handleSubcommand(args, configPlist)

if __name__ == '__main__':
    main()
