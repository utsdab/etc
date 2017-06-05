##
## Copyright (c) 1999 PIXAR.  All rights reserved.  This program or
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
## 1001 West Cutting Blvd.
## Richmond, CA  94804
##
## ----------------------------------------------------------------------------
#
# Rat.tcl
#   public interface for shared tcl procedures
#
#

#default sequence remapping function
# supported args:
#      -pad   : number of digits to pad resulting frame number
#      -in    : remapping function domain
#               this argument is used by other functions to give hints
#               regarding sequence length, range, etc.
#      -out   : remapping function range of valid frames

proc fit {args} {
    
    #value of current frame input value
    global f
    set i [lsearch $args "-pad"]
    if {$i != -1} {
	set pad [lindex $args [incr i]]	    
    } else {
	set pad 0	    
    }
    
    set i [lsearch $args "-out"]
    if {$i != -1} {
	set outStartVal [lindex $args [incr i]]
	set outStopVal [lindex $args [incr i]]
    } else {
	return $f    
    }   

    set i [lsearch $args "-in"]
    if {$i != -1} {
	set inStartVal [lindex $args [incr i]]
	set inStopVal [lindex $args [incr i]]
    } else {
	set inStartVal 1
	set inStopVal [expr 1 + [expr $outStopVal - $outStartVal]]  	    
    }   
    
    #remap frame range to file range
    
    set domainLength [expr $inStopVal - $inStartVal]
    set rangeLength [expr $outStopVal - $outStartVal]
    
    set i [lsearch $args "-abyss"]
    if {$i != -1 } {
	set type [lindex $args [incr i]]
	if {$type == "periodic"} {    
	    if { ($f < $inStartVal) || ($f > $inStopVal)} {
		set frame [expr $f - $inStartVal]
		set f [expr $frame % ($domainLength + 1)]
		set f [expr $f + $inStartVal]	
	    }
	}
    }

    if {$f < $inStartVal} {
	set frameNum $outStartVal
    } else {
	if {$f > $inStopVal} {
	    set frameNum $outStopVal
	} else {
	    set frame [expr $f - $inStartVal]
	    if {$domainLength > 0} {
		set frameNum [expr int([expr [expr $frame / $domainLength.0] * $rangeLength])] 
	    } else {
		set frameNum 0
	    }
	    set frameNum [expr $frameNum + $outStartVal]
	}
    }

    return [format %.$pad\d $frameNum]    
}

# FindArg:
# a utility for finding a specific argument from an opaque
# expression.  1st call FindArg -setup op val, then
# regsub the name of a known proc (like txmake) to ::RAT::FindArg,
# then call subst on your expression. Currently we support searching
# for args by index (-index num) or by argument (-argname argvalue).
#
proc ::RAT::FindArg args {
   global ::RAT::priv
   if {[lindex $args 0] == "-setup"} {
	set ::RAT::priv(op) [lindex $args 1]
	set ::RAT::priv(val) [lindex $args 2]
   } else {
   	set result {}
   	switch -- $::RAT::priv(op) {
	   -argname {
	   	set i [lsearch $args $::RAT::priv(val)]
	   	if {$i != -1} {
	   	   incr i
		   set result [lindex $args $i]
	   	}
	   }
	   -index {
	   	set result [lindex $args $::RAT::priv(val)]
	   }
   	}
   	return $result
   }
}

