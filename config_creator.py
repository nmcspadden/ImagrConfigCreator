#!/usr/bin/python

import subprocess
import sys
import os
import hashlib
import pprint
import argparse

#try:
#    import FoundationPlist as plistlib
#except ImportError:
#    import plistlib
import FoundationPlist as plistlib

# Imagr Config Plist class

class ImagrConfigPlist():
    
    workflowComponentTypes = dict()
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
                self.workflowDict[workflow.get('name')] = workflow
                #In other words, self.workflowDict['Sup']['name'] == 'Sup'
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
    
    def getWorkflowComponentTypes(self):
        """Returns a list of possible workflowComponentTypes"""
        return workflowComponentTypes.keys()
    
    def getWorkflows(self):
        """Returns a list of workflows in the plist"""
        return self.workflows
        
    def getWorkflowNames(self):
        """Returns a list of names of workflows in the plist"""
        return self.workflowDict.keys()
        
    def displayWorkflows(self):
        """Displays a pretty-print list of workflows"""
        pprint.pprint(self.workflows)
    
    def getPassword(self):
        """Returns the password hash"""
        return self.password
    
    def newPassword(self, password):
        """Sets a new password"""
        self.password = hashlib.sha512(str(password)).hexdigest()
        
    def setRestartAction(self, workflowName, action='None'):
        """Sets a restart action for the given workflow"""
        self.workflowDict[workflowName]['restart_action'] = action
        
    def setBless(self, workflowName, bless=False):
        """Sets bless to True or False for the given workflow"""
        self.workflowDict[workflowName]['bless_target'] = bless
        
    def setDescription(self, workflowName, description=''):
        """Sets description for the given workflow"""
        self.workflowDict[workflowName]['description'] = description
    
    def displayComponents(self, workflowName):
        """Displays a pretty-print list of components for a given workflow"""
        pprint.pprint(self.workflowDict[workflowName]['components'])
        
    def getComponents(self, workflowName):
        """Returns a list of components for a given workflow"""
        return self.workflowDict[workflowName]['components']
        
    def removeComponent(self, index, workflowName):
        """Removes a component at index from workflow"""
        del self.workflowDict[workflowName]['components'][index]
        
    def addImageComponent(self, index, url, workflowName):
        """Adds an Image task at index with URL for a workflow"""
        imageComponent = workflowComponentTypes['image']
        imageComponent['url'] = url
        self.workflowDict[workflowName]['components'].insert(index, imageComponent)
        
    def addPackageComponent(self, index, url, workflowName, first_boot=True):
        """Adds a Package task at index with URL, first_boot for workflow"""
        packageComponent = workflowComponentTypes['package']
        packageComponent['url'] = url
        packageComponent['first_boot'] = first_boot
        self.workflowDict[workflowName]['components'].insert(index, packageComponent)
        
    def addComputerNameComponent(self, index, workflowName, use_serial=False, auto=False):
        """Adds a ComputerName task at index with use_serial and auto for workflow"""
        computerNameComponent = workflowComponentTypes['computername']
        computerNameComponent['use_serial'] = use_serial
        computerNameComponent['auto'] = auto
        self.workflowDict[workflowName]['components'].insert(index, computerNameComponent)
        
    def addScriptComponent(self, index, content, workflowName, first_boot=True):
        """Adds a Script component at index with content for workflow"""
        scriptComponent = workflowComponentTypes['script']
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
 #       'new-password':         'password',     # new-password <password> <workflow>
 #       'show-password':        'password',     # show-password <workflow>
        'add-workflow':         'workflows',    # add-workflow <name>
        'display-workflows':    'workflows',    # display-workflows [<index>]
        'remove-workflow':      'workflows',    # remove-workflow <workflow>
        'set-restart-action':   'workflows',    # set-restart-action <restart> <workflow>
        'set-bless-target':     'workflows',    # set-bless-target <t/f> <workflow>
        'set-description':      'workflows',    # set-description <desc> <workflow>
        'add-component':        'components',   # add-component <type> [<index>] <workflow>
        'remove-component':     'components',   # remove-component <index> <workflow>
        'display-components':   'components',   # display-components [<index>] <workflow>
        'list-types':           'components',   
        'exit':                 'default',
        'help':                 'default',
        'version':              'default'
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
            cleanupAndExit(configPlist, 0)
        args = shlex.split(cmd)
        print "Args: %s" % args
        handleSubcommand(args, configPlist)

if __name__ == '__main__':
    main()
