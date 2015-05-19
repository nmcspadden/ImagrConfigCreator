#!/usr/bin/python

import fnmatch
import shlex
import subprocess
import sys
import argparse
import os
import readline

try:
    import FoundationPlist as plistlib
except ImportError:
    import plistlib

# Imagr Config Plist class

class ImagrConfigPlist():
    configPlist = dict()
    
    def __init__(self, path):
        if os.path.exists(self.plistPath):
            
        self.plistPath = path
    
    # List of commands mapped to data types that they'll autocomplete with
    cmds = {
        'new-password':         'password',     # new-password <password> <workflow>
        'show-password':        'password',     # show-password <workflow>
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
    CMD_ARG_DICT['workflows'] = getWorkflowNames()
    CMD_ARG_DICT['components'] = getComponentList()


# Generic helper functions for autocomplete, stolen from Munki

def tab_completer(text, state):
    '''Called by the readline lib to calculate possible completions'''
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
    '''Starts our tab-completer when running interactively'''
    readline.set_completer(tab_completer)
    if sys.platform == 'darwin':
        readline.parse_and_bind ("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")


def main():
    workflowList = list()
    plistPassword = ''
    
    parser = argparse.ArgumentParser()
    parser.add_argument("plist", help="Path to a plist to edit. Will create if it doesn't exist.")
    plistArgs = parser.parse_args()
    
    if os.path.exists(plistArgs.plist):
        try:
            configPlist = plistlib.readPlist(plistArgs.plist)
        except Exception, errmsg:
            print >> sys.stderr, 'Could not read plist %s' % plistArgs.plist
            sys.exit(-1)
        # file exists, must be parsed
        plistPassword = configPlist.get('password', '')
        workflowList = configPlist.get('workflows')
    else:
        # file does not exist, we'll save it on exit
        configPlist = dict()
    
    cmds = ['new-password',         # new-password <password> <workflow>
            'show-password',        # show-password <workflow>
            'add-workflow',         # add-workflow <name>
            'display-workflows',    # display-workflows [<index>]
            'remove-workflow',      # remove-workflow <workflow>
            'set-restart-action',   # set-restart-action <restart> <workflow>
            'set-bless-target',     # set-bless-target <t/f> <workflow>
            'set-description',      # set-description <desc> <workflow>
            'add-component',        # add-component <type> [<index>] <workflow>
            'remove-component',     # remove-component <index> <workflow>
            'display-components',   # display-components [<index>] <workflow>
            'list-types',   
            'exit',
            'help',
            'version'
            } 
    CMD_ARG_DICT['cmds'] = cmds

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
        handleSubcommand(args, configPlist)

if __name__ == '__main__':
    main()
