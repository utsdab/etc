#!/usr/bin/env python

#
# An example python Tractor login validation script for which connects
# with an ldap server
#
# Copyright (C) 2011-2012 Pixar Animation Studios.  
# The information in this file is provided for the exclusive use of the
# licensees of Pixar.  Such users have the right to use, modify, and
# incorporate this code into other products for purposes authorized
# by the Pixar license agreement, without fee.
#
# PIXAR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT
# SHALL PIXAR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES
# OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
# ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
#

import sys
import ldap

## ------------------------------------------------------------- ##

def main ():

    # This routine expects to receive a userid, challenge, and
    # password on stdin as newline-separated strings:
    # like  "yoda\n12345 abcd\nPW\n"
    #
    # Typically the inbound "password" will actually be a 
    # site-defined hash of the real password and the challenge.
    #

    user = raw_input()
    challenge = raw_input()
    pw_hash = raw_input()

    domain = ".local"

    serveruri="ldap://ldap.%s" % domain
    ldsrvr = ldap.initialize(serveruri)

    who = "uid=%s,ou=people,o=%s" % (user, domain)
    cred = pw_hash.strip()
    rc = 0

    try:
        ldsrvr.bind_s(who, cred)
    except ldap.LDAPError, error_message:
        who = "uid=%s,ou=sysaccounts,o=pixar.com" % user
        try:
            ldsrvr.bind_s(who, cred)
        except ldap.LDAPError, error_message:
            rc = 1

    del(ldsrvr)
    return rc

## ------------------------------------------------------------- ##

if __name__ == "__main__":

    rc = main()

    if 0 != rc:
        sys.exit(rc)
