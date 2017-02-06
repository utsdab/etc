#!/usr/bin/env python

#
# An example Tractor login validation script for classic Linux-style
# /etc/passwd entries.
#

#
# Copyright (C) 2010 Pixar Animation Studios.
#
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
import pwd
import crypt

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

    try:
        p = pwd.getpwnam(user)
    except KeyError:
        return 1  # unknown user

    cpw = p.pw_passwd

    salt = cpw[0:2]  # salt for new crypt must match original

    x = crypt.crypt( pw_hash, salt )

    if cpw == x:
        # success! password crypts match
        return 0
    else:
        # fail!  crypt not a match
        return 1

## ------------------------------------------------------------- ##

if __name__ == "__main__":

    rc = main()

    if 0 != rc:
        sys.exit(rc)
