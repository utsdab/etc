# ------------------------------------------------------------------------------
#
# Copyright (c) 2006-2012 Pixar Animation Studios. All rights reserved.
#
# The information in this file is provided for the exclusive use of the
# software licensees of Pixar.  It is UNPUBLISHED PROPRIETARY SOURCE CODE
# of Pixar Animation Studios; the contents of this file may not be disclosed
# to third parties, copied or duplicated in any form, in whole or in part,
# without the prior written permission of Pixar Animation Studios.
# Use of copyright notice is precautionary and does not imply publication.
#
# PIXAR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT
# SHALL PIXAR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES
# OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
# ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
#
# Pixar
# 1200 Park Ave
# Emeryville CA 94608
#
# ------------------------------------------------------------------------------
#
# RMSExpression $Revision: #1 $
#
# This file embodies the state and logic associated the RfM and Slim's
# scripting capabilities.  The basic idea is that there are a number
# of state variables plus a collection of procedures that operate
# on these.  RfM/Slim automatically update the state variables according
# to the the expression context.  Certain state variables are only
# guaranteed to be valid within a particular expression context.
# For example, the PARMNAME state variable is only valid when the
# EXPRESSION_CONTEXT includes "param".  Expression contexts are nested
# and we maintain the stack of CONTEXTS herein.
# Known EXPRESSION_CONTEXTs are:
#  "riopt", "riattr", "toropt", "torattr", 
#  "shader", "prim", "param", 
#  "txmakepass",  "renderpass", "cachepass", 
#  "clientscriptpass", "commandpass", "cleanuppass", 
#  "compilepass", "populatephase"
# Rather than search upwards through the EXPRESSION stack it may be
# more useful to access well-known state variables armed with the special
# knowledge of the nesting.  Specifically, SHADER and PARM contexts
# aren't nested.  
#
# When RfM and Slim are communicating, the HandleSyncEvent message
# is delivered to Slim to ensure it is offered the leading hand
# if it desires to follow a Maya session's travels across scene
# and project changes.
#
# One critical feature of this file is to implement pass reference
# scripting.  Passes are referred to through expressions and this
# allows us to change the expression results according to the executiong
# context requirements.  For example, the passref validity table
# is used to convert a reference to a renderpass output to a concrete
# filename.  The validity table embodies validity of one
# class of renderpass references relative to another render pass.
# When the table tells us that a fileref is invalid, we can
# return an empty file reference.
# 
# And this is only one example of the potential of expression-based
# representations in your pipeline. Here's another: we can monitor
# all pass reference requests that go by in a window of time.  From
# this we can infer the need for additional rendering or command passes.
# This idea is embodied elsewhere: e.g. RfMWorkExpression.tcl.
#
# Note on coding conventions:
#   Procedures and variables that begin with capital letters are 
#   intended to be for public consumption. We expect to support these 
#   entrypoints across multiple releases, so you can override them in 
#   your own scripting extensions, etc. Those entrypoints that begine
#   with _ or lowercase letters are to be treated as file-private.
#   These may change from release to release, so tread carefully.
#   Some of the uncapitalized names are implemented on the c-side.
#
namespace eval ::RMSExpression {

    proc HandleSyncEvent {event args} {
        ::RMS::LogMsg DEBUG "RMSExpression HandleSyncEvent: $event $args"
        if {[llength $args] == 1} {
            set args [lindex $args 0]
        }
        set err [catch [list _handleSyncEvent $event $args] result]
        if {$err == 0} {
            set err [catch [list HandleSyncEventNotice $event $result] result]
        } else {
            ::RMS::LogMsg ERROR "RMSExpression: $result"
            set result ""
        }
        ::RMS::LogMsg DEBUG "RMSExpression returning $result"
        return -code $err $result
    }

    # override this procedure via the usual .ini/LoadExtension mechanism
    # to provide customized behaviour in a site-specific manner
    proc HandleSyncEventNotice {event arglist} {
        # Use this syntax to prevent further handling of the message:
        # return -code 3 $message
        # Use this syntax to signal an error in the handling of the message:
        # return -code 1 $errorMessage
        # Or this syntax (equivalent to the option -code 0) to let the
        # the message pass through to further handling
        return $arglist
    }

    proc _init {} {
        # legacy varnames:  PROJ, ARGS, CLASS, CHAN, SRC, APPLOC
        variable _deprecatedVars {
            PROJ ARGS CLASS CHAN SRC APPLOC DSPYBASE
        }
        variable _staticVars {
            APPNAME APPVERS APPLOC
            HOST PID DSPYPORT USER HOME
        }
        variable _workspaceVars {
            WSCLASS FILE FILEDIR FILEBASE SCENE STAGE STAGECTX
            LAYERLIST
            PROJ
            RMSPROJ RMSPROJ_SHARING
            RMSPROD RMSPROD_GLOBAL 
        }
        variable _passVars {
            PASSID PASSHANDLE PASSCLASS CLASS CAMERA CREW FLAVOR CAMERAFLAVOR
        }
        # _basePatternVars are variables that may appear in BASEPATTERN
        variable _basePatternVars {
            LAYER CAMERA CAMERAFLAVOR JOBSTYLE JOBID JOBDATETIME JOBTIME
            RENDERTYPE
            SCENE PASSID DSPYID DSPYCHAN BAKECHAN
            PASSCLASS EXT 
            F F0 F1 F2 F3 F3 F4 F5 F6 F7 FF
        }
        
        # _dynamicVars are burned into the encapsulation of state
        # beware that no _workspaceVars get into here.
        variable _dynamicVars {
            JOBSTYLE JOBID JOBDATETIME JOBTIME TIMESTAMP LAYER RENDERTYPE
            RIBPATH SHADERPATH IMAGEPATH DATAPATH TEXTUREPATH 
            PASSID PASSCLASS CLASS PASSHANDLE
            CAMERA CREW FLAVOR CAMERAFLAVOR DEFAULTCAMERA PASSLAYER
            CMD CMDARGS ARGS
            DSPYID DSPYCHAN DSPYTYPE CHAN
            BAKECHAN BAKECHANNELS
            DENOISECHANNELS
            MAPNAME ASSETNAME BASE
            SRCFILE SRC
            EXT EXT_NO_DOT
            FRAMEFORMAT FRAME F F0 F1 F2 F3 F4 F5 F6 F7 F8 FF
            FIRSTFRAME LASTFRAME FPS PCT
            OBJPATH OBJNAME LIGHTNAME LIGHTARGS LIGHTHANDLE
            SHADERGROUP SHADERHANDLE SHADERNAME SHADERTYPE BOUNDCOSHADERS
            INSTANCETYPE INSTANCESLOT INSTANCENAME INSTANCEID NAMESPACE
            PARMNAME PARMTYPE PARMSUBTYPE PARMVAL
        }
        set _dynamicVars [concat $_dynamicVars [GetPref SiteScriptingVars]]

        variable EXPRESSION_CONTEXT {}; # (set above: riopt, riattr, ...)
        variable _exprCtxStack {}; # tracks EXPRESSION_CONTEXT
        variable _resetCallbacks {}; # list of procs to call on reset
        variable _stateMap; # maps abitrary key (usually filename) to state
        array set _stateMap {}
        variable _localizedPaths; # maps FILE to localized pathref
        array set _localizedPaths {}
        variable _assetrefFullpaths 0;
        variable _assetnmSeparator "_"
        variable _assetnmInvalidCharMap {}
        variable _memoizeFileExists
        array set _memoizeFileExists {}

        foreach v [concat $_staticVars $_workspaceVars $_dynamicVars] {
            if {![info exists ::RMSExpression::$v]} {
                variable $v {}
            }
        }

        _resetAssetnamePkg [GetPref AssetnameFullpaths]
        _resetEnvVars

        ResetDynamicVars
    }

    proc PushExpressionContext ctx {
        # NB: expression contexts currently shouldn't / don't prevent
        # side effects:  we don't encapsulate / restore _dynamicVars
        variable EXPRESSION_CONTEXT; variable _exprCtxStack
        lappend _exprCtxStack $ctx
        set EXPRESSION_CONTEXT $ctx
    }

    proc PopExpressionContext ctx {
        variable EXPRESSION_CONTEXT; variable _exprCtxStack
        set _exprCtxStack [lrange $_exprCtxStack 0 end-1]
        set EXPRESSION_CONTEXT  [lindex $_exprCtxStack end]
    }

    proc GetExpressionContextStack {} {
        variable _exprCtxStack
        return $_exprCtxStack
    }

    proc SetApplication {appname appvers apploc pid host dspyport} {
        variable APPNAME; variable APPVERS;
        variable APPLOC; variable PID;
        variable HOST; variable DSPYPORT;
        set APPNAME $appname
        set APPVERS $appvers
        set APPLOC $apploc
        set PID $pid
        set HOST $host
        set DSPYPORT $dspyport
    }

    proc SetUser {user home} {
        variable USER; variable HOME;
        set USER $user
        set HOME $home
    }

    proc SetJobTime {} {
        variable JOBDATETIME; variable JOBTIME;
        set sec [clock seconds]
        set JOBTIME [GetTimeStamp JobTime $sec]
        set JOBDATETIME [GetTimeStamp JobDateTime $sec]
    }

    proc SetJob {id jobstyle layer rendertype layerlist fullpaths} {
        variable JOBID; variable JOBSTYLE; 
        variable LAYER; variable LAYERLIST;
        variable RENDERTYPE;
        variable JOBDATETIME; variable JOBTIME;
        if {$JOBTIME eq ""} {
            SetJobTime
        }
        set JOBID $id
        set JOBSTYLE $jobstyle
        set LAYER $layer
        set LAYERLIST $layerlist
        set RENDERTYPE $rendertype

        ::RMS::LogMsg DEBUG "SetJob: $JOBID $JOBSTYLE $JOBTIME"

        # TimeStamp is legacy, JOBTIME, JOBDATETIME can be decorrelated from 
        # SetJob making it easier for alfred script generation, etc.
        set sec [clock seconds]
        SetTimeStamp $sec
        _resetAssetnamePkg $fullpaths
    }

    proc GetAssetRefRoot {} {
        variable _assetrefFullpaths
        variable RMSPROD
        if $_assetrefFullpaths { 
            return ""
        } else {
            return $RMSPROD; # which equals $RMSPROJ when PRODEQUALPROJS
        }
    }

    proc AddAssetRefPattern {key pat extcls} {
        # extends the ini-based tables for assetname patterns and extensions
        # this makes it possible to override the defaults on a per-pass/dspy
        # basis. NB: extcls is not an extension, but rather and extension class
        # Caller should provide, e.g. mayaiff, not .iff.
        variable _assetnmPatternMap
        variable _assetnmExtensionMap
        variable _assetnmInvalidCharMap
        set ext ""
        set fixed_key [string map $_assetnmInvalidCharMap $key]
        if {$extcls ne "" && $extcls ne "null"} {
            if [info exists _assetnmExtensionMap($extcls)] {
                set ext $_assetnmExtensionMap($extcls)
                set _assetnmExtensionMap($fixed_key) $ext
            } else {
                ::RMS::LogMsg WARNING \
                    "AssetnamePattern: unknown extcls: $extcls"
            }
        }
        if {![GetPref AssetnameDefeatOverrides]} {
            if {$pat eq ""} {
                # allow for removal of pattern if it's set back to empty
                if [info exists _assetnmPatternMap($fixed_key)] {
                    unset _assetnmPatternMap($fixed_key)
                }
            } else {
                if [info exists _assetnmPatternMap($fixed_key)] {
                    if {$pat ne $_assetnmPatternMap($fixed_key)} {
                        ::RMS::LogMsg DEBUG \
                            "Overriding AssetnamePattern for $key: $pat ($ext)"
                        set _assetnmPatternMap($fixed_key) $pat
                    }
                } else {
                    set _assetnmPatternMap($fixed_key) $pat
                }
            }
        }
    }

    proc GetTimeStamp { {fmt JobDateTime} {sec {}} } {
        variable TIMESTAMP
        if {$sec eq ""} {
            set sec [clock seconds]
            SetTimeStamp $sec
        }
        if {$fmt ne ""} {
            # perhaps it's a PrefName?
            set prefnm ${fmt}Format; # JobTimeFormat, JobDateTimeFormat
            set result [GetPref $prefnm ""]
            if {$result ne ""} {
                # aha, we found a pref with a value
                set fmt $result
            }
            # else we assume the user wants to talk
            # in tcl time format notation
        } 
        if {$fmt eq ""} {
            return $TIMESTAMP
        } else {
            return [clock format $sec -format $fmt]
        }
    }

    proc SetTimeStamp { {sec {}} } {
        variable TIMESTAMP
        if {$sec eq ""} {
            set sec [clock seconds]
        }
        set TIMESTAMP [clock format $sec]
    }

    proc SetWorkspace {wscls proj file base 
                       {basepattern {}} {stagectx -1} } {
        # update workspace-related scripting variables
        # required inputs:
        #   wsclass: usually "primary", "AssetRef" if 'file referencing' in play
        #   proj:  the project dir defines the workspace context
        #   file:  the file within the workspace from which asset references
        #           arise.  aka: SCENE
        #   base:  the basename defined within file for output refs
        #   basepattern: a substitable pattern to produce base... when provided
        #       this will override any value provided for base
        variable WSCLASS
        variable RMSPROD; variable RMSPROD_GLOBAL
        variable RMSPROJ; variable RMSPROJ_SHARING; variable PROJ;
        variable FILE; variable FILEBASE; variable FILEDIR; 
        variable SCENE; variable STAGE; variable STAGECTX;
        variable BASE; variable BASEPATTERN; variable DSPYBASE; 
        variable _localizedPaths
        variable _basePatternVars
        foreach v  $_basePatternVars {
            variable $v
        }

        if {$wscls eq "primary"} {
            set RMSPROD [workspace GetProdDir]
            set RMSPROD_GLOBAL [workspace GetProdGlobalDir]
            set RMSPROJ_SHARING [workspace GetProjSharingDir]
            if {$RMSPROD eq ""} {
                # for asset relativization against RMSPROD, we
                # cause RMSPROD to fallback to RMSPROJ-style relative.
                set RMSPROD $proj
                set RMSPROD_GLOBAL {}
            }
            array unset _localizedPaths
        }

        set before "$RMSPROJ/$FILE/$BASE/$STAGECTX"
        set WSCLASS $wscls
        set RMSPROJ $proj
        set PROJ $proj; # legacy
        set FILE $file
        set FILEBASE [_basename $FILE]; # /a/b/c.ext -> c

        if {[info exists _localizedPaths($FILE)]} {
            set FILEDIR $_localizedPaths($FILE)
        } else {
            set FILEDIR [file dirname [workspace LocalizePath $FILE]]
            set _localizedPaths($FILE) $FILEDIR
        }
        if {$FILEDIR eq "."} { 
            set FILEDIR ""
        }
        ::RMS::LogMsg DEBUG "FILE: $FILE -> FILEDIR: $FILEDIR"

        # setup STAGE
        if {$stagectx != -1} {
            set STAGECTX $stagectx
        }
        set SCENE $FILEBASE
        set strategy [GetPref AssetStageStrategy]
        if {$strategy eq ""} {
            set strategy file
        }
        set callback StageStrategyCB_$strategy
        set STAGE [$callback $proj $file]

        # setup BASE, DSPYBASE: may depend upon STAGE
        if {$basepattern ne ""} {
            set BASEPATTERN $basepattern
        } 
        if {$base ne ""} {
            set BASE [file tail $base]; # base should always be "pathless"
        } else {
            set BASE [subst $BASEPATTERN]
        }
        # base should always be "pathless"
        # so if we ended up with leading '/', strip it off
        set BASE [string trimleft $BASE "/"]

        set DSPYBASE $BASE

        set after "$RMSPROJ/$FILE/$BASE/$STAGECTX"
        if ![string equal $after $before] {
            ::RMS::LogMsg DEBUG \
                "SetWorkspace: WSCLASS:$WSCLASS PROJ:$RMSPROJ FILE:$FILE SCENE:$SCENE BASE:$BASE -> STAGE:$STAGE (STAGECTX: $STAGECTX)"
        }
    }

    # begin StageStrategyCB: see comments in RMS.ini
    #
    # Callbacks for computing $STAGE. Which one is called is controlled
    # by the value of AssetStageStrategy and the common and previously defined
    # values are below. The intention is you may define your own callback and
    # set AssetStageStrategy accordingly. This callback is excuted after all
    # the other project-related RMSExpression variables have been set.

    proc StageStrategyCB_file {proj file} {
        # produce STAGE based on filename
        # (lighting/woody_final.ma -> woody_final)
        variable FILEBASE; variable STAGECTX
        if {$STAGECTX ne ""} {
            return ${FILEBASE}_${STAGECTX}
        } else {
            return $FILEBASE
        }
    }

    proc StageStrategyCB_fileProjRel {proj file} {
        # produce STAGE uniqueified by subpath below RMSPROJ coupled with 
        # filename.  (lighting/woody_final.ma -> lighting_woody_final)
        variable FILEDIR; variable FILEBASE; variable STAGECTX;
        return [join [concat [split $FILEDIR /] $FILEBASE $STAGECTX] _]
    }

    proc StageStrategyCB_fileStripVersion {proj file} {
        # produce STAGE from filename, stripped of versioning
        # information according to AssetStripVersionExpr
        # lighting/woody_final_v1 -> woody_final
        variable FILEBASE; variable STAGECTX
        set rex [GetPref AssetStripVersionExpr]
        set result $FILEBASE; # in case regsub fails
        regsub $rex $FILEBASE "" result
        if {$STAGECTX ne ""} {
            return ${result}_${STAGECTX}
        } else {
            return $result
        }
    }

    proc StageStrategyCB_proj {proj file} {
        # produce STAGE from project name
        return [_basename $proj]
    }

    proc StageStrategyCB_env {proj file} {
        # produce stage from user environment... use with care as
        # the environments of multiple apps (RfM, Slim) may be difficult to
        # synchronize
        global env
        if {[info exists env(RMSSTAGE)]} {
            return $env(RMSSTAGE)
        } elseif {[info exists env(STAGE)]} {
            return $env(STAGE)
        } else {
            return untitled
        }
    }

    proc StageStrategyCB_pref {proj file} {
        # produce stage from user pref state... Use with care as
        # the pref state of multiple apps (RfM, Slim) may be difficult to
        # synchronize
        set stage [GetPref "RMSSTAGE" _nocreate]
        if {$stage ne ""} {
            return $stage
        } else {
            return untitled
        }
    }

    # end StageStrategyCB -----------------------------------------

    proc SetDefaultCamera {camera} {
        variable DEFAULTCAMERA
        variable _assetnmInvalidCharMap
        set fixedcam [string map $_assetnmInvalidCharMap $camera]
        set DEFAULTCAMERA $fixedcam
    }

    proc SetPass {passhandle passclass camera crew flavor camflavor args} {
        variable _assetnmInvalidCharMap
        set fixedcam [string map $_assetnmInvalidCharMap $camera]
        variable PASSHANDLE $passhandle
        variable PASSCLASS $passclass
        variable CLASS $passclass
        variable CAMERA $fixedcam
        variable CREW $crew
        variable FLAVOR $flavor
        variable CAMERAFLAVOR $camflavor
        variable PASSID
        variable PASSLAYER
        variable _assetnmSimplifyExpr
        SetDspy {} {} {}
        if {$PASSHANDLE ne ""} {
            set PASSID $PASSHANDLE
        } else {
            set pat [GetAssetnamePattern passhandle]
            set passid [Interpolate $pat]
            regsub -all $_assetnmSimplifyExpr $passid "" passid
            set PASSID $passid
        }
        array set amap $args
        if [info exists amap(-layer)] {
            set PASSLAYER $amap(-layer)
        } else {
            set PASSLAYER ""
        }
    }

    proc SaveState {key {state {}}} {
        variable _stateMap
        if {$state ne {}} {
            set _stateMap($key) $state
        } else {
            set _stateMap($key) [Encapsulate _dynamicVars]
        }
    }

    proc GetState {key} {
        variable _stateMap
        set result {}
        if {[info exists _stateMap($key)]} {
            set result $_stateMap($key)
        }
        return $result
    }

    proc SetCmd {cmdname cmdargs} {
        variable CMD; variable CMDARGS; variable ARGS
        set CMD $cmdname; 
        set CMDARGS $cmdargs; set ARGS $cmdargs
    }

    proc SetTimeContext {firstframe lastframe fps} {
        variable FIRSTFRAME; variable LASTFRAME; variable FPS;
        set FIRSTFRAME $firstframe
        set LASTFRAME $lastframe
        set FPS $fps
    }

    proc SetFrame f {
        variable FIRSTFRAME; variable LASTFRAME; variable PCT;
        variable F; variable FF; variable FRAME; 
        variable F0; variable F1; variable F2;
        variable F3; variable F4; variable F5;
        variable F6; variable F7; variable F8;
        variable FRAMEFORMAT
        set FF {} 
        if {[string eq $f job] || $f <= -3000} {
            foreach varnm {FRAME F F0 F1 F2 F3 F4 F5 F6 F7 F8} {
                set $varnm job
            }
            set PCT 0
        } else {
            # f is a float to support subframe motion
            set PCT [expr $f / ($LASTFRAME - $FIRSTFRAME + 1.0)]
            set fi [expr int($f)]
            set fr [expr int(100 * ($f - $fi))]
            if {$fr > 0 && $fr < 100} {
                # FF is the intra-frame pct. Used for, e.g., subframe sampling.
                set FF [format ".%02d" $fr]
            }
            set F [format "%01d" $fi]
            set F0 $F
            set F1 $F
            set F2 [format "%02d" $fi]
            set F3 [format "%03d" $fi]
            set F4 [format "%04d" $fi]
            set F5 [format "%05d" $fi]
            set F6 [format "%06d" $fi]
            set F7 [format "%07d" $fi]
            set F8 [format "%08d" $fi]
            set FRAME [subst $FRAMEFORMAT]; 
                # NB: FRAMEFORMAT can be empty -> no frame numbers in filename
        }
    }

    proc SetDspy {id chan type} {
        variable _assetnmInvalidCharMap
        set fixed_id $id
        set fixed_chan $chan
        # Only strip illegal characters out of id or chan if it isn't a tcl var
        # which would later be substed away
        if ![string match "\${*}" $id] {
            set fixed_id [string map $_assetnmInvalidCharMap $id]
        }
        if ![string match "\${*}" $chan] {
            set fixed_chan [string map $_assetnmInvalidCharMap $chan]
        }
        variable DSPYID $fixed_id
        variable DSPYCHAN $fixed_chan
        variable CHAN $fixed_chan
        variable DSPYTYPE $type
    }

    proc SetShaderGroup {shadergroup} {
        variable SHADERGROUP
        variable LIGHTHANDLE
        set SHADERGROUP $shadergroup
        set LIGHTHANDLE $shadergroup
    }

    proc SetShader {shadertype shadername shaderhandle boundcoshaders} {
        variable SHADERTYPE $shadertype
        variable SHADERNAME $shadername
        variable SHADERHANDLE $shaderhandle
        variable BOUNDCOSHADERS
        variable NAMESPACE
        # don't allow vestigal NAMESPACE - it gets set in SetSlimInsatnce
        set NAMESPACE {};
        set len [llength $boundcoshaders]
        if $len {
            # this var is unique:  it's actually a full decl/value pair
            # appropriate for a RIB Box parameterlist.
            set BOUNDCOSHADERS "\"string\[$len\] __boundcoshaders\" \["
            set i 0
            foreach coshader $boundcoshaders {
                if {$i > 0} {
                    append BOUNDCOSHADERS " "
                }
                append BOUNDCOSHADERS "\"$coshader\""
                incr i
            }
            append BOUNDCOSHADERS "\]"
        } else {
            set BOUNDCOSHADERS {}
        }
    }

    proc SetSlimInstance {type slot name id {nmspace {}}} {
        variable INSTANCETYPE $type
        variable INSTANCESLOT $slot
        variable INSTANCENAME  $name
        variable INSTANCEID $id
        variable NAMESPACE $nmspace
    }

    proc SetParameter {parmname parmtype parmsubtype parmval} {
        variable PARMNAME $parmname
        variable PARMTYPE $parmtype
        variable PARMSUBTYPE $parmsubtype
        variable PARMVAL $parmval
    }

    proc SetObject {objpath objname} {
        variable OBJPATH $objpath
        variable OBJNAME $objname
    }

    proc SetLight {lightname args} {
        variable LIGHTNAME $lightname
        variable LIGHTARGS $args
        variable LIGHT
        array set LIGHT $args
    }

    proc SetSrcFile src {
        variable SRC $src; 
        variable SRCFILE $src
    }

    proc SetVar {varnm varval} {
        set ::RMSExpression::$varnm $varval
    }

    proc GetVar {varnm} {
        if [info exists ::RMSExpression::$varnm] {
            return [set ::RMSExpression::$varnm]
        } else {
            ::RMS::LogMsg ERROR "RMSExpression::GetVar $varnm doesn't exist"
            return {}
        }
    }

    proc Interpolate str {
        set result [namespace eval ::RMSExpression [list subst $str]]
        return $result
    }

    proc Encapsulate { {varlistnm _dynamicVars} } {
        # serializer for the state described by $varlistnm
        variable $varlistnm
        set state {}
        foreach varnm [lsort [set $varlistnm]] {
            lappend state [list $varnm [set ::RMSExpression::$varnm]]
        }
        return $state
    }

    proc Instantiate {state} {
        # de-serializer for $state
        foreach e $state {
            foreach {varnm varval}  $e {
                SetVar $varnm $varval
            }
        }
    }

    proc GetAssetOutputPath {key args} {
        variable _assetnmLocatorMap
        variable ASSETNAME; variable F0; variable FRAME
        variable RMSPROJ
        set oldanm $ASSETNAME
        set oldf $F0
        set ASSETNAME ""
        array set amap $args
        if [info exists amap(-frame)] {
            SetFrame $amap(-frame)
        } else {
            SetVar FRAME ""
        }
        if ![info exists _assetnmLocatorMap($key)] {
            ::RMS::LogMsg WARNING "GetAssetOutputPath key:$key is unknown"
            set result ""
        } else {
            set result $_assetnmLocatorMap($key)
            array set amap $args
            if [info exists amap(-resolve)] {
                set result [_fullyResolve $result]
                set result [file join $RMSPROJ $result]
            }
        }
        if {$FRAME eq ""} {
            if {"/" eq [string index $result end-1]} {
                # convert potential /usr/local/foo// to /usr/local/foo
                set result [string range $result 0 end-1]
            }
        }
        set ASSETNAME $oldanm
        SetFrame $oldf
        return $result
    }

    proc GetAssetnamePattern key {
        variable _assetnmPatternMap
        if ![info exists _assetnmPatternMap($key)] {
            return $_assetnmPatternMap(_default)
        } else {
            return $_assetnmPatternMap($key)
        }
    }

    proc GetAssetnameExtension key {
        variable _assetnmExtensionMap
        if ![info exists _assetnmExtensionMap($key)] {
            return ""
        } else {
            return $_assetnmExtensionMap($key)
        }
    }

    proc AssetRef args {
        # Here is the primary entrypoint for asset reference generation
        # returns a fully-expanded string representation of
        # an asset for use in, e.g., RIB files, alfred scripts, etc.
        #
        # Required Args:
        #   -ref nm 
        #     <or>
        #   -cls key (source for ASSETNAME pattern)
        # Optional Args:
        #   -assetnmpat val (explicit ASSETNAME pattern, nees cls for output)
        #   -refproj (the project context from whence the ref comes)
        #   -reffile file (the filename context from whence the ref comes)
        #   -fullpath 0/1 (return a full or relative pathname)
        #   -stripext 0/1 (to be deprecated?)
        #   -simplify 0/1 (default 1)
        #   -createdir 0/1 (default 0)
        #   -verbose 0,1,2 (default 0)
        #   -handle h (sets HANDLE) 
        #   -id idstr 
        #   -VAR value  (sets VAR, where VAR is like CAMERA, etc...)
        #   -return oneassetref/bothassetrefs
         
        variable BASE; variable FILE; variable PASSID
        variable RMSPROJ; variable RMSPROD
        variable _assetrefFullpaths;
        variable _assetnmPatternMap
        variable _assetnmExtensionMap
        variable _assetnmInvalidCharMap
        variable _assetnmLocatorMap
        variable _assetnmSeparator
        variable _assetnmSimplifyExpr

        set invoc "AssetRef $args"
        # debugging LogMsg at the end refers to $invoc

        set fullpath $_assetrefFullpaths
        set createdir 0
        set cls "unset"
        set assetnmpat ""
        set id ""
        set stripext 0
        set simplify 1
        set assetref "unset"
        set refproj $RMSPROJ
        set reffile $FILE
        set verbose 0
        set return "oneassetref"
        set result {}
        set base $BASE
        set amap(-HANDLE) undefined
        foreach {nm val} $args {
            set i [lsearch  {-handle -fullpath -createdir -cls -assetnmpat \
                                -stripext -id -simplify -return \
                                -ref -refproj -reffile \
                                -verbose \
                               } $nm]
            if {$i == -1} {
                set amap($nm) $val
            } else {
                switch -- $nm {
                    -handle {
                        set amap(-HANDLE) $val; # send to SetVar, below
                    }
                    -fullpath {
                        set fullpath $val
                    }
                    -createdir {
                        set createdir $val
                    }
                    -cls {
                        set cls $val
                    }
                    -assetnmpat {
                        set assetnmpat $val
                    }
                    -return {
                        set return $val
                    }
                    -id {
                        set id $val
                    }
                    -stripext {
                        set stripext $val
                    }
                    -simplify {
                        set simplify $val
                    }
                    -ref {
                        set assetref $val
                    }
                    -refproj {
                        if {$val ne ""} {
                            set refproj $val
                        }
                    }
                    -reffile {
                        if {$val ne ""} {
                            set reffile $val
                        }
                    }
                    -verbose {
                        set verbose $val
                    }
                }
            }
        }; # end of arg parsing for non-state-changing args

        PushState {_dynamicVars _workspaceVars}
        if [info exists amap(-frame)] {
            SetFrame $amap(-frame)
            unset amap(-frame);
        }
        # all other amap entries will be SetVar

        foreach {nm val} [array get amap] {
            if {[string index $nm 0] eq "-"} {
                SetVar [string range $nm 1 end] $val
            } else {
                ::RMS::LogMsg WARNING "RMSExpression: unknown arg $nm $val"
            }
        }

        # The real value of $HANDLE is substituted below 
        # after the simplify regexp is applied.
        if {$simplify && $_assetnmSimplifyExpr ne ""} {
            SetVar HANDLE "\${HANDLE}"
        }

        if {$cls ne "unset" && $cls ne {}} {
            # we're generating a name according to PASSID, PASSCLASS,
            # plus all the other scripting state.
            if ![info exists _assetnmLocatorMap($cls)] {
                set msg "Can't find $cls in AssetclassLocatorMap ($invoc)"
                ::RMS::LogMsg WARNING $msg
                error $msg
            }
            if {$assetnmpat ne ""} {
                # we have an override for the tabulated values
                set pat $assetnmpat
            } else {
                if {$id ne "" && [info exists _assetnmExtensionMap($id)]} {
                    set ext $_assetnmExtensionMap($id)
                    #RMS::LogMsg NOTICE "Found an extension for $id: $ext"
                } elseif [info exists _assetnmExtensionMap($cls)] {
                    set ext $_assetnmExtensionMap($cls)
                } else {
                    set ext ""
                }
                SetVar EXT $ext
                if {$id ne "" && [info exists _assetnmPatternMap($id)]} {
                    set pat $_assetnmPatternMap($id)
                    #RMS::LogMsg NOTICE "Found a pattern for $id: $pat"
                } elseif [info exists _assetnmPatternMap($cls)] {
                    set pat $_assetnmPatternMap($cls)
                } else {
                    set pat $_assetnmPatternMap(_default)
                }
            }
            set assetname {}
            if [catch {Interpolate $pat} assetname] {
                error "$assetname ($::errorInfo)"
            } elseif ![string match "skipping unknown:*" $assetname] {
                SetVar ASSETNAME $assetname
            }
            if {$assetref eq "unset" && $assetname ne {}} {
                if {[file pathtype [GetVar ASSETNAME]] == "absolute" ||
                    [file pathtype $amap(-HANDLE)] == "absolute"} {
                    # if ASSETNAME is absolute, don't use _assetnmLocatorMap
                    set assetref [GetVar ASSETNAME]
                } else {
                    # here we interpolate the assetclassLocatorMap value:
                    #   should turn something like this:
                    #       $DATAPATH/$FRAME/$ASSETNAME
                    #   to approximately this:
                    #       renderman/$STAGE/data/0001/bar.0001.tex
                    # one more level of substitution remains to obtain a 
                    #   fully-flattened pathname (below)
                    set assetref [Interpolate $_assetnmLocatorMap($cls)]
                }
            } elseif {$assetref eq "unset"} {
                set assetref {}
            }
        }
        SetWorkspace "AssetRef" $refproj $reffile $base
        if [catch {Interpolate $assetref} result] {
            error "$result ($::errorInfo)"
        }
        if $stripext {
            set result [file rootname $result]
        }
        if {$simplify && $_assetnmSimplifyExpr ne ""} {
            # we shouldn't simplify pathnames, only filenames.
            set result_tail [file tail $result]
            set result_dir [file dirname $result]
            if {$result_dir eq "."} {
                set result_dir ""
            }
            regsub -all $_assetnmSimplifyExpr $result_tail "" presult
            if {$verbose > 1} {
                ::RMS::LogMsg NOTICE \
                    "regsub $result -> $presult ($_assetnmSimplifyExpr)"
            }

            # substitute HANDLE after simplify expression but before
            # applying invalid char map
            SetVar HANDLE $amap(-HANDLE)
            set presult [string map "\${HANDLE} \"$amap(-HANDLE)\"" $presult]

            # also allow for HANDLE in result_dir 
            if [string match "*HANDLE*" $result_dir] {
                set fixedname [string map $_assetnmInvalidCharMap $amap(-HANDLE)]
                set result_dir [string map "\${HANDLE} \"$fixedname\"" $result_dir]
            }

            # in case HANDLE was a path, reset result_dir and result_tail
            if {$result_dir eq ""} {
                set result_dir [file dirname $presult]
                if {$result_dir eq "."} {
                    set result_dir ""
                }
                set result_tail [file tail $presult]
            } else {
                set result_tail $presult
            }
            set result_tail [string map $_assetnmInvalidCharMap $result_tail ]
            set result [file join $result_dir $result_tail]
        }
        if {!$createdir} {
            # we're not creating an asset, so try to resolve against
            # the PROD/PROJ settings. If resolve fails just leave the
            # path alone since it may be found in standard locations
            # (like the @ entry on a search path)
            switch $cls {
               "shader" -
               "rishader" {
                    set extensions {slo sl}
                } 
                default {
                    set extensions {}
                }
            }
            set result_fp [workspace ResolvePath $result local $extensions]
            if {$result_fp eq "" && ($cls eq "ribdriver" || $cls eq "rishader")} {
                set result_fp [file join $RMSPROJ $result]
            }
            if {$result_fp ne ""} {
                if {$fullpath == 0} {
                    set result [_pathRelativize $RMSPROD $result_fp]
                } else {
                    set result $result_fp
                }
            } else {
                # couldn't produce a full-path; leave it alone and assume
                # file may exist in searchpaths for its rez type.
                set result_fp [file join $RMSPROJ $result]
                if {$fullpath != 0} {
                    set result $result_fp
                }
            }
        } else {
            # we are making an asset so make sure the full path is
            # under RMSPROJ
            set result_fp [file join $RMSPROJ $result]
            if {$fullpath == 0} {
                set result [_pathRelativize $RMSPROD $result_fp]
            } else {
                set result $result_fp
            }
            
            set dir [file dirname $result_fp]
            if ![_fileExists $dir] {
                # ::RMS::LogMsg NOTICE "AssetRef: creating dir $dir"
                if [catch {file mkdir $dir} msg] {
                    if ![_fileExists $dir] {
                        # handle the case where some thing else created the dir
                        ::RMS::LogMsg ERROR "AssetRef: problem creating $dir ($msg)"
                    }
                }
            }
        } 
        if {$verbose} {
            ::RMS::LogMsg NOTICE \
                "$invoc -> $result (simplify: $simplify, fullpath: $fullpath)"
        }
        PopState
        if {$return ne "oneassetref"} {
            set result [list $result $result_fp]
        }
        return $result
    }

    proc ResetDynamicVars {} {
        variable _stateStack; variable _stateMap; variable _stateMapStack;
        variable _memoizeFileExists
        #may want to push workspace vars before a render (when reset occurs)
        #set _stateStack {}
        set _stateMapStack {}
        SetTimeStamp
        SetDspy {} {} {}
        SetCmd {} {}
        SetPass {} {} {} {} {} {} -layer {}
        SetSrcFile {}
        SetFrame -4000
        SetShaderGroup {}
        SetShader {} {} {} {}
        SetParameter {} {} {} {}
        SetObject {} {}
        SetVar MAPNAME {<undefined>}
        SetVar LAYER {}
        SetVar DENOISECHANNELS {}
        SetSlimInstance {} {} {} {} {}
        array unset _stateMap
        array unset _memoizeFileExists
        workspace ClearCaches
        _callResetCallbacks
    }

    proc PushState { {varlistNameList {_dynamicVars}} } {
        variable _stateStack
        set state {}
        foreach varlistName $varlistNameList {
            set state [concat $state [Encapsulate $varlistName]]
        }
        lappend _stateStack $state
        return {}
    }

    proc PopState {} {
        variable _stateStack
        if {[llength $_stateStack] >= 1} {
            Instantiate [lindex $_stateStack end]
            set _stateStack [lrange $_stateStack 0 end-1]
        } else {
            ::RMS::LogMsg ERROR "RMSExpression::PopState stack is empty!"
        }
        return {}
    }

    proc PushStageCtx stagectx {
        variable PROJ; variable FILE; variable BASEPATTERN;
        PushState {_dynamicVars _workspaceVars}
        SetWorkspace primary $PROJ $FILE {} $BASEPATTERN $stagectx
    }

    proc PopStageCtx {} {
        PopState
    }

    proc PushStateMap {} {
        variable _stateMapStack
        variable _stateMap
        lappend _stateMapStack [array get _stateMap]
        return {}
    }

    proc PopStateMap {} {
        variable _stateMapStack
        variable _stateMap
        if {[llength $_stateMapStack] >= 1} {
            array set _stateMap [lindex $_stateMapStack end]
            set _stateMapStack [lrange $_stateMapStack 0 end-1]
        } else {
            ::RMS::LogMsg ERROR "RMSExpression::PopStateMap stack is empty!"
        }
        return {}
    }
    
    # Extenders of RMSExpression can use this procedure to add a callback 
    # to be called by ResetDynamicVars
    proc AddResetCallback {procnm} {
        variable _resetCallbacks
        lappend _resetCallbacks $procnm
    }

    # - private ---------------------------------------------------

    proc _callResetCallbacks {} {
        variable _resetCallbacks
        foreach procnm $_resetCallbacks {
            eval $procnm
        }
    }

    proc _resetEnvVars {} {
        # make environment variables available as regular tcl vars
        foreach nm [GetPref SiteEnvVars] {
            if {![info exists ::RMSExpression::$nm]} {
                catch { variable $nm [GetEnv $nm]}
            }
        }
    }

    proc _fileExists {f} {
        variable _memoizeFileExists
        if {[info exists _memoizeFileExists($f)]} {
            return $_memoizeFileExists($f)
        } else {
            set result [file exists $f]
            set _memoizeFileExists($f) $result
            return $result
        }
    }

    proc _pathRelativize {root path} {
        set l [string length $root]
        if [string equal -length $l $root $path] {
            set path [string trimleft [string range $path $l end] /]
        }
        return $path
    }

    proc _fullyResolve pathname {
        set result $pathname
        # we currently anticipate no more that 3 levels of indirection
        for {set i 0} {$i < 3} {incr i} {
            if {-1 != [string first "\$" $result]} {
                set result [Interpolate $result]
            } else {
                break;
            }
        }
        return $result
    }

    proc _amapRequires {invoc mapnm args} {
        upvar $mapnm amap
        foreach a $args {
            if ![info exists amap($a)] {
                error "$invoc: missing required argument $a"
            }
        }
    }

    proc _handleSyncEvent {event arglist} {
        array set amap $arglist
        set handled 0
        set invoc "$event $arglist"
        switch -glob -- $event {
            "time:change" {
                _amapRequires $invoc amap -firstframe -lastframe -fps -time
                SetTimeContext $amap(-firstframe) $amap(-lastframe) $amap(-fps)
                SetFrame $amap(-time)
                set handled 1
            }
            "file:import" -
            "file:reference" -
            "file:export" {
                # nothing to do here...
            }
            "file:open" -
            "file:save" -
            "file:new" {
                _amapRequires $invoc amap -proj -file -basepattern
                set proj $amap(-proj); unset amap(-proj)
                set file $amap(-file); unset amap(-file)
                set pattern $amap(-basepattern); unset amap(-basepattern)
                if [info exists amap(-stagectx)] {
                    set stagectx $amap(-stagectx)
                    unset amap(-stagectx)
                } else {
                    set stagectx "-1"; # undefined ctx
                }
                workspace SetProject $proj
                # Below, get proj back from workspace rather than using $proj
                # when setting workspace vars below, because changes can occur
                # like with unc paths //FOO/bar -> //foo/bar
                # we want the vals to match; they're used when relativizing.
                SetWorkspace primary [workspace GetProjDir] $file {} $pattern $stagectx
                set handled 1
            }
            "session:clear" {
                if [info exists amap(-proj)] {
                    set proj $amap(-proj)
                } else {
                    variable RMSPROJ
                    set proj $RMSPROJ
                }
                if [info exists amap(-file)] {
                    set file $amap(-file)
                } else {
                    set file [file join $proj untitled]
                }
                workspace SetProject $proj
                SetWorkspace primary [workspace GetProjDir] $file untitled {}
                set handled 1
            }
            "session:status" {
                _amapRequires $invoc amap -state
                if [info exists amap(-proj)] {
                    set proj $amap(-proj)
                    unset amap(-proj)
                    set file {}
                    if [info exists amap(-file)] {
                        set file $amap(-file)
                        unset amap(-file)
                    }
                    if [info exists amap(-stagectx)] {
                        set stagectx  $amap(-stagectx)
                        unset amap(-stagectx)
                    } else {
                        set stagectx -1; # ie undefined
                    }
                    SetWorkspace primary $proj $file untitled {} $stagectx
                }
                Instantiate $amap(-state); # should't contain RMSPROJ
                                           # might contain DSPY, so perform
                                           # after SetWorkspace
                unset amap(-state)
                set handled 1
            }
            "session:busybegin" -
            "session:busyend" -
            "slim:*" {
                # nothing to do here...
            }
            default {
                ::RMS::LogMsg DEBUG "HandleSyncEvent unexpected event $event"
            }
        }
        if {!$handled} {
            ::RMS::LogMsg DEBUG "$event is unhandled..."
        }
        return [array get amap]
    }

    proc _basename filename {
        return  [file rootname [file tail $filename]]
    }

    proc _resetAssetnamePkg fullpaths {
        variable _assetrefFullpaths $fullpaths
        variable _assetnmLocatorMap
        array set _assetnmLocatorMap [GetPref AssetLocTable]

        variable _assetnmPatternMap
        array set _assetnmPatternMap [GetPref AssetnamePatternTable]

        variable _assetnmExtensionMap
        array set _assetnmExtensionMap [GetPref AssetnameExtTable]

        variable _assetnmInvalidCharMap [GetPref AssetnameInvalidCharMap]
        variable _assetnmSimplifyExpr [GetPref AssetnameSimplifyRegexp]

        SetVar FRAMEFORMAT [GetPref AssetnameFrameFormat]

        # some backwards compatibility for existing expressions:
        SetVar IMAGEPATH [workspace GetDir rfmImages]
        SetVar DATAPATH [workspace GetDir rfmData]
        SetVar SHADERPATH [workspace GetDir rfmShaders]
        SetVar TEXTUREPATH [workspace GetDir rfmTextures]
        SetVar RIBPATH [workspace GetDir rfmRIBs]
    }

    # GetRIBPreamble:
    #   this proc is called by RMS apps to obtain the setup RIB
    #   required to render.  It is used by Slim's preview renderer
    #   as well as by RfM's swatch render and general RIB gen.
    #   Sites can override this but should ensure that RMSPROJ variables
    #   are defined. clientctx can be used to deliver client-specific
    #   preamble variation.
    proc GetRIBPreamble client {
        variable RMSPROD; variable RMSPROD_GLOBAL
        variable RMSPROJ; variable RMSPROJ_SHARING; variable PROJ;
        variable RENDERTYPE;

        set rib \
"Option \"ribparse\" \"string varsubst\" \[\"\"\]
Option \"ribparse\" \"string varsubst\" \[\"$\"\]\n"

        switch -- [GetPref RMSProductionModel] {
            ProjEqualsProd {
                append rib \
"IfBegin \"!defined(RMSPROJ_FROM_ENV)\"
Option \"user\" \"string RMSPROJ\" \"${RMSPROJ}\"
IfEnd\n"
            }
            ProjWithinProd {
                append rib \
"IfBegin \"!defined(RMSPROJ_FROM_ENV)\"
Option \"user\" \"string RMSPROJ\" \"${RMSPROJ}\"
Option \"user\" \"string RMSPROJ_SHARING\" \"${RMSPROJ_SHARING}\"
Option \"user\" \"string RMSPROD\" \"${RMSPROD}\"
Option \"user\" \"string RMSPROD_GLOBAL\" \"${RMSPROD_GLOBAL}\"
IfEnd\n"
            }
        }
        append rib \
"IfBegin \"!defined(RMSTREE)\"
Option \"user\" \"string RMSTREE\" \"[::RMS::GetDir rmstree]\"
IfEnd\n"

        # local must go first
        foreach dir {local archive display shader texture rixplugin} {
            if {$dir eq "local"} {
                set sp "resource"
            } else {
                set sp $dir
            }
            append rib "Option \"searchpath\" \"string $sp\" \
                       \[\"[workspace GetSearchPaths $dir partial RIB]\"\]\n"
        }

        set dirmaps [workspace GetDirMaps RIB]
        set dirmaps [string map {"\"" "\\\"" "[" "\\[" "]" "\\]"} $dirmaps]
        append rib "Option \"searchpath\" \"string dirmap\" \[\"$dirmaps\"\]\n"

        set subdir ""
        append rib "Option \"searchpath\" \"string rifilter\" \
                   \[\"\${RMSTREE}/lib/rif/$subdir:[workspace GetSearchPaths rifilter partial RIB]\"\]\n"
        append rib "Option \"searchpath\" \"string procedural\" \
                   \[\"\${RMSTREE}/lib/plugins/$subdir:[workspace GetSearchPaths procedural partial RIB]\"\]\n"

        return $rib
    }
}

::RMSExpression::_init
::RMS::LogMsg DEBUG "RMS Expression Subsystem Initialized"

