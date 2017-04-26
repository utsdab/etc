##              
## Copyright (c) 2008 PIXAR.  All rights reserved.  This program or
## documentation contains proprietary confidential information and trade
## secrets of PIXAR.  Reverse engineering of object code is prohibited.
## Use of copyright notice is precautionary and does not imply
## publication.
##  
##                      RESTRICTED RIGHTS NOTICE
##  
## Use, duplication, or disclosure by the Government is subject to the
## following restrictions:  For civilian agencies, subparagraphs (a) through
## (d) of the Commercial Computer Software--Restricted Rights clause at
## 52.227-19 of the FAR; and, for units of the Department of Defense, DoD
## Supplement to the FAR, clause 52.227-7013 (c)(1)(ii), Rights in
## Technical Data and Computer Software.
##  
## Pixar
## 1200 Park Ave
## Emeryville, CA  94608
##      
#
# RMSCommands $Revision: #1 $
#
namespace eval ::RMS {

proc CompileShader filename {
    set compileCmd [GetPref ShaderCompiler]
    if ![string equal $compileCmd {}] {
        set i [lsearch $compileCmd %f]
        if {$i != -1} {
            set retstr {}
            set ncompileCmd [lreplace $compileCmd $i $i $filename]
            set ncompileCmd [linsert $ncompileCmd 0 exec]
            catch $ncompileCmd msg
            if {-1 != [string first "NOT COMPILED" msg]} {
                ::RMS::LogMsg ERROR $msg
                error $msg
            } else {
                # We expect an assortment of WARNINGS of this sort:
                # Warning: Possible use of uninitialized
                # Currently shader doesn't support -woff capability.
                # The unfiltered msg is available in debug-mode.
                ::RMS::LogMsg DEBUG $msg
                foreach l [split $msg \n] {
                    if {$l == {}} continue
                    if {-1==[string first "Possible use of uninitialized" $l]} {
                        append retstr "$l\n"
                    }
                }
                if [GetPref ShaderCompilerCleanup 1] {
                    if {[catch {file delete $filename} msg]} {
                        ::RMS::LogMsg ERROR $msg
                    } else {
                        ::RMS::LogMsg DEBUG "deleted $filename"
                    }
                }
            }
            return $retstr; # no error
        }
    }
    error "Bogus ShaderCompiler pref: $compileCmd"
}

}

::RMS::LogMsg DEBUG "RMS Commands Installed"

