#!/usr/bin/env bash

#  this is a script that runs upon login and needs to be located in /etc/profile.d
#  so is local to the machine


echo ""
echo  "STARTING: ${BASH_SOURCE}"

#########  UTSDABBASE
ID=`/usr/bin/id -u`
[ -n "$ID" -a "$ID" -le 500 ] && [ $ID -ne 495 ] && echo "System User-- not using dabanim.sh" && return

#########  DABRENDER and DABDEV
_dabrender="/Volumes/dabrender"
_dabdev="/Users/Shared/UTS_Dev/gitRepositories/utsdab_repos"
unset DABRENDER
unset DABDEV



###  ideally we want to test whether this is a mounted filesystem that can be read
if [ -d ${_dabrender} ]; then
    export DABRENDER="${_dabrender}"
    echo "INFO    : DABRENDER = ${DABRENDER}"
    if [ -f ${DABRENDER}/etc/uts/profile ]; then
        source "${DABRENDER}/etc/uts/profile"
        echo "INFO: Run the main profile script ${DABRENDER}/etc/uts/profile"
    else
        echo "CRITICAL: Cant run the main profile script ${DABRENDER}/etc/uts/profile"
    fi

else
    echo "CRITICAL: Cant set DABRENDER  ${_dabrender}, trying DABDEV."
    unset DABRENDER
fi


########  source  profile
if [ -d ${_dabdev} ]; then
    export DABDEV="${_dabdev}"
    echo "INFO    : DABDEV = ${DABDEV}"
    if [ -f ${DABDEV}/etc/uts/profile ]; then
        source "${DABDEV}/etc/uts/profile"
        echo "INFO: Run dev profile script ${DABDEV}/etc/uts/profile"
    else
        echo "CRITICAL: Cant run dev profile script ${DABDEV}/etc/uts/profile"
    fi
else
    echo "CRITICAL: Cant set DABDEV  ${_dabdev}"
fi

echo     "ENDING  : ${BASH_SOURCE}"
echo     ""
