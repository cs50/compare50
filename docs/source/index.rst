``compare50``
=============

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Contents:

   api

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`api`
.. * :ref:`modindex`
.. * :ref:`search`

Compare50 is a tool for detecting similarity in code that supports well over 300 programming and templating languages. The tool itself is open-source and by design extensible in its comparison methods. There is no need to upload code to an external host, compare50 runs locally from the command-line. As a local tool, compare50 presents its findings in static and interactive HTML files that allow for easy sharing. And it does so blazingly fast, easily comparing 1000 source files within seconds.


Installation
************

First make sure you have Python 3.6 or higher installed. You can download Python |download_python|.

.. |download_python| raw:: html

   <a href="https://www.python.org/downloads/ target="_blank">here</a>

To install compare50 under Linux / OS X:

.. code-block:: bash

    pip install compare50

Under Windows, please |install_windows_sub|. Then install compare50 within the subsystem.

.. |install_windows_sub| raw:: html

   <a href="https://docs.microsoft.com/en-us/windows/wsl/install-win10" target="_blank">install the Linux subsystem</a>

Alternatively you can opt to run compare50 via cli50. Cli50 will in fact pull in a Docker image with compare50 pre-installed. So all you need to do is install and run cli50, and you are then good to go. Please refer to cli50's docs For instructions on how to install.

Usage
*******

To compare two source files, simply run:

Usage::

    compare50 foo.java bar.java

It quickly becomes tedious to type out every file to compare. So instead shell globbing can be used to for instance compare all .java files in the current directory:

Usage::

    compare50 *.java

Compare50 conceptually takes submissions in the form of paths as its command-line arguments. If that path just so happens to be a directory and not a single file, then every file within that directory is grouped together and treated as a single submission. For instance the following compares two directories foo and bar:

Usage::

    compare50 foo bar

Or better yet, everything in the current directory:

Usage::

    compare50 *

Odds are that directories contain files that should not be compared. Say for instance some extraneous `.txt` files. To exclude these, just run compare50 with the optional `-x` (eXclude) argument like so:

Usage::

    compare50 * -x "*.txt"

Do note the quotation marks above. These are necessary as the shell would otherwise glob `*.txt` to every text file in the current directory. This would have compare50 exclude just these files, and not the text files within the submissions themselves.

Sometimes its specific types of files that need to be compared, and in that case it is easier to tell compare50 what to include rather than exclude. To support this compare50 comes with an optional `-i` (Include) argument. The exclude and include argument interact with each other in order. If familiar, this is in similar spirit to a `.gitignore` file, where each line either includes or excludes some files. So let us say we want to compare no other files, but every `.java` file, except `foo.java`. This can be achieved like so:

Usage::

    compare50 * -x "*" -i "*.java" -x "foo.java"

The order of the arguments above is important here. Each include or exclude argument will override the previous. So the above reads as following. Take everything in the current directory and treat it as a submission. Then exclude everything from every submission. Next, once again include every `.java` file. Finally, exclude `foo.java` once more.


Usage::

    usage: compare50 [-h] [-a ARCHIVE [ARCHIVE ...]] [-d DISTRO [DISTRO ...]]
                     [-p PASSES [PASSES ...]] [-i INCLUDE [INCLUDE ...]]
                     [-x EXCLUDE [EXCLUDE ...]] [--list] [-o OUTPUT] [-v]
                     [-n MATCHES] [--profile] [--debug]
                     submissions [submissions ...]

    positional arguments:
      submissions           Paths to submissions to compare

    optional arguments:
      -h, --help            show this help message and exit
      -a ARCHIVE [ARCHIVE ...], --archive ARCHIVE [ARCHIVE ...]
                            Paths to archive submissions. Archive submissions are
                            not compared against other archive submissions, only
                            against regular submissions.
      -d DISTRO [DISTRO ...], --distro DISTRO [DISTRO ...]
                            Paths to distribution files. Contents of these files
                            are stripped from submissions.
      -p PASSES [PASSES ...], --passes PASSES [PASSES ...]
                            Specify which passes to use. compare50 ranks only by
                            the first pass, but will render views for every pass.
      -i INCLUDE [INCLUDE ...], --include INCLUDE [INCLUDE ...]
                            Globbing patterns to include from every submission.
                            Includes everything (*) by default. Make sure to quote
                            your patterns to escape any shell globbing!
      -x EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                            Globbing patterns to exclude from every submission.
                            Nothing is excluded by default. Make sure to quote
                            your patterns to escape any shell globbing!
      --list                List all available passes and exit.
      -o OUTPUT, --output OUTPUT
                            location of compare50's output
      -v, --verbose         display the full tracebacks of any errors
      -n MATCHES            number of matches to output
      --profile             profile compare50 (development only, requires
                            line_profiler, implies debug)
      --debug               don't run anything in parallel, disable progress bar
