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
import sys

class EditAuTxtOptions(object):

    @staticmethod
    def make_parser():
        usage = '%prog [OPTIONS] AUTXT'
        parser = optparse.OptionParser(version=__version__, description=__doc__, usage=usage)
        # Default group
        # --help, --version defined automatically
        parser.add_option('--copyright', '-C', action='store_true', help='show copyright and exit')
        parser.add_option('--license', '-L', action='store_true', help='show license and exit')
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

def _main():
    '''Main method.'''
    parser = EditAuTxtOptions.make_parser()
    (opts, args) = parser.parse_args()
    options = EditAuTxtOptions(parser, opts, args)

# Main entry point
if __name__ == '__main__': _main()

