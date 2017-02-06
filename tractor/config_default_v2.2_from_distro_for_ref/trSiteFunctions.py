#
# Site-specific python implementations of optional scripting functions
# ----------------------------------------------------------------
# Copyright (C) 2012 Pixar Animation Studios.
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
# ----------------------------------------------------------------
#

#
# python script based login password management.  See the Tractor Administration
# documentation for a detailed discussion of the steps required to
# integrate the Tractor login scheme with site security policies.
#
# 

def trSitePasswordHash (passwd, challenge):
    # By default, Tractor ignores passwords completely,
    # and login names are only used for basic event tracking and to
    # restrict some UI actions.  The return value of this function,
    # below, should be the Python 'None' value when the default
    # password-ignore behavior is desired.
    #
    # Otherwise, this function should return a string that is the
    # site-customized encoding of the user's typed-in plaintext password,
    # possibly also incorporating the given server-supplied one-time
    # random challenge string.  The matching site-specific server-side
    # handling of this encoded string MUST be implemented in the login
    # validator file as defined in the crews.config file.

    # return None   # passwords are ignored (default factory setting)
    # or
    # return your_custom_encoding( passwd, challenge )

    return None

