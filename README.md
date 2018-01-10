`editautxt` is a script written in Python that rewrites a LOCKSS au.txt file
so AUs are moved from one daemon repository directory (e.g. `/cache1/gamma`)
to another (e.g. `/cache2/gamma`).

# Installing

Recommended setup for some installation directory `${INSTALLDIR}` (e.g.
`${HOME}/software`):

* Add `${HOME}/bin` to your `$PATH`.

* Clone from Git:

        cd ${INSTALLDIR}
        git clone git@github.com:lockss/editautxt     # with SSH key
        git clone https://github.com/lockss/editautxt # without SSH key

* Make a symbolic link:

        cd ${HOME}/bin
        ln -s ${INSTALLDIR}/lockss-gitflow-init/editautxt

# Using

The change applies to one or more AUs designated by their AUIDs. The list of
target AUIDs is typically fed via a text file, one AUID per line, using the
--auids option, but combinations of any number of individual AUIDs with --auid
and any number of AUID files with --auids can be used to build the list of
target AUIDs.

Other than --auid/--auids options, the script accepts four parameters:

* the path to an au.txt file (which can be a copy of a real one, if you want to
  perform the change somewhere else and examine it before making it "live")
* a source repository directory, e.g. `/cache1/gamma`
* a destination repository directory, e.g. `/cache2/gamma`
* the daemon's default repository directory, e.g. `/cache0/gamma`. This is
  needed because the daemon assumes that the first repository directory it gets
  in its configuration (`config.dat`) is special, and AUs in that default
  repository directory do not get an explicit repository line in au.txt.
  
Example to move the AUIDs listed in the file `/tmp/auidstomove` within
`/cache0/gamma/config/au.txt` from `/cache1/gamma` to `/cache2/gamma`,
in a daemon that uses `/cache0/gamma` as its default repository directory: 

    editautxt --auids=/tmp/auidstomove /cache0/gamma/config/au.txt /cache1/gamma /cache2/gamma /cache0/gamma 

Note that the script makes a backup copy of the au.txt file `${AUTXT}` given as
the first argument. It tries `${AUTXT}.1`, `${AUTXT}.2`, etc. until a
never-before-used backup file `${AUTXT}.${n}` is found. The largest value
`${n}` in a directory is the most recent backup.

# Updating

* Pull from Git:

        cd ${INSTALLDIR}/lockss-gitflow-init
        git pull