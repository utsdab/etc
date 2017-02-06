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
# TORExpression.tcl
#   TCL procedures required to support parameter expressions across
#   TOR applications.   Used by MTOR, Slim, etc.
#
# $Revision: #1 $
#
#

#
# doExpand:
#
#   Called before expanding every slim appearance.
#   Determines whether a particular appearance should
#   be output into the RIB stream.
#
#   Slim makes some attempt at providing an ELEMENTTYPE-specific
#   hint as to whether to expand an appearance into RIB.
#   This hint is in the form of a RIB Attribute indicating
#   that the shader wants to ignore a class of ELEMENTS.
#   Most commonly, this occurs during shadow generation.
#   Only those shaders that modify opacity or displacements
#   are required during shadow generation.
#
#   args:
#   	rib stream
#	    Attribute "visibility" "string transmission" ["shader"]
#
#   returns:
#   	0 - don't expand into RIB
#   	1 - expand into RIB
#
proc doExpand rib {
    global ELEMENTNAME ELEMENTTYPE \
	   INSTANCENAME INSTANCETYPE INSTANCETYPE_FILTER
    
    if [info exists ::INSTANCETYPE_FILTER] {
	if ![info exists ::INSTANCETYPE_FILTER($INSTANCETYPE)] {
	    set newt [GetPref TORExpandMap($INSTANCETYPE)]
	    if [string equal $newt {}] {
		RAT::LogMsg ERROR \
		"doExpand: unknown appearance type: $INSTANCETYPE"
	    } else {
		if !$INSTANCETYPE_FILTER($newt) {
		    #RAT::LogMsg DEBUG \
		    #"doExpand: filtering mapped app type: $INSTANCETYPE"
		    return 0 
		}
	    }
	} else {
	    if !$INSTANCETYPE_FILTER($INSTANCETYPE) {
		    #RAT::LogMsg DEBUG \
		    #"doExpand: filtering app type: $INSTANCETYPE"
		return 0 
	    }
	}
    }
    
    # always expand ribboxes and tclboxes - they
    # can embed their own logic.
    if [string match *box $INSTANCETYPE] { return 1 }

    # always expand ensembles, since they may
    # contain ribboxes and tclboxes
    if {$INSTANCETYPE == "ensemble"} { return 1 }

    if {[string equal $ELEMENTTYPE shadow] ||
                                [string equal $ELEMENTTYPE occlusion]} {
    	set i [string first "displacementbound" $rib]
    	# assume that if displacementbound is provided
    	# that it is nonzero and implies that the shader
    	# should be expanded in shadow generation.
    	if {$i != -1} { return 1 }

        #RAT::LogMsg DEBUG "doExpand for shadow \n\n$rib\n\n"
        set i [string first {"visibility" "int transmission"} $rib]
        if {$i != -1} {
            # modern usage:
            #   Attribute "visibility" "int transmission" [0/1]
            #   Attribute "shade" "string transmissionhitmode" \
            #                                   ["shader" | "primitive"]
            set l [split [string range $rib $i end]]
            set v [lindex $l 3]
            # RAT::LogMsg DEBUG "found vis $v"
            if [string match *1* $v] {
                # it's visible to transmission rays (and shadow maps)
                set i [string first {"shade" "string transmissionhitmode"} $rib]
                if {$i != -1} {
                    set l [split [string range $rib $i end]]
                    set v [lindex $l 3]

                    # ["shader"] | or ["primitive"]
                    if [string match *shader* $v] {
                        # visible to transmission rays && shaded
                        return 1 
                    }
                }
            } 
        } else {
            set i [string first {"visibility" "transmission"} $rib]
            if {$i != -1 } {
                # deprecated as of rps14:
                #   Attribute "visibility" "transmission" \
                #               ["opaque" | "transparent" | "Os" | "shader"]
                set l [split [string range $rib $i end]]
                set v [lindex $l 2]
            } else {
                # deprecated before rps14:
                #   Attribute "render" "string casts_shadows" \
                #               ["Os" | "none" | "opaque" | "shade" ]
                set i [string first {"render" "string casts_shadows"} $rib]
                if {$i != -1} {
                    set l [split [string range $rib $i end]]
                    set v [lindex $l 3]
                }
            }
            if {$i != -1} {
                switch -glob -- $v {
                    *shade* -
                    *Os* { 
                        return 1 
                    }
                }
            } 
	}
        # in shadow or occlusion pass, don't emit shader, we're either 
        # invisible to transmission rays or transmissionhitmode isn't shade
        return 0
    }
    return 1
}

# nb: adaptor now lives in SlimExpression.tcl

# objPrefix:
#   analyze the $OBJNAME value to determine the prefix resulting
#   from an import or reference operation.  Useful in cases where
#   palettes are stored externally and which do refer to multiple
#   copies of the same object.
#
proc objPrefix {} {
    global OBJNAME
    set i [string last : $OBJNAME]
    if {$i == -1} {
	set i [string last _ $OBJNAME]
    }
    if {$i == -1} { return {} }
    return [string range $OBJNAME 0 $i]
}

::RAT::LogMsg DEBUG "TOR Expression Subsystem Loaded"
