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

# Imagr Config Plist class

class ImagrConfigPlist():
    workflowComponentTypes = {  'image' : {'url':'http'}, 
                                'package' : { 'url' : 'http', 'first_boot' : True },
                                'computername' : { 'use_serial' : False, 'auto' : False },
                                'script' : { 'content' : '#!/bin/bash', 'first_boot' : True }
                             }
    
    def __init__(self, path):
        if os.path.exists(path):
            plist = plistlib.readPlist(path)
            self.workflowDict = dict()
            self.password = plist.get('password')
            for workflow in plist.get('workflows'):
                self.workflowDict[str(workflow.get('name'))] = workflow  #In other words, self.workflowDict['Sup']['name'] == 'Sup'
        else:
            self.password = ''
            self.workflows = list()
            self.workflowDict = dict()
        self.plistPath = path
    
    def synchronize(self):
        """Writes the current plist to disk"""
        with open(self.plistPath, 'wb') as outfile:
            plist = dict()
            plist['password'] = self.password
            workflows = list()
            for workflow in self.workflowDict.keys():
                workflows.append(workflow)
            plist['workflows'] = workflows
            plistlib.writePlist(plist)
    
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
    
    def getWorkflows(self):
        """Returns a list of workflows in the plist"""
        return self.workflows
    
    def getWorkflowNames(self):
        """Returns a list of names of workflows in the plist"""
        return self.workflowDict.keys()
    
    # Workflow subcommands
    def display_workflows(self, args):
        """Displays a pretty-print list of workflows"""
        #args is basically ignored
        if len(args) != 0:
            print >> sys.stderr, 'Usage: display-workflows'
            return 22 # Invalid argument
        workflows = list()
        for workflow in self.workflowDict.keys():
            workflows.append(workflow)
        pprint.pprint(workflows)
        return 0
    
    def add_workflow(self, args):
        """Adds a new workflow to the list of workflows"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: add-workflow <workflowName>'
            return 22
        workflow = dict()
        workflow['name'] = args[0]
        workflow['description'] = ''
        workflow['restart_action'] = 'none'
        workflow['bless_target'] = False
        workflow['components'] = list()
        self.workflowDict[args[0]] = workflow
        self.show_workflow(args)
        return 0
    
    def remove_workflow(self, args):
        """Removes workflow with given name from list"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: remove-workflow <workflowName>'
            return 22
        del self.workflowDict[args[0]]
        self.display_workflows([])
        return 0
    
    def show_workflow(self, args):
        """Shows a workflow with a given name"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: show-workflow <workflowName>'
            return 22
        pprint.pprint(self.workflowDict[args[0]])
        return 0
    
    # Password subcommands
    def show_password(self, args):
        """Returns the password hash"""
        #args is basically ignored
        if len(args) != 0:
            print >> sys.stderr, 'Usage: show-password'
            return 22 # Invalid argument
        print self.password
        return 0
    
    def new_password(self, args):
        """Sets a new password"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: new-password <password>'
            return 22
        self.password = hashlib.sha512(str(args[0])).hexdigest()
        self.show_password([])
        return 0
    
    # RestartAction subcommands
    def set_restart_action(self, args):
        """Sets a restart action for the given workflow"""
        if len(args) > 2 or len(args) == 0:
            print >> sys.stderr, 'Usage: set-restart-action <workflowName> <action>'
            return 22
        if len(args) == 1:
            action = 'none'
        if len(args) == 2:
            if args[1] not in ['restart', 'shutdown', 'none']:
                print >> sys.stderr, 'Usage: set-restart-action must have \'restart\', \'shutdown\', or \'none\''
                return 22
            action = args[1]
        self.workflowDict[args[0]]['restart_action'] = action
        self.show_workflow(args[0:1])
        return 0
    
    # Bless subcommands
    def set_bless_target(self, args):
        """Sets bless to True or False for the given workflow"""
        if len(args) != 2:
            print >> sys.stderr, 'Usage: set-bless-target <workflowName> <True/False>'
            return 22
        self.workflowDict[args[0]]['bless_target'] = bool(args[1])
    
    # Description subcommands
    def set_description(self, args):
        """Sets description for the given workflow"""
        if len(args) != 2:
            print >> sys.stderr, 'Usage: set-description <workflowName> <description>'
            return 22
        self.workflowDict[args[0]]['description'] = args[1]
        self.show_workflow(args[0:1])
        return 0
    
    # Component-related functions that are not subcommands
    def getComponents(self, workflowName):
        """Returns a list of components for a given workflow"""
        return self.workflowDict[workflowName]['components']
    
    # Component subcommands
    def display_components(self, args):
        """Displays a pretty-print list of components for a given workflow"""
        if len(args) != 1:
            print >> sys.stderr, 'Usage: display_components <workflowName>'
            return 22
        pprint.pprint(self.workflowDict[args[0]]['components'])
    
    def remove_component(self, index, workflowName):
        """Removes a component at index from workflow"""
        del self.workflowDict[workflowName]['components'][index]
    
    def addImageComponent(self, index, url, workflowName):
        """Adds an Image task at index with URL for a workflow"""
        imageComponent = self.workflowComponentTypes['image']
        imageComponent['url'] = url
        self.workflowDict[workflowName]['components'].insert(index, imageComponent)
    
    def addPackageComponent(self, index, url, workflowName, first_boot=True):
        """Adds a Package task at index with URL, first_boot for workflow"""
        packageComponent = self.workflowComponentTypes['package']
        packageComponent['url'] = url
        packageComponent['first_boot'] = first_boot
        self.workflowDict[workflowName]['components'].insert(index, packageComponent)
    
    def addComputerNameComponent(self, index, workflowName, use_serial=False, auto=False):
        """Adds a ComputerName task at index with use_serial and auto for workflow"""
        computerNameComponent = self.workflowComponentTypes['computername']
        computerNameComponent['use_serial'] = use_serial
        computerNameComponent['auto'] = auto
        self.workflowDict[workflowName]['components'].insert(index, computerNameComponent)
    
    def addScriptComponent(self, index, content, workflowName, first_boot=True):
        """Adds a Script component at index with content for workflow"""
        scriptComponent = self.workflowComponentTypes['script']
        scriptComponent['content'] = content
        scriptComponent['first_boot'] = first_boot
        self.workflowDict[workflowName]['components'].insert(index, scriptComponent)


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
       print "GOODBYE!"
       sys.exit(0)

    if subcommand == 'help':
        return help(args)

    try:
        # find function to call by looking in the ImagrConfigPlist name table
        # for a function with a name matching the subcommand
        subcommand_function = getattr(plist, subcommand)
        return subcommand_function(args[1:])
    except (TypeError, KeyError, AttributeError):
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
        configPlist = ImagrConfigPlist()
    
    # List of commands mapped to data types that they'll autocomplete with
    cmds = {
        'new-password':         'workflows',     # new-password <password>
        'show-password':        'workflows',     # show-password
        'add-workflow':         'workflows',    # add-workflow <name>
        'display-workflows':    'workflows',    # display-workflows [<index>]
        'show-workflow':        'workflows',    # show-workflow <workflow>
        'remove-workflow':      'workflows',    # remove-workflow <workflow>
        'set-restart-action':   'workflows',    # set-restart-action <workflow> <restart> 
        'set-bless-target':     'workflows',    # set-bless-target <t/f> <workflow>
        'set-description':      'workflows',    # set-description <desc> <workflow>
        'add-component':        'workflows',   # add-component <type> [<index>] <workflow>
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
            # At some point I'll do something more useful here
            sys.exit(0)
        args = shlex.split(cmd)
        print "Args: %s" % args
        handleSubcommand(args, configPlist)

if __name__ == '__main__':
    main()
