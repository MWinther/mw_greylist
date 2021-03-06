#!/usr/local/bin/python

import sys, os, getopt, socket, string

def check_rbl_like (hostname, 
                    root_name = "blackholes.mail-abuse.org", 
                    yes_addr = "127.0.0.2",
                    do_log = 0):
    
    addr = socket.gethostbyname(hostname)
    if do_log: print "Host %s resolves to %s" % (hostname, addr)
    addr_parts = string.split(addr, '.')
    addr_parts.reverse()
    check_name = "%s.%s" % (string.join(addr_parts, '.'), root_name)
    try:
        check_addr = socket.gethostbyname(check_name)
    except socket.error:
        check_addr = None
    if do_log: print "RBL returns %s" % check_addr
    if check_addr == yes_addr:
        return 1
    else:
        return 0

def check_rbl(hostname):
    return check_rbl_like (hostname)

def check_dul(hostname):
    return check_rbl_like (hostname, "dialups.mail-abuse.org", "127.0.0.3")

def check_rss(hostname):
    return check_rbl_like (hostname, "relays.mail-abuse.org", "127.0.0.2")

def usage(argv0):
  print "%s [--help]" % argv0

def main(argv, environ):
  alist, args = getopt.getopt(argv[1:], "", ["help"])

  for (field, val) in alist:
    if field == "--help":
      usage (argv[0])
      return

  for host in args:
    print "RBL: %s" % (check_rbl(host))
    print "DUL: %s" % (check_dul(host))
    print "RSS: %s" % (check_rss(host))

if __name__ == "__main__":
  main (sys.argv, os.environ)
    
