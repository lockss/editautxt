#!/usr/bin/env python2

'''A script to edit the LOCKSS Daemon's au.txt file offline.'''

__copyright__ = '''\
Copyright (c) 2000, Board of Trustees of Leland Stanford Jr. University.
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

__version__ = '0.1.0'

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
        if not os.path.isdir(repopath):
            parser.error('directory not found: %s' % (repopath,))
        repodir = os.path.join(repopath, 'cache')
        if not os.path.isdir(repodir):
            parser.error('directory not found: %s' % (repodir,))
        return repodir

class EditAuTxt(object):

    def __init__(self, options):
        super(EditAuTxt, self).__init__()
        self.options = options
        self.autxtauids = None
        self.autxtlines = None

    def ask_daemon_stopped(self):
        resp = raw_input('Are you sure the LOCKSS Daemon is stopped? [yn] ')
        if resp != 'y':
            sys.exit('Exiting.')
        print 'Are you REALLY sure the LOCKSS Daemon is stopped?'
        print 'Type yes only if you are absolutely certain.'
        resp = raw_input()
        if resp != 'yes':
            sys.exit('Exiting.')

    def backup_autxt(self):
        i = 1
        while True:
            filestr = '%s.%d' % (self.options.autxt, i)
            if not os.path.isfile(filestr):
                break
            i = i + 1
        shutil.copyfile(self.options.autxt, filestr)

    def perform_change(self):
        srcval = 'local\\:%s' % (self.options.srcrepo,)
        dstval = 'local\\:%s' % (self.options.dstrepo,)
        errors = list()
        for auid in self.options.auids:
            linenum = self.autxtauids.get(auid, None)
            if linenum is None and self.options.warn_if_missing:
                continue
            line = self.autxtlines[linenum]
            key, eq, val = line.partition('=')
            if val != srcval:
                errors.append(auid)
            else:
                self.autxtlines[linenum] = '%s=%s' % (key, dstval)
        if len(errors) > 0:
            print 'AUIDs not in %s in au.txt:' % (self.options.srcrepo)
            for auid in errors:
                print auid
            sys.exit('Exiting.')

    def parse_autxt(self):
        self.autxtauids = dict()
        for i, line in enumerate(self.autxtlines):
            if '.reserved.' not in line:
                continue
            pluginid, dot, aukey = line.rpartition('.reserved.disabled=')[0].partition('org.lockss.au.')[1].partition('.')
            auid = '%s&%s' % (pluginid, aukey)
            if auid not in self.options.auids:
                continue
            if '.reserved.disabled=' in line:
                self.autxtauids.setdefault(auid, -1)
                continue
            if '.reserved.repository=' in line:
                self.autxtauids[auid] = i
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
        # Fix up default repository
        for auid in self.options.auids:
            if self.autxtauids.get(auid) == -1:
                self.autxtauids[auid] = len(self.autxtlines)
                self.autxtlines.append('org.lockss.au.%s.%s.reserved.repository=%s' % (auid.partition('&')[0].replace('.', '|'), auid.partition('&')[1], self.options.defrepo))

    def read_autxt(self):
        with open(os.path.expanduser(self.options.autxt)) as f:
            self.autxtlines = [x.rstrip() for x in f]

    def rewrite_autxt(self):
        with open(os.path.expanduser(self.options.autxt), 'w') as f:
            for line in self.autxtlines:
                f.write(line + '\n')        

    def run(self):
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

