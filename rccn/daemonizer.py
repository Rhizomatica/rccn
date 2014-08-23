#############################################################################
#  
# $Id: daemonizer.py,v 1.3 2005/01/22 01:05:44 irmen Exp $
# Run Pyro servers as daemon processes on Unix/Linux.
# This won't work on other operating systems such as Windows.
# Author: Jeff Bauer  (jbauer@rubic.com)
# This software is released under the MIT software license.
# Based on an earlier daemonize module by Jeffery Kunce
# Updated by Luis Camaano to double-fork-detach.
#
# This is part of "Pyro" - Python Remote Objects
# which is (c) Irmen de Jong - irmen@users.sourceforge.net
#
#############################################################################

import sys, os, time
from signal import SIGINT, SIGHUP
import logging
import pwd, grp
import getopt
log = logging.getLogger( 'DaemonStarter' )


class DaemonizerException:
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class Daemonizer:
    """
    Daemonizer is a class wrapper to run a Pyro server program
    in the background as daemon process.  The only requirement 
    is for the derived class to implement a main_loop() method.
    See Test class below for an example.

    The following command line operations are provided to support
    typical /etc/init.d startup/shutdown on Unix systems:

        start | stop | restart

    In addition, a daemonized program can be called with arguments:

        status  - check if process is still running

        debug   - run the program in non-daemon mode for testing

    Note: Since Daemonizer uses fork(), it will not work on non-Unix
    systems.
    """
    def __init__(self, pidfile=None):
        log.debug("Calling Daemonizer orig. init")
        if not pidfile:
            self.pidfile = "/tmp/%s.pid" % self.__class__.__name__.lower()
        else:
            self.pidfile = pidfile
        self.chuid=False
        self.chuid_actions=False

    def become_daemon(self, root_dir='/'):
        log.debug("Become Daemon")
        if os.fork() != 0:  # launch child and ...
            os._exit(0)  # kill off parent
        log.debug("Calling setsid")
        os.setsid()
        log.debug("Calling chdir")
        os.chdir(root_dir)
        log.debug("Calling umask")
        os.umask(0)
        log.debug("Calling fork")
        if os.fork() != 0: # fork again so we are not a session leader
            os._exit(0)
        log.debug("Wrapping stdin")
        sys.stdin.close()
        sys.__stdin__ = sys.stdin
        log.debug("Wrapping stdout")
        sys.stdout.close()
        sys.stdout = sys.__stdout__ = _NullDevice()
        log.debug("Wrapping stderr")
        sys.stderr.close()
        sys.stderr = sys.__stderr__ = _NullDevice()
        #sys.stderr = sys.__stderr__ = log.debug
        log.debug("Daemonized")
        #for fd in range(1024):
        #    try:
        #        os.close(fd)
        #    except OSError:
        #        pass

    def daemon_start(self, start_as_daemon=1, root_dir='/'):
        log.debug("Daemon Start")
        if start_as_daemon:
            self.become_daemon(root_dir)
        log.debug("Checking if the process is already running")
        if self.is_process_running():
            msg = "Unable to start server. Process is already running."
            raise DaemonizerException(msg)
        log.debug("Writing pid file")
        f = open(self.pidfile, 'w')
        f.write("%s" % os.getpid())
        f.close()
        log.debug("Calling main_loop")
        if self.chuid:
            log.debug("Change running privileges to "+str(self.chuid))
            print 'Change running privileges to', str(self.chuid)
            self.change_uid(self.chuid)
        self.main_loop()

    def daemon_stop(self):
        pid = self.get_pid()
        try:
            os.kill(pid, SIGINT)  # SIGTERM is too harsh...
            time.sleep(1)
            try:
                os.unlink(self.pidfile)
            except OSError:
                pass
        except IOError:
            pass

    def daemon_reload(self):
        pid = self.get_pid()
        try:
           os.kill(pid, SIGHUP)
        except:
           pass

    def get_pid(self):
        try:
            f = open(self.pidfile)
            pid = int(f.readline().strip())
            f.close()
        except IOError:
            pid = None
        return pid
    def is_process_running(self):
        pid = self.get_pid()
        if pid:
            try:
                os.kill(pid, 0)
                return 1
            except OSError:
                pass
        return 0

    def main_loop(self):
        """NOTE: This method must be implemented in the derived class."""
        msg = "main_loop method not implemented in derived class: %s" % \
              self.__class__.__name__
        raise DaemonizerException(msg)

    def change_uid(self, uid):
      c_user =  uid
      c_group = None
      print os.getuid
      if os.getuid() == 0:
         if ':' in c_user:
            c_user, c_group =  c_user.split(":", 1)
         cpw = pwd.getpwnam(c_user)
         c_uid = cpw.pw_uid
         if c_group:
            cgr = grp.getgrnam(c_group)
            c_gid = cgr.gr_gid
         else:
            c_gid = cpw.pw_gid
            c_group = grp.getgrgid(cpw.pw_gid).gr_name
         c_groups = []
         for item in grp.getgrall():
            if c_user in item.gr_mem:
               c_groups.append(item.gr_gid)
         if c_gid not in c_groups:
            c_groups.append(c_gid)

         if callable(self.chuid_actions):
            self.chuid_actions(c_uid, c_gid)

         os.setgid(c_gid)
         os.setgroups(c_groups)
         os.setuid(c_uid)

         

    def process_command_line(self, argv, verbose=1, usagestr=None, chuid_actions=False):
        usage = "usage:  %s [options] start | stop | reload | restart | status | debug " \
                "(run as non-daemon)\n\n" \
                % os.path.basename(argv[0])
        usage += "OPTIONS:\n"
        usage += "\t--chuid=<username[:group]>\tchange username and group of the running process\n"

        try:
            optlist, args = getopt.getopt(argv[1:], "", ['chuid='])
            for opt in optlist:
                if opt[0] == '--chuid':
                    self.chuid=opt[1]
                    self.chuid_actions=chuid_actions

        except:
            pass

        if usagestr:
            usage += usagestr
        if len(argv) < 2:
            print usage
            raise SystemExit
        else:
            operation = argv[len(argv)-1]
        pid = self.get_pid()
        if operation == 'status':
            if self.is_process_running():
                print "Server process %s is running." % pid
            else:
                print "Server is not running."
        elif operation == 'start':
            if self.is_process_running():
                print "Server process %s is already running." % pid
                raise SystemExit
            else:
                if verbose:
                    print "Starting server process."
                self.daemon_start(1, os.path.abspath(os.path.dirname(argv[0])))
        elif operation == 'stop':
            if self.is_process_running():
                self.daemon_stop()
                if verbose:
                    print "Server process %s stopped." % pid
            else:
                print "Server process %s is not running." % pid
                raise SystemExit
        elif operation == 'reload':
            if self.is_process_running():
               if verbose:
                  print "Reloading server process."
               self.daemon_reload()
            else:
               if verbose:
                  print "Server isn't running. Starting it."
               self.daemon_start(1, os.path.abspath(os.path.dirname(argv[0])))
        elif operation == 'restart':
            self.daemon_stop()
            if verbose:
                print "Restarting server process."
            self.daemon_start(1, os.path.abspath(os.path.dirname(argv[0])))
        elif operation == 'debug':
            self.daemon_start(0, os.path.abspath(os.path.dirname(argv[0])))
        else:
            print "Unknown operation:", operation
            raise SystemExit


class _NullDevice:
    """A substitute for stdout/stderr that writes to nowhere."""

    def isatty(self, *a, **kw):
        return False

    def write(self, s):
        pass

    def flush(self, s):
        pass


class Test(Daemonizer):
    def __init__(self):
        Daemonizer.__init__(self)

    def main_loop(self):
        while 1:
            time.sleep(1)


if __name__ == "__main__":
    test = Test()
    test.process_command_line(sys.argv)
