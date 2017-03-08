
# --------------------------------------------------------------------------
# poseReader.h - C++ Header File
# --------------------------------------------------------------------------
# Copyright 2004 Michael B. Comet  All Rights Reserved
# --------------------------------------------------------------------------
#
# DESCRIPTION:
#	Header for poseReader node.
#
# AUTHORS:
#		Michael B. Comet - comet@comet-cartoons.com
#
# VERSIONS:
#		1.00 - 09/11/04 - comet - Initial Rev.
#		1.06 - 10/17/04 - comet - Moved over smooth/gaussian options here.
#					Brought up version to match with poseDeformer.
#					Now has animCuve mode.
#		1.08 - 11/16/04 - comet - Now does translate
#		1.09 - 11/17/04 - comet - Has multiTrigger support for better usage
#				of multiple nodes at once.  Also has allowRotate option.
#		1.10 - 01/21/05 - mcomet - Now has nodestate HasNoEffect stop.
#		1.20 - 04/04/09 - rtrowbridge - Now written in Python so the plugin does not need recompiled!
#
# --------------------------------------------------------------------------
#
#  poseReader - Pose Space Angle Reader Maya Plugin by Michael B. Comet
#  Copyright 2004 Michael B. Comet
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#   For information on poseDeformer contact:
#			Michael B. Comet - comet@comet-cartoons.com
#			or visit http:#www.comet-cartooons.com/toons/
#
# --------------------------------------------------------------------------


import sys
import math
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender


#
# Defines
#
VERSION = "1.20"

# 0x0010A580 - 0x0010A5BF  COMET BLOCK Assigned by ALIAS! 64 entries!
#
ID_BLOCKSTART = 0x0010A580

NAME_POSEREADER = "poseReader"
NAME_MULTITRIGGER = "multiTrigger"
CREATEDATE = "2 - 4 - 2009"

# Previous entries used by other plugins I wrote...
ID_POSEREADER = OpenMaya.MTypeId(ID_BLOCKSTART+5)			# 0x0010A585
ID_MULTITRIGGER = OpenMaya.MTypeId(ID_BLOCKSTART+8)			# 0x0010A588

VRADTODEG = 57.295828
VDEGTORAD = 0.0174533

ETRIGGERMODE = { 'eTriggerLowest':0, 'eTriggerAverage':1, 'eTriggerMultiply':2 }
EINTERPMODE = { 'eInterpLinear':0, 'eInterpSmoothStep':1, 'eInterpGaussian':2, 'eInterpCurve':3 }

# --------------------------------------------------------------------------
#
# multiTrigger - Class definition for main pose calc node
#
class multiTrigger ( OpenMayaMPx.MPxNode ):

	# Input Attrs
	aInput = OpenMaya.MObject()				# Cmpd Inputs
	aEnvelope = OpenMaya.MObject()		 	# Basic overall envelope
	aTriggerMode = OpenMaya.MObject()		# How are we triggering output value?
	aInputValues = OpenMaya.MObject()		# Array of input values

	# Output Attrs
	aOutWeight = OpenMaya.MObject()		 	# Output weight

	def __init__(self):
		OpenMayaMPx.MPxNode.__init__(self)

	# multiTrigger creator
	def creator(self):
		return OpenMayaMPx.asMPxPtr( multiTrigger() )

	# multiTrigger::initialize() - Setup attrs on node.
	def initialize(self):

		nAttr = OpenMaya.MFnNumericAttribute()
		cAttr = OpenMaya.MFnCompoundAttribute()
		eAttr = OpenMaya.MFnEnumAttribute()
		mAttr = OpenMaya.MFnMatrixAttribute()
		msgAttr = OpenMaya.MFnMessageAttribute()


		# Input Attrs
		#
		multiTrigger.aEnvelope = nAttr.create( "envelope", "fj", OpenMaya.MFnNumericData.kFloat, 1.0 );
		nAttr.setSoftMin(0.0)
		nAttr.setSoftMax(1.0)
		nAttr.setKeyable(True)

		multiTrigger.aTriggerMode = eAttr.create( "triggerMode", "tmod", 0)
		eAttr.addField("lowest", ETRIGGERMODE['eTriggerLowest'] )
		eAttr.addField("average", ETRIGGERMODE['eTriggerAverage'] )
		eAttr.addField("multiply", ETRIGGERMODE['eTriggerMultiply'] )
		eAttr.setKeyable(True)

		multiTrigger.aInputValues = nAttr.create( "inputValues", "ival", OpenMaya.MFnNumericData.kDouble, 1.0 )
		nAttr.setArray(True)
		nAttr.setUsesArrayDataBuilder(True)


		# Now make cmpd
		multiTrigger.aInput = cAttr.create( "input", "inp" )
		cAttr.addChild( multiTrigger.aEnvelope )
		cAttr.addChild( multiTrigger.aTriggerMode )
		cAttr.addChild( multiTrigger.aInputValues )


		# Output Attrs
		#
		multiTrigger.aOutWeight = nAttr.create( "outWeight", "out", OpenMaya.MFnNumericData.kDouble, 0.0 )
		nAttr.setWritable(False);

		# Add the attributes we have created to the node
		#
		try:
			multiTrigger.addAttribute( multiTrigger.aInput )
		except:
			sys.stderr.write( "addAttribute" ); raise

		try:
			multiTrigger.addAttribute( multiTrigger.aOutWeight )
		except:
			sys.stderr.write( "addAttribute" ); raise

		# Set up a dependency between the input and the output.  This will cause
		# the output to be marked dirty when the input changes.  The output will
		# then be recomputed the next time the value of the output is requested.
		#
		try:
			multiTrigger.attributeAffects( multiTrigger.aInput, multiTrigger.aOutWeight )
		except:
			sys.stderr.write( "attributeAffects" ); raise

		return OpenMaya.MStatus.kSuccess;

	# --------------------------------------------------------------------------
	#
	# multiTrigger::compute() - Main calc
	#
	def compute( self, plug, data ):

		if( plug == multiTrigger.aOutWeight ):

			thisObject = self.thisMObject()

			# Read input values
			hEnvelope = data.inputValue( multiTrigger.aEnvelope )
			fEnv = hEnvelope.asFloat()

			hNodeState = data.inputValue( self.state )
			nNodeState = hNodeState.asShort()

			# For speed
			if (fEnv == 0.0 or nNodeState == 1):

				hOutWeight = data.outputValue( multiTrigger.aOutWeight )
				hOutWeight.set( 0.0 )
				hOutWeight.setClean()
				data.setClean( plug )
				return OpenMaya.MStatus.kSuccess

			hTriggerMode = data.inputValue( multiTrigger.aTriggerMode )
			eTriggerMode = hTriggerMode.asShort()

			# Read in the value weights
			dArrVals = OpenMaya.MDoubleArray()
			uValsPtr = OpenMaya.MScriptUtil().asUintPtr()		#Unsigned Int Pointer
			self.readInputValues(data, dArrVals, uValsPtr)
			uVals = OpenMaya.MScriptUtil.getUint( uValsPtr )

			# ==========================================
			# Now do real calc

			dWt = 0.0			# output weight

			# Now go thru each input weight...
			for u in range(0, uVals, 1):

				if (u == 0):
					dWt = dArrVals[u]
				else:

					if(eTriggerMode == ETRIGGERMODE['eTriggerLowest']):
						if (dArrVals[u] < dWt):
							dWt = dArrVals[u]

					elif(eTriggerMode == ETRIGGERMODE['eTriggerAverage']):
							dWt += dArrVals[u]

					elif(eTriggerMode == ETRIGGERMODE['eTriggerMultiply']):
							dWt *= dArrVals[u]

			# end of u loop


			if (eTriggerMode == ETRIGGERMODE['eTriggerAverage'] and uVals > 0):
				dWt = dWt / uVals		# Average now...


			# End of node calc
			# ==========================================
			# Set outputs
			hOutWeight = data.outputValue( multiTrigger.aOutWeight )
			hOutWeight.setDouble( dWt )
			hOutWeight.setClean()

			data.setClean( plug )

		else:
			return OpenMaya.MStatus.kUnknownParameter

		return OpenMaya.MStatus.kSuccess

	#private:
	# --------------------------------------------------------------------------
	#
	# multiTrigger::readInputValues() - Reads input values.
	#
	def readInputValues(self, data, dArrVals, uValsPtr):

		hArrInputValues = data.inputArrayValue( multiTrigger.aInputValues ) 	# MArrayDataHandle

		uVals = hArrInputValues.elementCount()									# How many inputs?
		OpenMaya.MScriptUtil.setUint( uValsPtr, uVals )

		dArrVals.setLength( uVals )												# alloc array

		for u in range(uVals-1):

			hEleVal = hArrInputValues.jumpToElement(u)
			hEleVal = hArrInputValues.inputValue()
			try:
				dArrVals[u] = hEleVal.asDouble()
			except:
				pass

			hArrInputValues.next()												# and go to next one.

		return OpenMaya.MStatus.kSuccess


# --------------------------------------------------------------------------
#
# poseReader - Class definition for main pose calc node
#
class poseReader ( OpenMayaMPx.MPxLocatorNode ):

	# Input Attrs
	aPoseData = OpenMaya.MObject()				# Array Compound of input data
	aWorldMatrixLiveIn = OpenMaya.MObject()		# mat for real jnt
	aWorldMatrixPoseIn = OpenMaya.MObject()		# mat for pose loc
	aMsgAnimCurve = OpenMaya.MObject()		 	# Msg attr from an animCurve.
	aAnimCurveOutput = OpenMaya.MObject()		# Output from animCurve.
	aReadAxis = OpenMaya.MObject()		 		# Enum of what axis, x,y,z,all to read?
	aInterpMode = OpenMaya.MObject()		 	# How to interpolate from 0-180...
	aAllowRotate = OpenMaya.MObject()		 	# 0-1 allowing of rotate or not.
	aMinAngle = OpenMaya.MObject()		 		# Anything in here is one default 0
	aMaxAngle = OpenMaya.MObject()		 		# up to here... default 180
	aAllowTwist = OpenMaya.MObject()		 	# 0-1 allowing of twist or not.
	aMinTwist = OpenMaya.MObject()		 		# Min Twist allowed
	aMaxTwist = OpenMaya.MObject()		 		# Max Twist allowed
	aAllowTranslate = OpenMaya.MObject()		# If on, translate anywhere is allowed.
	aMinTranslate = OpenMaya.MObject()		 	# Min Translate allowed
	aMaxTranslate = OpenMaya.MObject()		 	# Max Translate allowed

	aDrawData = OpenMaya.MObject()		 		# Compound of drawing options
	aDrawDetail = OpenMaya.MObject()		 	# Detail level of drawing.
	aDrawCone = OpenMaya.MObject()				# Text cone options
	aDrawText = OpenMaya.MObject()				# Text draw options
	aDrawReverse = OpenMaya.MObject()			# For joints where the axis is backwards, you may want this.
	aDrawHighlight = OpenMaya.MObject()			# Change to maya sel colors when selected?

	# Find the GL function table for the
	# draw method
	glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
	glFT = glRenderer.glFunctionTable()

	# Output Attrs
	aOutWeight = OpenMaya.MObject()				# Output weight

	def __init__(self):
		OpenMayaMPx.MPxLocatorNode.__init__(self)

	# poseReader creator
	def creator(self):
		return OpenMayaMPx.asMPxPtr( poseReader() )

	# poseReader::initialize() - Setup attrs on node.
	def initialize(self):

		nAttr = OpenMaya.MFnNumericAttribute()
		cAttr = OpenMaya.MFnCompoundAttribute()
		eAttr = OpenMaya.MFnEnumAttribute()
		mAttr = OpenMaya.MFnMatrixAttribute()
		msgAttr = OpenMaya.MFnMessageAttribute()

		# Input Attrs
		#
		poseReader.aWorldMatrixLiveIn = mAttr.create( "worldMatrixLiveIn", "wml" )
		poseReader.aWorldMatrixPoseIn = mAttr.create( "worldMatrixPoseIn", "wmp" )
		poseReader.aMsgAnimCurve = msgAttr.create("msgAnimCurve", "msgac")
		poseReader.aAnimCurveOutput = nAttr.create( "animCurveOutput", "acout", OpenMaya.MFnNumericData.kDouble, 1.0 );

		poseReader.aReadAxis = eAttr.create( "readAxis", "axi", 1)
		eAttr.addField("X-Axis", 0)
		eAttr.addField("Y-Axis", 1)
		eAttr.addField("Z-Axis", 2)
		eAttr.setKeyable(True) ;

		poseReader.aInterpMode = eAttr.create( "interpMode", "imod", 0 )
		eAttr.addField("Linear", EINTERPMODE['eInterpLinear'] )
		eAttr.addField("SmoothStep", EINTERPMODE['eInterpSmoothStep'] )
		eAttr.addField("Gaussian", EINTERPMODE['eInterpGaussian'] )
		eAttr.addField("AnimCurve", EINTERPMODE['eInterpCurve'] )
		eAttr.setKeyable(True)

		poseReader.aAllowRotate = nAttr.create( "allowRotate", "aro", OpenMaya.MFnNumericData.kDouble, 0.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(1.0)
		nAttr.setKeyable(True)

		poseReader.aMinAngle = nAttr.create( "minAngle", "min", OpenMaya.MFnNumericData.kDouble, 0.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(180.0)
		nAttr.setKeyable(True)

		poseReader.aMaxAngle = nAttr.create( "maxAngle", "max", OpenMaya.MFnNumericData.kDouble, 180.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(180.0)
		nAttr.setKeyable(True)

		poseReader.aAllowTwist = nAttr.create( "allowTwist", "atw", OpenMaya.MFnNumericData.kDouble, 1.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(1.0)
		nAttr.setKeyable(True)

		poseReader.aMinTwist = nAttr.create( "minTwist", "mtw", OpenMaya.MFnNumericData.kDouble, 0.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(180.0)
		nAttr.setKeyable(True)

		poseReader.aMaxTwist = nAttr.create( "maxTwist", "xtw", OpenMaya.MFnNumericData.kDouble, 180.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(180.0)
		nAttr.setKeyable(True)

		poseReader.aAllowTranslate = nAttr.create( "allowTranslate", "atr", OpenMaya.MFnNumericData.kDouble, 1.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(1.0)
		nAttr.setKeyable(True)

		poseReader.aMinTranslate = nAttr.create( "minTranslate", "mtr", OpenMaya.MFnNumericData.kDouble, 0.0 )
		nAttr.setMin(0.0)
		nAttr.setKeyable(True)

		poseReader.aMaxTranslate = nAttr.create( "maxTranslate", "xtr", OpenMaya.MFnNumericData.kDouble, 1.0 )
		nAttr.setMin(0.0)
		nAttr.setKeyable(True)


		# Now make cmpd
		poseReader.aPoseData = cAttr.create( "poseData", "data" )
		cAttr.addChild( poseReader.aWorldMatrixLiveIn )
		cAttr.addChild( poseReader.aWorldMatrixPoseIn )
		cAttr.addChild( poseReader.aMsgAnimCurve )
		cAttr.addChild( poseReader.aAnimCurveOutput )
		cAttr.addChild( poseReader.aReadAxis )
		cAttr.addChild( poseReader.aInterpMode )
		cAttr.addChild( poseReader.aAllowRotate )
		cAttr.addChild( poseReader.aMinAngle )
		cAttr.addChild( poseReader.aMaxAngle )
		cAttr.addChild( poseReader.aAllowTwist )
		cAttr.addChild( poseReader.aMinTwist )
		cAttr.addChild( poseReader.aMaxTwist )
		cAttr.addChild( poseReader.aAllowTranslate )
		cAttr.addChild( poseReader.aMinTranslate )
		cAttr.addChild( poseReader.aMaxTranslate )


		poseReader.aDrawDetail = nAttr.create( "drawDetail", "det", OpenMaya.MFnNumericData.kInt, 14.0 )
		nAttr.setMin(0)
		nAttr.setMax(48)
		nAttr.setKeyable(True)

		poseReader.aDrawCone = eAttr.create("drawCone", "con", 2 )
		eAttr.addField( "off", 0)
		eAttr.addField( "on", 1)
		eAttr.addField( "selected", 2)
		eAttr.setKeyable(True)

		poseReader.aDrawText = eAttr.create("drawText", "txt", 2 )
		eAttr.addField( "off", 0)
		eAttr.addField( "on", 1)
		eAttr.addField( "selected", 2)
		eAttr.setKeyable(True)

		poseReader.aDrawHighlight = nAttr.create( "drawHighlight", "dhi", OpenMaya.MFnNumericData.kFloat, 1.0 )
		nAttr.setMin(0.0)
		nAttr.setMax(1.0)
		nAttr.setKeyable(True)

		poseReader.aDrawReverse = nAttr.create( "drawReverse", "drv", OpenMaya.MFnNumericData.kBoolean, 0 )
		nAttr.setKeyable(True)

		poseReader.aDrawData = cAttr.create( "drawData", "ddat" )
		cAttr.addChild( poseReader.aDrawDetail )
		cAttr.addChild( poseReader.aDrawCone )
		cAttr.addChild( poseReader.aDrawText )
		cAttr.addChild( poseReader.aDrawReverse )
		cAttr.addChild( poseReader.aDrawHighlight )



		# Output Attrs
		#
		poseReader.aOutWeight = nAttr.create( "outWeight", "out", OpenMaya.MFnNumericData.kDouble, 1.0 )
		nAttr.setWritable(False)


		# Add the attributes we have created to the node
		#
		try:
			poseReader.addAttribute( poseReader.aPoseData )
		except:
			sys.stderr.write( "addAttribute" ); raise

		try:
			poseReader.addAttribute( poseReader.aDrawData )
		except:
			sys.stderr.write( "addAttribute" ); raise

		try:
			poseReader.addAttribute( poseReader.aOutWeight )
		except:
			sys.stderr.write( "addAttribute" ); raise

		# Set up a dependency between the input and the output.  This will cause
		# the output to be marked dirty when the input changes.  The output will
		# then be recomputed the next time the value of the output is requested.
		#
		try:
			poseReader.attributeAffects( poseReader.aPoseData, poseReader.aOutWeight )
		except:
			sys.stderr.write( "attributeAffects" )
			raise

		return OpenMaya.MStatus.kSuccess

	#
	# poseReader::compute() - Main calc
	#
	def compute( self, plug, data ):

		#sys.__stdout__.write( "executing poseReader.compute()\n" )
		if( plug == poseReader.aOutWeight ):

			#sys.__stdout__.write( "aOutWeight updating in poseReader.compute()\n" )

			thisObject = self.thisMObject()

			# Just stop if we in a "HasNoEffect" node state...
			# state is an attribute of MPxNode with MPxLocator is derived from MPxNode
			hNodeState = data.inputValue( self.state )
			nNodeState = hNodeState.asShort()
			if (nNodeState == 1):
				return OpenMaya.MStatus.kSuccess


			# Read input values
			hWorldMatrixLiveIn = data.inputValue( poseReader.aWorldMatrixLiveIn )
			matLive = hWorldMatrixLiveIn.asMatrix()
			invmatLive = matLive.inverse()

			hWorldMatrixPoseIn = data.inputValue( poseReader.aWorldMatrixPoseIn )
			matPose = hWorldMatrixPoseIn.asMatrix()
			invmatPose = matPose.inverse()

			hReadAxis = data.inputValue( poseReader.aReadAxis )
			nReadAxis = hReadAxis.asShort()

			hInterpMode = data.inputValue( poseReader.aInterpMode )
			nInterpMode = hInterpMode.asShort()


			hAllowRotate = data.inputValue( poseReader.aAllowRotate )
			dAllowRotate = hAllowRotate.asDouble()

			hMinAngle = data.inputValue( poseReader.aMinAngle )
			dMinAngle = hMinAngle.asDouble()

			hMaxAngle = data.inputValue( poseReader.aMaxAngle )
			dMaxAngle = hMaxAngle.asDouble()

			if (dMinAngle >= dMaxAngle):
				dMinAngle = dMaxAngle-0.001

			hAllowTwist = data.inputValue( poseReader.aAllowTwist )
			dAllowTwist = hAllowTwist.asDouble()

			hMinTwist = data.inputValue( poseReader.aMinTwist )
			dMinTwist = hMinTwist.asDouble()

			hMaxTwist = data.inputValue( poseReader.aMaxTwist )
			dMaxTwist = hMaxTwist.asDouble()

			if (dMinTwist >= dMaxTwist):
				dMinTwist = dMaxTwist-0.001


			hAllowTranslate = data.inputValue( poseReader.aAllowTranslate )
			dAllowTranslate = hAllowTranslate.asDouble()

			hMinTranslate = data.inputValue( poseReader.aMinTranslate )
			dMinTranslate = hMinTranslate.asDouble()

			hMaxTranslate = data.inputValue( poseReader.aMaxTranslate )
			dMaxTranslate = hMaxTranslate.asDouble()

			if (dMinTranslate >= dMaxTranslate):
				dMinTranslate = dMaxTranslate-0.001

			# Get anim curve function set...
			#
			# Get a plug to msg attr
			plugMsgAnimCurve = OpenMaya.MPlug( thisObject, poseReader.aMsgAnimCurve )
			plugArrMsgACIn = OpenMaya.MPlugArray()					# What is connected into it?
			oAnimCurve = OpenMaya.MObject()
			plugMsgAnimCurve.connectedTo( plugArrMsgACIn, True, False )


			if (plugArrMsgACIn.length() > 0):						# If something is connected
				plugInput = OpenMaya.MPlug( plugArrMsgACIn[0] )		# get the node on the opposite side
				oAnimCurve = plugInput.node()


			#Since you can not pass a MStatus object to MFnAnimCurve with Python
			#You have to be more inventive with your code
			stat_fnAnimCurve = True
			fnAnimCurve = OpenMayaAnim.MFnAnimCurve()
			try:
				fnAnimCurve = OpenMayaAnim.MFnAnimCurve( oAnimCurve )
			except:
				stat_fnAnimCurve = False

			bHasAC = True

			if (not stat_fnAnimCurve or fnAnimCurve.animCurveType() != OpenMayaAnim.MFnAnimCurve().kAnimCurveUU):
				bHasAC = False
			else:
				bHasAC = True


			# ==========================================
			# Now do real calc

			dWt = 1.0				# output weight

			dDot = -1.0
			dAngle = 180.0
			dWtTwist = 1.0
			dWtTranslate = 1.0

			matRelPose = matLive * invmatPose		# where is joint relative to pose node?

			if (nReadAxis == 0):		# X-Axis

				# Get X axis of live joint in relative space of the pose node.
				vAxis = OpenMaya.MVector(1,0,0) * matRelPose
				vAxis.normalize()
				dDot = vAxis * OpenMaya.MVector(1,0,0)		# Now in pose space, compare it's X axis to the joint
				if (dDot >= 1.0):		# Have to do this to handle precision errors in acos returning -1.#IND
					dAngle = 0.0
				elif (dDot <= -1.0):
					dAngle = 180.0
				else:
					dAngle = math.acos(dDot) * VRADTODEG	# Now what is actual angle in degress?


				dWt = self.__calcWtFromAngle(dAngle, dMinAngle, dMaxAngle)

				dWt = ((1.0-dAllowRotate) * dWt) + (dAllowRotate * 1.0)

				if (dAllowTwist != 1.0):

					vAxisTwist = OpenMaya.MVector(0,1,0) * matRelPose
					vAxisTwist.normalize()
					dDotTwist = vAxisTwist * OpenMaya.MVector(0,1,0)
					dAngleTwist = 0
					if (dDotTwist >= 1.0):
						dAngleTwist = 0.0
					elif (dDotTwist <= -1.0):
						dAngleTwist = 180.0
					else:
						dAngleTwist = math.acos(dDotTwist) * VRADTODEG	# Now what is actual angle in degress?

					dWtTwist = self.__calcWtFromAngle(dAngleTwist, dMinTwist, dMaxTwist)

					dWt = ((1.0-dAllowTwist)*(dWt * dWtTwist)) + (dAllowTwist * dWt)


			elif (nReadAxis == 1):	# Y-Axis

				# Get Y axis of live joint in relative space of the pose node.
				vAxis = OpenMaya.MVector(0,1,0) * matRelPose
				vAxis.normalize()
				dDot = vAxis * OpenMaya.MVector(0,1,0)		# Now in pose space, compare it's Y axis to the joint
				if (dDot >= 1.0):					# Have to do this to handle precision errors in acos returning -1.#IND
					dAngle = 0.0
				elif (dDot <= -1.0):
					dAngle = 180.0
				else:
					dAngle = math.acos(dDot) * VRADTODEG	# Now what is actual angle in degress?

				dWt = self.__calcWtFromAngle(dAngle, dMinAngle, dMaxAngle)
				dWt = ((1.0-dAllowRotate) * dWt) + (dAllowRotate * 1.0)

				#sys.__stdout__.write( "dWt=" + str(dWt) + " dAngle=" + str(dAngle) + " acos(dDot)=" + str(acos(dDot)) + " dAllowTwist=" + str(dAllowTwist) + " dDot=" + str(dDot) + " vAxis=" + str(vAxis) + " dMinAngle=" + str(dMinAngle) + " dMaxAngle=" + str(dMaxAngle) + "\n" )

				if (dAllowTwist != 1.0):

					vAxisTwist = OpenMaya.MVector(1,0,0) * matRelPose
					vAxisTwist.normalize()
					dDotTwist = vAxisTwist * OpenMaya.MVector(1,0,0)
					dAngleTwist = 0.0
					if (dDotTwist >= 1.0):
						dAngleTwist = 0.0
					elif (dDotTwist <= -1.0):
						dAngleTwist = 180.0
					else:
						dAngleTwist = math.acos(dDotTwist) * VRADTODEG	# Now what is actual angle in degress?

					dWtTwist = self.__calcWtFromAngle(dAngleTwist, dMinTwist, dMaxTwist)

					dWt = ((1.0-dAllowTwist)*(dWt * dWtTwist)) + (dAllowTwist * dWt)

			elif (nReadAxis == 2):	# Z-Axis

				# Get Z axis of live joint in relative space of the pose node.
				vAxis = OpenMaya.MVector(0,0,1) * matRelPose
				vAxis.normalize()
				dDot = vAxis * OpenMaya.MVector(0,0,1)		# Now in pose space, compare it's Z axis to the joint
				if (dDot >= 1.0):							# Have to do this to handle precision errors in acos returning -1.#IND
					dAngle = 0.0
				elif (dDot <= -1.0):
					dAngle = 180.0
				else:
					dAngle = math.acos(dDot) * VRADTODEG	# Now what is actual angle in degress?

				dWt = self.__calcWtFromAngle(dAngle, dMinAngle, dMaxAngle)
				dWt = ((1.0-dAllowRotate) * dWt) + (dAllowRotate * 1.0)

				if (dAllowTwist != 1.0):

					vAxisTwist = OpenMaya.MVector(1,0,0) * matRelPose
					vAxisTwist.normalize()
					dDotTwist = vAxisTwist * OpenMaya.MVector(1,0,0)
					dAngleTwist = 0.0
					if (dDotTwist >= 1.0):
						dAngleTwist = 0.0
					elif (dDotTwist <= -1.0):
						dAngleTwist = 180.0
					else:
						dAngleTwist = math.acos(dDotTwist) * VRADTODEG;	# Now what is actual angle in degress?

					dWtTwist = self.__calcWtFromAngle(dAngleTwist, dMinTwist, dMaxTwist)

					dWt = ((1.0-dAllowTwist)*(dWt * dWtTwist)) + (dAllowTwist * dWt)


			if (dAllowTranslate != 1.0):

				vTrans = OpenMaya.MVector( matRelPose(3,0), matRelPose(3,1), matRelPose(3,2) )
				dDist = vTrans.length()
				if (dDist <= dMinTranslate):
					dWtTranslate = 1.0
				elif (dDist >= dMaxTranslate):
					dWtTranslate = 0.0
				else:
					dWtTranslate = 1.0 - ((dDist - dMinTranslate) / (dMaxTranslate - dMinTranslate))

				dWt = ((1.0-dAllowTranslate)*(dWt * dWtTranslate)) + (dAllowTranslate * dWt)


			# Adjust actual output a bit if desired.
			if (nInterpMode == EINTERPMODE['eInterpLinear']):
				pass
			elif (nInterpMode == EINTERPMODE['eInterpSmoothStep']):
				dWt = self.__smoothStep(dWt)
			elif (nInterpMode == EINTERPMODE['eInterpGaussian']):
				dWt = self.__smoothGaussian(dWt)
			elif (nInterpMode == EINTERPMODE['eInterpCurve']):

				if (not bHasAC):
					OpenMaya.MGlobal.displayWarning( self.name() + ": You must connect an animCurveUU node into the msgAnimCurve attribute to use animCurve interpolation features." )
				else:
					dAtX = 1.0 - dWt

					plugInput = fnAnimCurve.findPlug("input")	# Mmm sometimes going outside the DAG is good...or it's good to be bad...
					plugInput.setValue(dAtX)					# Do this so we wake up the curve...and then us again.

					hAnimCurveOutput = data.inputValue( poseReader.aAnimCurveOutput )
					dOutput = hAnimCurveOutput.asDouble()
					#sys.__stdout__.write( "dOutput=" + str(dOutput) + "\n")

					dWt = dOutput		# Could do commented out code below, but since we are using in/out to actually drive stuff, just use that anyhow...
					#fnAnimCurve.evaluate(dAtX, dWt)		# Whatever 0-1 we are at, get real value from curve.

			# End of node calc
			# ==========================================


			# Set outputs
			hOutWeight = data.outputValue( poseReader.aOutWeight )
			hOutWeight.setDouble( dWt )
			hOutWeight.setClean()

			data.setClean( plug )

		else:
			return OpenMaya.MStatus.kUnknownParameter

    #
	# poseReader::draw() - Draw routine
	#
	def draw( self, view, path, dispStyle, status ):
		# Get the attrs needed
		#
		thisNode = self.thisMObject()
		#depThis = MFnDependencyNode( thisNode )
		#name = depThis.name()
		dagThis = OpenMaya.MFnDagNode( thisNode )
		name = dagThis.name()
		oParent = dagThis.parent(0)
		dagParent = OpenMaya.MFnDagNode( oParent )
		nameParent = dagParent.name()

		plugDrawDetail = OpenMaya.MPlug( thisNode, self.aDrawDetail)
		nDrawDetail = plugDrawDetail.asInt()

		# If set to zero, means no drawing at all!
		if (nDrawDetail == 0):
			return

		plugDrawCone = OpenMaya.MPlug( thisNode, self.aDrawCone )
		nDrawCone = plugDrawCone.asInt()

		plugDrawText = OpenMaya.MPlug( thisNode, self.aDrawText )
		nDrawText = plugDrawText.asInt()

		plugDrawReverse = OpenMaya.MPlug( thisNode, self.aDrawReverse)
		bDrawReverse = plugDrawReverse.asBool()

		plugDrawHighlight = OpenMaya.MPlug( thisNode, self.aDrawHighlight)
		fDrawHighlight = plugDrawHighlight.asFloat()

		plugOutWeight = OpenMaya.MPlug( thisNode, self.aOutWeight)
		dOutWeight = plugOutWeight.asDouble()

		plugReadAxis = OpenMaya.MPlug( thisNode, self.aReadAxis)
		nReadAxis = plugReadAxis.asInt()

		plugAllowTwist = OpenMaya.MPlug( thisNode, self.aAllowTwist)
		dAllowTwist = plugAllowTwist.asDouble()

		plugAllowRotate = OpenMaya.MPlug( thisNode, self.aAllowRotate)
		dAllowRotate = plugAllowRotate.asDouble()

		plugMinAngle = OpenMaya.MPlug( thisNode, self.aMinAngle)
		dMinAngle = plugMinAngle.asDouble()

		plugMaxAngle = OpenMaya.MPlug( thisNode, self.aMaxAngle)
		dMaxAngle = plugMaxAngle.asDouble()

		if (dMinAngle >= dMaxAngle):
			dMinAngle = dMaxAngle-0.001

		plugAllowTranslate = OpenMaya.MPlug( thisNode, self.aAllowTranslate)
		dAllowTranslate = plugAllowTranslate.asDouble()

		plugMinTranslate = OpenMaya.MPlug( thisNode, self.aMinTranslate)
		dMinTranslate = plugMinTranslate.asDouble()

		plugMaxTranslate = OpenMaya.MPlug( thisNode, self.aMaxTranslate)
		dMaxTranslate = plugMaxTranslate.asDouble()

		if (dMinTranslate >= dMaxTranslate):
			dMinTranslate = dMaxTranslate-0.001

		# End of getting attrs
		bShaded = False

		# now even if we want shaded...if we are not in a shaded mode, de-activate it!
		if ( dispStyle != OpenMayaUI.M3dView().kFlatShaded and dispStyle != OpenMayaUI.M3dView().kGouraudShaded ):
		    bShaded = False

		# Figure override color
		colO = OpenMaya.MColor()
		bColOverride = False
		bSel = False	# are we selected?

		# And now a few overrides for selection, last selection or
		#	template... So make nice colors
		#
		# From M3dView::DisplayStatus status  in the draw() command
		if (status == OpenMayaUI.M3dView().kLead):
			colO = OpenMaya.MColor(0.26, 1.0, 0.64)		# maya green
			bColOverride = True
			bSel = True

		elif (status == OpenMayaUI.M3dView().kActive):
			colO = OpenMaya.MColor(1.0, 1.0, 1.0)		# maya white
			bColOverride = True
			bSel = True

		elif (status == OpenMayaUI.M3dView().kActiveAffected):
			colO = OpenMaya.MColor(0.78, 1.0, 0.78)		# maya magenta
			bColOverride = True

		elif (status == OpenMayaUI.M3dView().kTemplate):
			colO = OpenMaya.MColor(0.47, 0.47, 0.47)		# maya template gray
			bColOverride = True

		elif (status == OpenMayaUI.M3dView().kActiveTemplate):
			colO = OpenMaya.MColor(1.0, 0.47, 0.47)		# maya selected template pink
			bColOverride = True

		else:
			colO = OpenMaya.MColor(0.1, 0.2, 0.7)		# else set color as desired
			fDrawHighlight = 0.0							# If default, then set highlght to 0 so always do user color.


		view.beginGL() 	# Start openGL

		# Push the color settings
		self.glFT.glPushAttrib( OpenMayaRender.MGL_CURRENT_BIT | OpenMayaRender.MGL_POINT_BIT  | OpenMayaRender.MGL_LINE_BIT )
		self.glFT.glBegin( OpenMayaRender.MGL_LINES )

		view.setDrawColor( colO )	# Set color as desired

		dHead = 0.1
		nSegs = nDrawDetail + 1
		dNeg = 1.0
		if (bDrawReverse):
			dNeg = -1.0

		# First draw X-Axis
		if (nReadAxis == 0 or dAllowTwist != 1.0):

			view.setDrawColor( self.blendColor(OpenMaya.MColor(1.0, 0.0, 0.0), colO, fDrawHighlight) )	# Set color as desired


				# Shaft
			self.glFT.glVertex3d( 0.0, 0.0, 0.0)
			self.glFT.glVertex3d( 1.0*dNeg, 0.0, 0.0)

			if (nReadAxis == 0 and nDrawDetail >= 2):

					# Head
				self.glFT.glVertex3d( (1.0+dHead)*dNeg, 0.0, 0.0)
				self.glFT.glVertex3d( 1.0*dNeg, (dHead/2.0), (dHead/2.0))

				self.glFT.glVertex3d( (1.0+dHead)*dNeg, 0.0, 0.0)
				self.glFT.glVertex3d( 1.0*dNeg, (dHead/2.0), -(dHead/2.0))

				self.glFT.glVertex3d( (1.0+dHead)*dNeg, 0.0, 0.0)
				self.glFT.glVertex3d( 1.0*dNeg, -(dHead/2.0), -(dHead/2.0))

				self.glFT.glVertex3d( (1.0+dHead)*dNeg, 0.0, 0.0)
				self.glFT.glVertex3d( 1.0*dNeg, -(dHead/2.0), (dHead/2.0))

					# Base square of head
				self.glFT.glVertex3d( 1.0*dNeg, (dHead/2.0), (dHead/2.0))
				self.glFT.glVertex3d( 1.0*dNeg, (dHead/2.0), -(dHead/2.0))

				self.glFT.glVertex3d( 1.0*dNeg, (dHead/2.0), -(dHead/2.0))
				self.glFT.glVertex3d( 1.0*dNeg, -(dHead/2.0), -(dHead/2.0))

				self.glFT.glVertex3d( 1.0*dNeg, -(dHead/2.0), -(dHead/2.0))
				self.glFT.glVertex3d( 1.0*dNeg, -(dHead/2.0), (dHead/2.0))

				self.glFT.glVertex3d( 1.0*dNeg, -(dHead/2.0), (dHead/2.0))
				self.glFT.glVertex3d( 1.0*dNeg, (dHead/2.0), (dHead/2.0))

			if (nDrawCone == 1 or (nDrawCone == 2 and bSel)):

				if (nReadAxis == 0 and nDrawDetail >= 3 and dAllowRotate != 1.0):

					view.setDrawColor( self.blendColor(OpenMaya.MColor(0.8, 0.0, 0.0), colO, fDrawHighlight) )	# Set color as desired

						# Draw MAX Circle
						# Figure where down primary axis the circle will be drawn
						# and also the radius at the point.
						#
					dLen = dNeg * math.cos(dMaxAngle/180.0*3.14159)	# As angle from 0..180, dLen= 1.0..-1.0
					dRad = math.sin(dMaxAngle/180.0*3.14159)	# As angle from 0..90..180, dRad=0.0...1.0...0.0

					# Now draw circle
					for i in range(nSegs):

						dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
						dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
						a = dRad * math.cos(dPct)
						b = dRad * math.sin(dPct)
						a2 = dRad * math.cos(dPct2)
						b2 = dRad * math.sin(dPct2)

						self.glFT.glVertex3d( 0.0, 0.0, 0.0 )
						self.glFT.glVertex3d( dLen, a, b )

						self.glFT.glVertex3d( dLen, a, b )
						self.glFT.glVertex3d( dLen, a2, b2 )


						# Draw MIN Circle
						# Figure where down primary axis the circle will be drawn
						# and also the radius at the point.
						#
					dLen = dNeg * math.cos(dMinAngle/180.0*3.14159)		# As angle from 0..180, dLen= 1.0..-1.0
					dRad = math.sin(dMinAngle/180.0*3.14159)			# As angle from 0..90..180, dRad=0.0...1.0...0.0

					view.setDrawColor( self.blendColor(OpenMaya.MColor(1.0, 0.0, 0.0), colO, fDrawHighlight) );	# Set color as desired

					# Now draw circle
					for i in range(nSegs):

						dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
						dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
						a = dRad * math.cos(dPct)
						b = dRad * math.sin(dPct)
						a2 = dRad * math.cos(dPct2)
						b2 = dRad * math.sin(dPct2)

						self.glFT.glVertex3d( 0.0, 0.0, 0.0 ) ;
						self.glFT.glVertex3d( dLen, a, b ) ;

						self.glFT.glVertex3d( dLen, a, b ) ;
						self.glFT.glVertex3d( dLen, a2, b2 ) ;

			#end of if draw cone x

		# End of Draw X


		# Draw Y-Axis
		if (nReadAxis == 1 or dAllowTwist != 1.0):

			view.setDrawColor( self.blendColor( OpenMaya.MColor(0.0, 1.0, 0.0), colO, fDrawHighlight) )	# Set color as desired

				# Shaft
			self.glFT.glVertex3d( 0.0, 0.0, 0.0)
			self.glFT.glVertex3d( 0.0, 1.0*dNeg, 0.0)

			if (nReadAxis == 1 and nDrawDetail >= 2):

					# Head
				self.glFT.glVertex3d( 0.0, (1.0+dHead)*dNeg, 0.0)
				self.glFT.glVertex3d( (dHead/2.0), 1.0*dNeg, (dHead/2.0))

				self.glFT.glVertex3d( 0.0, (1.0+dHead)*dNeg, 0.0)
				self.glFT.glVertex3d( (dHead/2.0), 1.0*dNeg, -(dHead/2.0))

				self.glFT.glVertex3d( 0.0, (1.0+dHead)*dNeg, 0.0)
				self.glFT.glVertex3d( -(dHead/2.0), 1.0*dNeg, -(dHead/2.0))

				self.glFT.glVertex3d( 0.0, (1.0+dHead)*dNeg, 0.0)
				self.glFT.glVertex3d( -(dHead/2.0), 1.0*dNeg, (dHead/2.0))

					# Base square of head
				self.glFT.glVertex3d( (dHead/2.0), 1.0*dNeg, (dHead/2.0))
				self.glFT.glVertex3d( (dHead/2.0), 1.0*dNeg, -(dHead/2.0))

				self.glFT.glVertex3d( (dHead/2.0), 1.0*dNeg, -(dHead/2.0))
				self.glFT.glVertex3d( -(dHead/2.0), 1.0*dNeg, -(dHead/2.0))

				self.glFT.glVertex3d( -(dHead/2.0), 1.0*dNeg, -(dHead/2.0))
				self.glFT.glVertex3d( -(dHead/2.0), 1.0*dNeg, (dHead/2.0))

				self.glFT.glVertex3d( -(dHead/2.0), 1.0*dNeg, (dHead/2.0))
				self.glFT.glVertex3d( (dHead/2.0), 1.0*dNeg, (dHead/2.0))


			if (nDrawCone == 1 or (nDrawCone == 2 and bSel)):

				if (nReadAxis == 1 and nDrawDetail >= 3 and dAllowRotate != 1.0):

					view.setDrawColor( self.blendColor(OpenMaya.MColor(0.0, 0.8, 0.0), colO, fDrawHighlight) )	# Set color as desired

						# Draw MAX Circle
						# Figure where down primary axis the circle will be drawn
						# and also the radius at the point.
						#
					dLen = dNeg * math.cos(dMaxAngle/180.0*3.14159)	# As angle from 0..180, dLen= 1.0..-1.0
					dRad = math.sin(dMaxAngle/180.0*3.14159)	# As angle from 0..90..180, dRad=0.0...1.0...0.0

					# Now draw circle
					for i in range (nSegs):

						dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
						dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
						a = dRad * math.cos(dPct)
						b = dRad * math.sin(dPct)
						a2 = dRad * math.cos(dPct2)
						b2 = dRad * math.sin(dPct2)

						self.glFT.glVertex3d( 0.0, 0.0, 0.0 )
						self.glFT.glVertex3d( a, dLen, b )

						self.glFT.glVertex3d( a, dLen, b )
						self.glFT.glVertex3d( a2, dLen, b2 )


						# Draw MIN Circle
						# Figure where down primary axis the circle will be drawn
						# and also the radius at the point.
						#
					dLen = dNeg * math.cos(dMinAngle/180.0*3.14159)		# As angle from 0..180, dLen= 1.0..-1.0
					dRad = math.sin(dMinAngle/180.0*3.14159)			# As angle from 0..90..180, dRad=0.0...1.0...0.0

					view.setDrawColor( self.blendColor(OpenMaya.MColor(0.0, 1.0, 0.0), colO, fDrawHighlight) )	# Set color as desired

					# Now draw circle
					for i in range (nSegs):

						dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
						dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
						a = dRad * math.cos(dPct)
						b = dRad * math.sin(dPct)
						a2 = dRad * math.cos(dPct2)
						b2 = dRad * math.sin(dPct2)

						self.glFT.glVertex3d( 0.0, 0.0, 0.0 )
						self.glFT.glVertex3d( a, dLen, b )

						self.glFT.glVertex3d( a, dLen, b )
						self.glFT.glVertex3d( a2, dLen, b2 )

			# end of draw Y cone

		# End of draw Y


		# Draw Z-Axis
		if (nReadAxis == 2 or dAllowTwist != 1.0):

			view.setDrawColor( self.blendColor(OpenMaya.MColor(0.0, 0.0, 1.0), colO, fDrawHighlight) )	# Set color as desired


				# Shaft
			self.glFT.glVertex3d( 0.0, 0.0, 0.0)
			self.glFT.glVertex3d( 0.0, 0.0, 1.0*dNeg)

			if (nReadAxis == 2 and nDrawDetail >= 2):

					# Head
				self.glFT.glVertex3d( 0.0, 0.0, (1.0+dHead)*dNeg)
				self.glFT.glVertex3d( (dHead/2.0), (dHead/2.0), 1.0*dNeg)

				self.glFT.glVertex3d( 0.0, 0.0, (1.0+dHead)*dNeg)
				self.glFT.glVertex3d( (dHead/2.0), -(dHead/2.0), 1.0*dNeg)

				self.glFT.glVertex3d( 0.0, 0.0, (1.0+dHead)*dNeg)
				self.glFT.glVertex3d( -(dHead/2.0), -(dHead/2.0), 1.0*dNeg)

				self.glFT.glVertex3d( 0.0, 0.0, (1.0+dHead)*dNeg)
				self.glFT.glVertex3d( -(dHead/2.0), (dHead/2.0), 1.0*dNeg)

					# Base square of head
				self.glFT.glVertex3d( (dHead/2.0), (dHead/2.0), 1.0*dNeg)
				self.glFT.glVertex3d( (dHead/2.0), -(dHead/2.0), 1.0*dNeg)

				self.glFT.glVertex3d( (dHead/2.0), -(dHead/2.0), 1.0*dNeg)
				self.glFT.glVertex3d( -(dHead/2.0), -(dHead/2.0), 1.0*dNeg)

				self.glFT.glVertex3d( -(dHead/2.0), -(dHead/2.0), 1.0*dNeg)
				self.glFT.glVertex3d( -(dHead/2.0), (dHead/2.0), 1.0*dNeg)

				self.glFT.glVertex3d( -(dHead/2.0), (dHead/2.0), 1.0*dNeg)
				self.glFT.glVertex3d( (dHead/2.0), (dHead/2.0), 1.0*dNeg)


			if (nDrawCone == 1 or (nDrawCone == 2 and bSel)):

				if (nReadAxis == 2 and nDrawDetail >= 3 and dAllowRotate != 1.0):

					view.setDrawColor( self.blendColor(OpenMaya.MColor(0.0, 0.0, 0.8), colO, fDrawHighlight) )	# Set color as desired


						# Draw MAX Circle
						# Figure where down primary axis the circle will be drawn
						# and also the radius at the point.
						#
					dLen = dNeg * math.cos(dMaxAngle/180.0*3.14159)		# As angle from 0..180, dLen= 1.0..-1.0
					dRad = math.sin(dMaxAngle/180.0*3.14159)			# As angle from 0..90..180, dRad=0.0...1.0...0.0

					# Now draw circle
					for i in range (nSegs):

						dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
						dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
						a = dRad * math.cos(dPct)
						b = dRad * math.sin(dPct)
						a2 = dRad * math.cos(dPct2)
						b2 = dRad * math.sin(dPct2)

						self.glFT.glVertex3d( 0.0, 0.0, 0.0 )
						self.glFT.glVertex3d( a, b, dLen )

						self.glFT.glVertex3d( a, b, dLen )
						self.glFT.glVertex3d( a2, b2, dLen )


						# Draw MIN Circle
						# Figure where down primary axis the circle will be drawn
						# and also the radius at the point.
						#
					dLen = dNeg * math.cos(dMinAngle/180.0*3.14159)		# As angle from 0..180, dLen= 1.0..-1.0
					dRad = math.sin(dMinAngle/180.0*3.14159)					# As angle from 0..90..180, dRad=0.0...1.0...0.0

					view.setDrawColor( self.blendColor(OpenMaya.MColor(0.0, 0.0, 1.0), colO, fDrawHighlight) );	# Set color as desired

					# Now draw circle
					for i in range (nSegs):

						dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
						dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
						a = dRad * math.cos(dPct)
						b = dRad * math.sin(dPct)
						a2 = dRad * math.cos(dPct2)
						b2 = dRad * math.sin(dPct2)

						self.glFT.glVertex3d( 0.0, 0.0, 0.0 )
						self.glFT.glVertex3d( a, b, dLen )

						self.glFT.glVertex3d( a, b, dLen )
						self.glFT.glVertex3d( a2, b2, dLen )

				# end of draw z cone

			# end of draw Z


		# Draw Translate
		if (dAllowTranslate != 1.0 and (nDrawCone == 1 or (nDrawCone == 2 and bSel)) ):

			view.setDrawColor( self.blendColor(OpenMaya.MColor(1.0, 0.0, 0.0), colO, fDrawHighlight) )	# Set color as desired

					# Draw MIN Sphere
					#
			dRad = dMinTranslate
			for i in range (nSegs):

				dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
				dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
				a = dRad * math.cos(dPct)
				b = dRad * math.sin(dPct)
				a2 = dRad * math.cos(dPct2)
				b2 = dRad * math.sin(dPct2)
				self.glFT.glVertex3d( a, b, 0 )
				self.glFT.glVertex3d( a2, b2, 0 )

				self.glFT.glVertex3d( 0, a, b )
				self.glFT.glVertex3d( 0, a2, b2 )

				self.glFT.glVertex3d( a, 0, b )
				self.glFT.glVertex3d( a2, 0, b2 )

			view.setDrawColor( self.blendColor( OpenMaya.MColor(1.0, 1.0, 0.0), colO, fDrawHighlight) )	# Set color as desired

					# Draw MAX Sphere
					#
			dRad = dMaxTranslate
			for i in range (nSegs):

				dPct = 2.0 * 3.14159 * ( i / (nSegs-1.0) )
				dPct2 = 2.0 * 3.14159 * ( (i+1.0) / (nSegs-1.0) )
				a = dRad * math.cos(dPct)
				b = dRad * math.sin(dPct)
				a2 = dRad * math.cos(dPct2)
				b2 = dRad * math.sin(dPct2)
				self.glFT.glVertex3d( a, b, 0 )
				self.glFT.glVertex3d( a2, b2, 0 )

				self.glFT.glVertex3d( 0, a, b )
				self.glFT.glVertex3d( 0, a2, b2 )

				self.glFT.glVertex3d( a, 0, b )
				self.glFT.glVertex3d( a2, 0, b2 )

			# end of draw translate



		self.glFT.glEnd() # End of LINES


		# Draw Weight Text
		if (nDrawText == 1 or (nDrawText == 2 and bSel)):

			col0 = OpenMaya.MColor(0.0, 1.0, 1.0)
			col1 = OpenMaya.MColor(1.0, 1.0, 0.0)
			colText = OpenMaya.MColor( col0 * (1.0-float(dOutWeight))) + ( col1 * float(dOutWeight))
			view.setDrawColor( colText )

			dDrawLen = (1.0 + (dHead*1.5)) * dNeg
			ptDraw = OpenMaya.MPoint()
			if (nReadAxis == 0):
				ptDraw = OpenMaya.MPoint(dDrawLen, 0,0)
			elif (nReadAxis == 1):
				ptDraw = OpenMaya.MPoint(0, dDrawLen, 0)
			elif (nReadAxis == 2):
				ptDraw = OpenMaya.MPoint(0,0, dDrawLen)

			#char str[256];
			#sprintf( str, "%s: %1.3f", nameParent.asChar(), dOutWeight )
			drawStr = (nameParent + ": " + str(dOutWeight))
			view.drawText( drawStr, ptDraw, OpenMayaUI.M3dView().kLeft )


		self.glFT.glPopAttrib()
		view.endGL()		# End openGL

    #
	# ccMuscleDisplay::isBounded - Do we have our own bounding box?
	#
	def isBounded( self ):
		return False

	#private:
	# --------------------------------------------------------------------------
	#
	# poseReader::calcWtFromAngle() - Calcs weight based on a 0-180 angle.
	#
	def __calcWtFromAngle(self, dAngle, dMinAngle, dMaxAngle):

		dWt = 0.0

		if (dAngle >= dMaxAngle):
			dWt = 0.0
		elif (dAngle <= dMinAngle):
			dWt = 1.0
		else:

			dDelta = dMaxAngle - dMinAngle
			if (dDelta > 0):
				dWt = 1.0 - ((dAngle - dMinAngle) / dDelta)
			else:
				dWt = 0.0

		return dWt

	#
	# poseReader::smoothStep() - Take a value from 0-1 and instead of having it be linear,
	#		make it ease out and then in from the 0 and 1 locations.
	#
	def __smoothStep(self, dVal):

		# x^2*(3-2x)
		dRet = dVal * dVal * (3.0 - (2.0 * dVal) )
		return dRet

	#
	# poseReader::smoothGaussian() - Take a value from 0-1 and instead of having it be linear,
	#		make it ease out and then in from the 0 and 1 locations.  This has more of a longer
	#		ease than a smoothstep and so a faster falloff in the middle.
	#
	def __smoothGaussian(self, dVal):

		# 1.0 - exp( (-1 * x^2 ) / (2*sigma^2) )

		dSigma = 1.0		# Must be >0.   As drops to zero, higher value one lasts longer.

		dRet = (1.0 - math.exp( -1.0 * (dVal*dVal) * 10.0  / (2.0 * dSigma*dSigma)  ) )	# RBF
		return dRet

	#
	# poseReader::blendColor() - Blend between col1 and colr2 as fBlend goes from 0 to 1
	#
	def blendColor(self, col1, col2, fBlend):

		col1 = ( col1 * (1.0 - fBlend) )
		col2 = ( col2 * fBlend )
		col = col1 + col2

		return col


# --------------------------------------------------------------------------
#
# initializePlugin() - Main load of plugin
#
#	Description:
#		this method is called when the plug-in is loaded into Maya.  It
#		registers all of the services that this plug-in provides with
#		Maya.
#
#	Arguments:
#		obj - a handle to the plug-in object (use MFnPlugin to access it)
#
#
def initializePlugin( obj ):

	plugin = OpenMayaMPx.MFnPlugin( obj, "Autodesk", "8.5", "Any")

	try:
		plugin.registerNode( NAME_POSEREADER, ID_POSEREADER, poseReader().creator, poseReader().initialize, OpenMayaMPx.MPxNode.kLocatorNode )
	except:
		sys.stderr.write( "Failed to register node: %s" % NAME_POSEREADER )
		raise

	try:
		plugin.registerNode( NAME_MULTITRIGGER, ID_MULTITRIGGER, multiTrigger().creator, multiTrigger().initialize, OpenMayaMPx.MPxNode.kDependNode );
	except:
		sys.stderr.write( "Failed to register node: %s" % NAME_MULTITRIGGER )
		raise


	OpenMaya.MGlobal.displayInfo( NAME_POSEREADER + " " + str(VERSION) + " - Created: " + CREATEDATE )
	OpenMaya.MGlobal.displayInfo( "poseReader converted to Python by Ryan L Trowbridge")
	OpenMaya.MGlobal.displayInfo( "poseReader Copyright 2004,2005 Michael B. Comet")
	OpenMaya.MGlobal.displayInfo("poseReader comes with ABSOLUTELY NO WARRANTY; for details read the")
	OpenMaya.MGlobal.displayInfo("license.txt file.  This is free software, and you are welcome to")
	OpenMaya.MGlobal.displayInfo("redistribute it under certain conditions; See license.txt for details.")


# --------------------------------------------------------------------------
#
# uninitializePlugin() - Disable/unload main plugin
#
#	Description:
#		this method is called when the plug-in is unloaded from Maya. It
#		deregisters all of the services that it was providing.
#
#	Arguments:
#		obj - a handle to the plug-in object (use MFnPlugin to access it)
#
#
def uninitializePlugin( obj ):

	plugin = OpenMayaMPx.MFnPlugin( obj )

	try:
		plugin.deregisterNode( ID_POSEREADER )
	except:
		sys.stderr.write( "Failed to deregister node: %s" % NAME_POSEREADER )

	try:
		plugin.deregisterNode( ID_MULTITRIGGER )
	except:
		sys.stderr.write( "Failed to deregister node: %s" % NAME_MULTITRIGGER )
