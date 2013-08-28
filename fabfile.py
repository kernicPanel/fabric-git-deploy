#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from fabric.api import *
from fabric.contrib.console import confirm
import os
import cmd
import ConfigParser
import pprint
import socket

config = ConfigParser.RawConfigParser()
config.read('deploy.cfg')

currentBranch = ''
processBranches = ['develop', 'testing', 'master', 'recipe', 'staging', 'production']
localBranches = []
source = ''
destination = ''
environnements = config.sections()
localModifs = False
debug = False

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

def printHeader(message):
    print bcolors.HEADER + message + bcolors.ENDC

def printWarning(message):
    print bcolors.WARNING + message + bcolors.ENDC

def printError(message):
    print bcolors.FAIL + message + bcolors.ENDC

def checkLocalEnv():
    """docstring for checkLocalEnv"""
    if env.user == 'wwwmastr':
        abort( bcolors.FAIL + "Veuillez utiliser ce script avec votre propre user" + bcolors.ENDC )

class FakeCommand:
    failure = False
    failed = False

    def splitlines(self):
        return ['line 1', 'line 2']

    def split(self, arg):
        return '* develop'

    def startswith(self, arg):
        return ''


def execLocal(command, capture=False):
    commandLine = bcolors.WARNING + os.getlogin() + "@" + socket.gethostname() + bcolors.OKGREEN + " " + os.path.abspath(os.path.curdir) + " $ " + bcolors.OKBLUE + command + bcolors.ENDC
    if debug:
        if not capture:
            print commandLine
        result = FakeCommand()
        return result
    else:
        if not capture:
            print "\n" + commandLine
        return local(command, capture)


def execRun(command, capture=False, expected=False):
    commandLine = bcolors.FAIL + env.user + "@" + env.host_string + bcolors.OKGREEN + " " + env.cwd + " $ " + bcolors.OKBLUE + command + bcolors.ENDC
    if debug:
        if not capture:
            print commandLine

        if expected:
            return expected

        result = FakeCommand()
        return result
    else:
        if not capture:
            print "\n" + commandLine
        return run(command, capture)


def hasModifs( remote = False):
    """docstring for hasModifs"""
    if not remote:
        #gsp = execLocal("git status --porcelain")
        gsp = execLocal("git status", True)
    else:
        #gsp = execRun("git status --porcelain")
        gsp = execRun("git status", True)
    gspArr = gsp.splitlines()
    for line in gspArr:
        #print line
        #if line[0] == 'M':
        if line == '# Changed but not updated:':
            #if not remote:
                #print "Des modifications de fichiers existent."
                #print "Veuillez comitter celles-ci ou lancer la commande 'git stash' pour les stocker, et 'git stash pop' pour les récupérer apres avoir relancé ce script."
                #print gsp
                #abort("Sortie")
            #else:
                return True

def checkModifs():
    """docstring for checkModifs"""
    if hasModifs() and confirm("Des modifications existent: Voulez-vous les stocker par un 'git stash' ?"):
        stash = execLocal("git stash")
        if not stash.failed:
            global localModifs
            localModifs = True
        else:
            printError("'git stash' a échoué.")
            printWarning("Veuillez comitter les modifications ou lancer la commande 'git stash' pour les stocker, et 'git stash pop' pour les récupérer apres avoir relancé ce script.")
            abort("Sortie du script")

def restoreModifs():
    """docstring for restoreModifs"""
    if localModifs:
        pop = execLocal("git stash pop")
        if pop.failed:
            printError("La restauration des modifications par 'git stash pop' a échoué ...")

class Source(cmd.Cmd):
    prompt = "Branche source (? for help) --> "
    #def do_current(self, value):
        #"""current branch"""
        #setSource(currentBranch)
        #return True

    def do_develop(self, value):
        """develop"""
        setSource(self.lastcmd)
        return True

    def do_testing(self, value):
        """testing"""
        setSource(self.lastcmd)
        return True

    def do_master(self, value):
        """master"""
        setSource(self.lastcmd)
        return True

    def do_recipe(self, value):
        """recipe"""
        setSource(self.lastcmd)
        return True

    def do_staging(self, value):
        """staging"""
        setSource(self.lastcmd)
        return True

    def do_quit(self, value):
        """quit"""
        setSource('quit')
        return True

    def do_EOF(self, line):
        return True

def setSource(branch):
    """Set source Branch"""
    global source
    source = branch
    #print "Branche source : " + branch

class Destination(cmd.Cmd):
    prompt = "Branche destination (? for help) --> "

    def testDestination(self, branch):
        """docstring for testDestination"""
        return processBranches.index(source) < processBranches.index(branch)

    def setDestination(self, branch):
        """Set destination Branch"""
        if not self.testDestination(branch):
            return False
        global destination
        destination = branch
        #print "Branche destination : " + branch
        return True

    def do_develop(self, value):
        """develop"""
        return self.setDestination(self.lastcmd)

    def do_testing(self, value):
        """testing"""
        return self.setDestination(self.lastcmd)

    def do_master(self, value):
        """master"""
        return self.setDestination(self.lastcmd)

    def do_recipe(self, value):
        """recipe"""
        return self.setDestination(self.lastcmd)

    def do_staging(self, value):
        """staging"""
        return self.setDestination(self.lastcmd)

    def do_production(self, value):
        """production"""
        return self.setDestination(self.lastcmd)

    def do_quit(self, value):
        """quit"""
        global destination
        destination = self.lastcmd
        return True

    def do_EOF(self, line):
        return True


def test():
    """docstring for test"""
    Destination().cmdloop()

def getCurrentBranch():
    """Retrieve current branch name"""
    branches = execLocal("git branch", True)
    global currentBranch
    currentBranch = branches.split('* ')[1].split('\n')[0]
    print("current branch : " + currentBranch)
    return currentBranch

def checkBranch(branch):
    """check if branch exists"""
    return branch in localBranches

def retrieveBranches():
    """init : Retrieve local branches"""
    names = execLocal("git branch", True).split('\n')
    global localBranches
    for branchName in names:
        localBranches.append(branchName.strip(' *'))

#def checkBranches():
    #"""Check if process branches exists"""
    #global localBranches
    #localBranches = execLocal("git branch", True).split('\n')
    ##print("local branches : ")
    #for branch in localBranches:
        #print(branch)
    #print("process branches : ")
    #for processBranch in processBranches:
        #print(processBranch)

def createLocalBranch(branch):
    """docstring for createLocalBranch"""
    #print("git branch " + branch + " origin/" + branch)
    execLocal("git branch " + branch + " origin/" + branch)

def pushTobranch():
    """docstring for pushTobranch"""
    indexSource = processBranches.index(source) + 1
    #print('source ' + str(indexSource))
    indexDestination = processBranches.index(destination) + 1
    #print('destination ' + str(indexDestination))
    for branch in processBranches[indexSource:indexDestination]:
        #print(branch)
        if not checkBranch(branch):
            createLocalBranch(branch)
        updateBranch(branch)


def updateBranch(branch):
    """Update branch with previous process branch"""
    prevBranch = processBranches[processBranches.index( branch ) - 1]
    #verif index > 0

    #print("git checkout " + branch)
    #print("git pull origin " + branch)
    #if not prevBranch == "production":
        #print("git merge " + prevBranch)
    #print("git push origin " + branch)

    execLocal("git checkout " + branch)
    #execLocal("git pull origin " + branch)
    execLocal("git pull")
    #execLocal("git rebase " + prevBranch)
    if not prevBranch == "production":
        execLocal("git merge --no-ff " + prevBranch)
    execLocal("git push origin " + branch)
    updateEnv(branch)

def cleanError(host, error, envHasModifs = False, command = False):
    """docstring for eanError"""
    print("sur " + host)
    printError("l'erreur suivante est survenue :")
    printError(error)
    if confirm("Ouvrir un shell sur l'environnement ?"):
        printWarning("'exit' ou ctrl-d pour revenir au script")
        if envHasModifs:
            printWarning("Attention, un 'git stash' a été effectué, et un 'git stash pop' vous sera prorosé avant l'arret du script ou sera effectué automatiquement si vous décidez de reprendre l'éxécution normale")
        open_shell(command)
    if not confirm("Poursuivre l'exécution du script ?"):
        if envHasModifs and confirm("Des modifications ont étées sauvegardée par un 'git stash'. Voulez-vous les restaurer par un 'git stash pop' ?"):
            pop = execRun("git stash pop")
            if not pop.failed:
                printWarning("Modifications restaurées")

        abort("Script interronpu par l'utilisateur")
    pass

def updateEnv(branch):
    """docstring for updateEnv"""
    #print branch
    if config.has_section(branch):
        env.user = config.get(branch, 'user')
        env.host_string = config.get(branch, 'host')
        env.warn_only = config.get(branch, 'warn_only')
        url = config.get(branch, 'url')
        source = config.get(branch, 'source')
        vardir = config.get(branch, 'vardir')
        sudopull = config.has_option(branch, 'sudopull')
        envHasModifs = False

        #print env.user
        #print env.host_string
        #print url
        #print source
        #print vardir
        with cd(url):
            with cd(source):
                confPwd = os.path.normpath(url + '/' + source)
                pwd = os.path.normpath(execRun('pwd', True, confPwd))
                if not pwd == confPwd:
                    #print pwd
                    #print confPwd
                    cleanError(env.host_string, "Mauvais url ou source dans le fichier de conf", envHasModifs, "cd " + confPwd)

                #cleanError(env.host_string, "test porcelain", envHasModifs, "cd " + confPwd)

                if hasModifs( True ):
                    envHasModifs = True
                    execRun("git stash")


                if sudopull:
                    print sudopull
                    #pull = execRun("sudo git pull origin " + branch)
                    pull = execRun("sudo git pull")
                else:
                    #print("git pull origin " + branch)
                    pull = execRun("git pull origin " + branch)
                    #pull = execRun("git pull")


                if pull.failed:
                    cleanError(env.host_string, pull, envHasModifs, "cd " + confPwd)
                if envHasModifs:
                    execRun("git stash pop")

            pwd = execRun('pwd', True)
            #print("rm -fr var/cache/* " + "var/" + vardir + "/cache/*")
            rm  = execRun("rm -fr var/cache/* " + "var/" + vardir + "/cache/*")
            if rm.failed:
                cleanError(env.host_string, rm, envHasModifs, "cd " + url)

def restoreCurrentBranch():
    """docstring for restoreCurrentBranch"""
    execLocal("git checkout " + currentBranch)

def deploy():
    """main deploy tool"""
    #hasModifs()
    checkLocalEnv()
    checkModifs()
    printHeader("\ndeploy start")
    getCurrentBranch()
    #commit()
    retrieveBranches()
    Source().cmdloop()
    if source == 'quit':
        return
    Destination().cmdloop()
    if destination == 'quit':
        return
    updateBranch(source)
    updateEnv(source)
    pushTobranch()
    restoreCurrentBranch()
    restoreModifs()
