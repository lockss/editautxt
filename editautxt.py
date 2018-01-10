#!/usr/bin/env python2

'''A script to edit the LOCKSS Daemon's au.txt file offline.'''

__copyright__ = '''\
Copyright (c) 2000-2018, Board of Trustees of Leland Stanford Jr. University.
All rights reserved.'''

__license__ = '''\
Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.'''

__version__ = '1.1.0'

import optparse
import os.path
import shutil
import sys

class EditAuTxtOptions(object):

    @staticmethod
    def make_parser():
        usage = '%prog [OPTIONS] {--auid AUID|--auids=AFILE} AUTXT SRCREPO DSTREPO DEFREPO'
        parser = optparse.OptionParser(version=__version__, description=__doc__, usage=usage)
        # Default group
        # --help, --version defined automatically
        parser.add_option('--copyright', '-C', action='store_true', help='show copyright and exit')
        parser.add_option('--license', '-L', action='store_true', help='show license and exit')
        group = optparse.OptionGroup(parser, 'AUIDs')
        group.add_option('--auid', action='append', default=list(), help='add AUID to target AUIDs')
        group.add_option('--auids', action='append', default=list(), metavar='AFILE', help='add AUIDs in AFILE to target AUIDs')
        parser.add_option_group(group)
        group = optparse.OptionGroup(parser, 'Other options')
        group.add_option('--warn-if-missing', action='store_true', default=False, help='do not fail if a target AUID is not found in au.txt')
        parser.add_option_group(group)
        return parser

    def __init__(self, parser, opts, args):
        '''
        Constructor.

        Arguments:
        - parser (optparse.OptionParser): an option parser
        - opts (optparse.Values): the option values returned by the option
        parser
        - args (list of strings): the remaining arguments returned by the
        option parser
        '''
        super(EditAuTxtOptions, self).__init__()
        # --help, --version handled automatically
        # --copyright, --license
        if any([opts.copyright, opts.license]):
            if opts.copyright:
                print __copyright__
            elif opts.license:
                print __copyright__
                print
                print __license__
            else:
                raise RuntimeError('internal error')
            sys.exit()
        # autxt, srcrepo, dstrepo, defrepo, srcdir, dstdir, defdir
        if len(args or list()) != 4:
            parser.error('expected 4 arguments, got %d' % (len(args or list()),))
        self.autxt, self.srcrepo, self.dstrepo, self.defrepo = args
        if not os.path.isfile(self.autxt):
            parser.error('file not found: %s' % (autxt,))
        self.srcdir = self.repodir(parser, self.srcrepo)
        self.dstdir = self.repodir(parser, self.dstrepo)
        self.defdir = self.repodir(parser, self.defrepo)
        # auids
        self.auids = opts.auid[:]
        for fstr in opts.auids:
            self.auids.extend(file_lines(fstr))
        if len(self.auids) == 0:
            parser.error('at least one target AUID is required')
        # warn_if_missing
        self.warn_if_missing = bool(opts.warn_if_missing)

    def repodir(self, parser, repopath):
        '''
        Checks if a directory string corresponds to a daemon repository by
        checking if it has a 'cache' subdirectory. If it does, that
        subdirectory is returned. If not, the error function of the option
        parser is invoked.

        Arguments:
        - parser (optparse.OptionParser): an option parser
        - repopath (string): a directory

        Returns:
        The 'cache' subdirectory of the given directory.
        '''
        if not os.path.isdir(repopath):
            parser.error('directory not found: %s' % (repopath,))
        repodir = os.path.join(repopath, 'cache')
        if not os.path.isdir(repodir):
            parser.error('directory not found: %s' % (repodir,))
        return repodir

class EditAuTxt(object):

    def __init__(self, options):
        '''
        Constructor.

        Arguments:
        - options (EditAuTxtOptions): an options struct.
        '''
        super(EditAuTxt, self).__init__()
        self.options = options
        self.autxtauids = None
        self.autxtlines = None

    def ask_daemon_stopped(self):
        '''
        Deliberately obnoxious interactive prompt asking twice if the daemon
        is really stopped; exits if the user does not respond properly.
        '''
        resp = raw_input('Are you sure the LOCKSS Daemon is stopped? [yn] ')
        if resp != 'y':
            sys.exit('Exiting.')
        print 'Are you REALLY sure the LOCKSS Daemon is stopped?'
        print 'Type yes only if you are absolutely certain.'
        resp = raw_input()
        if resp != 'yes':
            sys.exit('Exiting.')

    def backup_autxt(self):
        '''
        Makes a backup of au.txt before rewriting it. Tries au.txt.1, au.txt.2,
        etc. until a never-before-used backup file name is found.
        '''
        i = 1
        while True:
            filestr = '%s.%d' % (self.options.autxt, i)
            if not os.path.isfile(filestr):
                break
            i = i + 1
        shutil.copyfile(self.options.autxt, filestr)

    def perform_change(self):
        '''
        Performs the requested change from one daemon repository directory
        to another.
        '''
        srcval = 'local\\:%s' % (self.options.srcrepo,)
        dstval = 'local\\:%s' % (self.options.dstrepo,)
        errors = list()
        for auid in self.options.auids:
            # If --warn-if-missing was used, okay if AUID not found
            linenum = self.autxtauids.get(auid, None)
            if linenum is None and self.options.warn_if_missing:
                continue
            # Parse original au.txt repository line
            line = self.autxtlines[linenum]
            key, eq, val = line.partition('=')
            # Verify that origin is correct
            if val != srcval:
                # Incorrect: remember error
                errors.append(auid)
            else:
                # Correct: rewrite au.txt repository line
                self.autxtlines[linenum] = '%s=%s' % (key, dstval)
        # Report and exit if there are any errors
        if len(errors) > 0:
            print 'AUIDs not in %s in au.txt:' % (self.options.srcrepo)
            for auid in errors:
                print auid
            sys.exit('Exiting.')

    def parse_autxt(self):
        '''
        Parses au.txt (from the lines loaded in memory).
        '''
        # Build a map from AUID to the line number in au.txt where that AU's
        # repository is defined (or -1 if there is no explicit repository line
        # in au.txt for that AU)
        self.autxtauids = dict()
        for i, line in enumerate(self.autxtlines):
            if '.reserved.' not in line:
                continue
            pluginid, dot, aukey = line.rpartition('.reserved.')[0].partition('org.lockss.au.')[2].partition('.')
            auid = '%s&%s' % (pluginid, aukey)
            if auid not in self.options.auids:
                continue
            if '.reserved.disabled=' in line:
                self.autxtauids.setdefault(auid, -1)
                continue
            if '.reserved.repository=' in line:
                self.autxtauids[auid] = i
        # Check that all the requested AUIDs were found in au.txt. Exit if any
        # were not found unless --warn-if-missing was used.
        errors = list()
        for auid in self.options.auids:
            if auid not in self.autxtauids:
                errors.append(auid)
        if len(errors) > 0:
            print 'AUIDs not found in au.txt:'
            for auid in errors:
                print auid
            if not self.options.warn_if_missing:
                sys.exit('Exiting')
        # Fix up default repository (AUIDs that map to line number -1) by
        # appending an explicit repository line to the end of the au.txt lines
        # in memory
        for auid in self.options.auids:
            if self.autxtauids.get(auid) == -1:
                self.autxtauids[auid] = len(self.autxtlines)
                self.autxtlines.append('org.lockss.au.%s.%s.reserved.repository=local\\:%s' % (auid.partition('&')[0], auid.partition('&')[2], self.options.defrepo))

    def read_autxt(self):
        '''
        Reads the lines of au.txt into memory.
        '''
        with open(os.path.expanduser(self.options.autxt)) as f:
            self.autxtlines = [x.rstrip() for x in f]

    def rewrite_autxt(self):
        '''
        Writes the modified au.txt lines in memory to au.txt.
        '''
        with open(os.path.expanduser(self.options.autxt), 'w') as f:
            for line in self.autxtlines:
                f.write(line + '\n')        

    def run(self):
        '''
        Entry point.
        '''
        self.ask_daemon_stopped()
        self.read_autxt()
        self.parse_autxt()
        self.perform_change()
        self.backup_autxt()
        self.rewrite_autxt()

# Last modified 2015-08-31
def file_lines(fstr):
    with open(os.path.expanduser(fstr)) as f: ret = filter(lambda y: len(y) > 0, [x.partition('#')[0].strip() for x in f])
    if len(ret) == 0: sys.exit('Error: %s contains no meaningful lines' % (fstr,))
    return ret

# Main entry point
if __name__ == '__main__':
    parser = EditAuTxtOptions.make_parser()
    (opts, args) = parser.parse_args()
    options = EditAuTxtOptions(parser, opts, args)
    EditAuTxt(options).run()

