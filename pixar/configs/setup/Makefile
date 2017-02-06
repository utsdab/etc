#
# This makefile runs an installation confidence test.
# It renders a simple scene description, trial.rib.
# Then it compares the output image to the expected
# output, check.tif, that was rendered at Pixar.
# The rendering uses an OSL shader that is compiled
# from source.
#

SHELL = /bin/bash

ifndef RMANTREE
$(warning RMANTREE not set, using ../..)
export RMANTREE = ../..
endif

CMPTIFF	= $(RMANTREE)/bin/cmptiff
SHADER	= $(RMANTREE)/bin/oslc
RENDER	= $(RMANTREE)/bin/prman

test:	trial
	$(CMPTIFF) -q -t .03 trial.tif check.tif

trial:	trial.rib shield.oso
	@echo > trial.tif
	$(RENDER) trial.rib

shield.oso:  shield.osl
	$(SHADER) shield.osl

clean:
	rm -f trial.tif shield.oso
