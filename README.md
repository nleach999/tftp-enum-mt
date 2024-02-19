# TFTP File Enumerator

I made this after being frustrated with the available TFTP file enumerator provided by `nmap`.  If you want to enumerate a large list,
it would be a bit cumbersome to do so with the `nmap` NSE script.


This version will do a multi-threaded enumeration so it can chew through a large list quite fast.  It also keeps a state file for each
host/file list so that it can resume near where the program last ended.

I spent only a few hours hacking this together.  YMMV


# Options

`-h` or `--help` - Show the option help.
`-H` or `--host` - The host name or IP of the machine hosting the TFTP service to enumerate.
`-p` or `--port` - The TFTP port (default: 69)
`-l` or `--list` - A path to a list of filenames used to enumerate the TFTP service.
`-c` or `--chunk` - The divisor size of the filename list given to each thread to enumerate (default: 1024)
`-t` or `--threads` - The number of concurrent threads used during enumeration (default: 3)
`-o` or `--outdir` - The location where downloaded files will be stored (default: .)
`--timeout` - The number of seconds to wait for a transfer timeout (default: 60)
