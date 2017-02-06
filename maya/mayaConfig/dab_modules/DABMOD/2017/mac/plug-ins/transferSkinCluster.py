# ----------------------------------------------------------------------------------------------
#
# transferSkinCluster.py
# v1.1
#
# export/import weights of the selected skinCluster
#
# Ingo Clemens
# www.braverabbit.de
#
# Copyright brave rabbit, Ingo Clemens 2012.
# All rights reserved.
#
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
#
#	USE AND MODIFY AT YOUR OWN RISK!!
#
# ----------------------------------------------------------------------------------------------


import os

import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaAnim as OpenMayaAnim

import maya.cmds as cmd
import maya.mel as mel

kPluginCmdName = 'transferSkinCluster'


# --------------------------------------------------------------------------------
# argument flags
# --------------------------------------------------------------------------------

helpFlag = '-h'
helpFlagLong = '-help'

fileFlag = '-f'
fileFlagLong = '-file'

modeFlag = '-m'
modeFlagLong = '-mode'

orderFlag = '-ro'
orderFlagLong = '-reverseOrder'

helpText = ''
helpText += '\n Description: The command exports and imports the selected skinCluster to/from a file.'
helpText += '\n'
helpText += '\n Flags: transferSkinCluster -h    -help          <n/a>       this message'
helpText += '\n                            -m    -mode          <int>       write (default=0) or read (1)'
helpText += '\n                            -ro   -reverseOrder  <int>       from file (default=0) or reversed (1)'
helpText += '\n                            -f    -file          <string>    the file name for the skinCluster weight data'
helpText += '\n'
helpText += '\n Usage:   Execute the command with the following arguments:'
helpText += '\n Execute: transferSkinCluster -m <mode> -f <file name>;';


# --------------------------------------------------------------------------------
# command
# --------------------------------------------------------------------------------

class transferSkinCluster(OpenMayaMPx.MPxCommand):
	
	def __init__( self ):
		OpenMayaMPx.MPxCommand.__init__(self)
	
	def doIt( self, args ):
		
		modeArg = 0
		fileName = ''
		orderArg = 0
		
		# parse the arguments.
		argData = OpenMaya.MArgDatabase(self.syntax(), args)
		
		if argData.isFlagSet(helpFlag):
			self.setResult(helpText)
			return()
		
		if argData.isFlagSet(modeFlag):
			modeArg = argData.flagArgumentDouble(modeFlag, 0)
		if argData.isFlagSet(orderFlag):
			orderArg = argData.flagArgumentDouble(orderFlag, 0)
		if argData.isFlagSet(fileFlag):
			fileName = argData.flagArgumentString(fileFlag, 0)
		else:
			OpenMaya.MGlobal.displayError(kPluginCmdName + ' needs file name flag.')
			return();
		
		if fileName == '':
			OpenMaya.MGlobal.displayError(kPluginCmdName + ' file name is not specified.')
			return()
		
		if modeArg < 0 or modeArg > 1:
			OpenMaya.MGlobal.displayError(kPluginCmdName + ' mode needs to be set to either 0 for \'write\' or 1 for \'read\'.')
			return()
		
		start = cmd.timerX()
		msgString = ''
		
		result = 0
		if modeArg == 0:
			result = self.writeWeights(fileName)
			msgString = 'exported to '
		else:
			result = self.readWeights(fileName, orderArg)
			msgString = 'imported from '
		
		doneTime = cmd.timerX(startTime=start)
		if result == 1:
			OpenMaya.MGlobal.displayInfo('transferSkinCluster command took %.02f seconds' % doneTime)
			OpenMaya.MGlobal.displayInfo('Weights ' + msgString + '\'' + fileName + '\'')


	# --------------------------------------------------------------------------------
	# read the weights file
	# --------------------------------------------------------------------------------

	def writeWeights( self, fileName ):
		
		# get the current selection
		skinClusterNode = cmd.ls(sl=True, fl=True)
		if len(skinClusterNode) != 0:
				skinClusterNode = skinClusterNode[0]
		else:
			OpenMaya.MGlobal.displayError('Select a skinCluster node to export.')
			return(-1)

		# check if it's a skinCluster
		if cmd.nodeType(skinClusterNode) != 'skinCluster':
			OpenMaya.MGlobal.displayError('Selected node is not a skinCluster.')
			return(-1)
		
		# get the MFnSkinCluster
		sel = OpenMaya.MSelectionList()
		OpenMaya.MGlobal.getActiveSelectionList(sel)
		skinClusterObject = OpenMaya.MObject()
		sel.getDependNode(0, skinClusterObject)
		skinClusterFn = OpenMayaAnim.MFnSkinCluster(skinClusterObject)
		
		# get the influence objects
		infls = cmd.skinCluster(skinClusterNode, q=True, inf=True)
		if len(infls) == 0:
			OpenMaya.MGlobal.displayError('No influence objects found for skinCluster %s.' % skinClusterNode)
			return(-1)
		
		# get the connected shape node
		shape = cmd.skinCluster(skinClusterNode, q=True, g=True)[0]
		if len(infls) == 0:
			OpenMaya.MGlobal.displayError('No connected shape nodes found.')
			return(-1)
		
		# get the dag path of the shape node
		cmd.select(shape, r=True)
		sel = OpenMaya.MSelectionList()
		OpenMaya.MGlobal.getActiveSelectionList(sel)
		shapeDag = OpenMaya.MDagPath()
		sel.getDagPath(0, shapeDag)
		# create the geometry iterator
		geoIter = OpenMaya.MItGeometry(shapeDag)
		
		# open the file for writing
		try:
			weightFile = open(fileName, 'wb')
		except:
			OpenMaya.MGlobal.displayError('A file error has occured for file \'' + fileName + '\'.')
			return(-1)
		
		# write all influences and the shape node to the file
		for i in range(0, len(infls), 1):
			weightFile.write(infls[i] + " ")
		weightFile.write(shape + '\n')
		
		weightFile.write(skinClusterNode + '\n')
		
		# write the attributes of the skinCluster node to the file
		result = cmd.getAttr(skinClusterNode + ".normalizeWeights")
		weightFile.write('-nw %s ' % result)
		result = cmd.getAttr(skinClusterNode + ".maxInfluences")
		weightFile.write('-mi %s ' % result)
		result = cmd.getAttr(skinClusterNode + ".dropoff")[0][0]
		weightFile.write('-dr %s\n' % result)
        
		# create a pointer object for the influence count of the MFnSkinCluster
		infCount = OpenMaya.MScriptUtil()
		infCountPtr = infCount.asUintPtr()
		OpenMaya.MScriptUtil.setUint(infCountPtr, 0)
		
		# get the skinCluster weights
		value = OpenMaya.MDoubleArray()
		while geoIter.isDone() == False:
			skinClusterFn.getWeights(shapeDag, geoIter.currentItem(), value, infCountPtr)
			for j in range(0, len(infls)):
				if value[j] > 0:
					lineArray = [geoIter.index(), infls[j], j, value[j]]
					weightFile.write(str(lineArray) + '\n')
			geoIter.next()
		
		weightFile.close()
		return(1)
		

	# --------------------------------------------------------------------------------
	# read the weights file
	# --------------------------------------------------------------------------------

	def readWeights( self, fileName, reverseOrder ):
		
		# open the file for reading
		try:
			weightFile = open(fileName, 'rb')
		except:
			OpenMaya.MGlobal.displayError('A file error has occured for file \'' + fileName + '\'.')
			return(-1)
		
		weightData = weightFile.read()
		weightLines = weightData.split('\n')
		weightFile.close()
		
		normalization = 1
		
		# variables for writing a range of influences
		weightString = ''
		inflStart = -1
		inflEnd = -1
		setCount = 0
		writeData = 0
		
		# --------------------------------------------------------------------------------
		# the first line contains the joints and skin shape
		# --------------------------------------------------------------------------------
		objects = weightLines[0]
		items = objects.split(' ')
		shape = items[len(items) - 1]
		
		# --------------------------------------------------------------------------------
		# the second line contains the name of the skin cluster
		# --------------------------------------------------------------------------------
		skinClusterName = weightLines[1]
		
		# --------------------------------------------------------------------------------
		# the third line contains the values for the skin cluster
		# --------------------------------------------------------------------------------
		objects = objects.split(' ')
		if reverseOrder == 1:
			objects = objects[::-1]
			objects.pop(0)
			objects.append(shape)

		# select the influences and the skin shape
		try:
			cmd.select(objects, r=True)
		except:
			weightFile.close()
			return()
		
		# check if the geometry is not already bound
		history = cmd.listHistory(shape, f=0, bf=1)
		for h in history:
			if cmd.nodeType(h) == 'skinCluster':
				OpenMaya.MGlobal.displayError(shape + ' is already connected to a skinCluster.')
				return(-1)
		
		# check for the version
		# up to Maya 2012 the bind method flag is not available
		version = mel.eval('getApplicationVersionAsFloat()')
		bindMethod = '-bm 0 '
		if version < 2013:
			bindMethod = '-ih '
		
		# create the new skinCluster
		newSkinCluster = mel.eval('newSkinCluster \"-tsb ' + bindMethod + weightLines[2] + '-omi true -rui false\"')[0]
		cmd.rename(newSkinCluster, skinClusterName)
		
		# get the current normalization and store it
		# it will get re-applied after applying all the weights
		normalization = cmd.getAttr(skinClusterName + '.nw')
		# turn off the normalization to correctly apply the stored skin weights
		cmd.setAttr((skinClusterName + '.nw'), 0)
		# pruning the skin weights to zero is much faster
		# than iterating through all components and setting them to 0
		cmd.skinPercent(skinClusterName, shape, prw=100, nrm=0)
		
		# allocate memory for the number of components to set
		weights = eval(weightLines[len(weightLines) - 2])
		# get the index of the last component stored in the weight list
		maxIndex = weights[0]
		cmd.select(skinClusterName, r=True)
		cmdString = ('setAttr -s ' + str(maxIndex + 1) + ' \".wl\"')
		OpenMaya.MGlobal.executeCommand(cmdString)
					
		# --------------------------------------------------------------------------------
		# apply the weight data
		# --------------------------------------------------------------------------------
		
		# timer for timing the read time without the smooth binding
		#start = cmd.timerX()
		
		for l in range(3, len(weightLines) - 1):
			
			weights = eval(weightLines[l])
			weightsNext = ''
			# also get the next line for checking if the component changes
			# but only if it's not the end of the list
			if l < len(weightLines) - 2:
				weightsNext = eval(weightLines[l + 1])
			else:
				weightsNext = weights
				writeData = 1
			
			compIndex = weights[0]
						
			# --------------------------------------------------------------------------------
			# construct the setAttr string
			# i.e. setAttr -s 4 ".wl[9].w[0:3]"  0.0003 0.006 0.496 0.496
			# --------------------------------------------------------------------------------
			
			# start a new range
			if inflStart == -1:
				inflEnd = inflStart = weights[2]
			else:
				# if the current component is the next in line
				if inflEnd == weights[2] - 1:
					inflEnd = weights[2]
				# if influences were dropped because of zero weight
				else:
					# fill the weight string inbetween with zeros
					for x in range(inflEnd + 1, weights[2]):
						weightString += '0 '
						setCount += 1
					inflEnd = weights[2]
				
			# add the weight to the weight string
			weightString += str(weights[3]) + ' '
			# increase the number of weights to be set
			setCount += 1
				
			# if the next line is for the next index set the weights
			if compIndex != weightsNext[0]:
				writeData = 1
				
			if writeData == 1:
				# decide if a range or a single influence index is written
				rangeString = ':' + str(inflEnd)
				if inflEnd == inflStart:
					rangeString = ''
					
				cmdString = ('setAttr -s ' + str(setCount) + ' \".weightList[' + str(compIndex) + '].weights[' + str(inflStart) + rangeString + ']\" ' + weightString)
				OpenMaya.MGlobal.executeCommand(cmdString)
					
				# reset and start over
				inflStart = inflEnd = -1
				writeData = 0
				setCount = 0
				weightString = ''
				
		cmd.setAttr((skinClusterName + '.nw'), normalization)
		
		#doneTime = cmd.timerX(startTime=start)
		#OpenMaya.MGlobal.displayInfo('%.02f seconds' % doneTime)
		
		return(1)


# --------------------------------------------------------------------------------
# define the syntax, needed to make it work with mel and python
# --------------------------------------------------------------------------------

# creator
def cmdCreator():
	return OpenMayaMPx.asMPxPtr(transferSkinCluster())
	
def syntaxCreator():
	syn = OpenMaya.MSyntax()
	syn.addFlag(helpFlag, helpFlagLong);
	syn.addFlag(fileFlag, fileFlagLong, OpenMaya.MSyntax.kString);
	syn.addFlag(modeFlag, modeFlagLong, OpenMaya.MSyntax.kLong);
	syn.addFlag(orderFlag, orderFlagLong, OpenMaya.MSyntax.kLong);
	return syn

# initialization
def initializePlugin( mobject ):
	mplugin = OpenMayaMPx.MFnPlugin(mobject, 'Ingo Clemens', '1.1', 'Any')
	try:
		mplugin.registerCommand(kPluginCmdName, cmdCreator, syntaxCreator)
	except:
		sys.stderr.write('Failed to register command: %s\n' % kPluginCmdName)
		raise

def uninitializePlugin( mobject ):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterCommand(kPluginCmdName)
	except:
		sys.stderr.write( 'Failed to unregister command: %s\n' % kPluginCmdName )
		raise


melProcs = '''

//----------------------------------------------------------------------------------------------
//
// checking for the skinWeights folder
//
//----------------------------------------------------------------------------------------------

global proc string icTransferSkinClusterCheckDir()
{
	string $weightPath = "data/skinWeights";
	string $workDir = `workspace -q -rd`;
	string $tempDir = `workspace -q -dir`;
	workspace -dir $workDir;

	if (!`filetest -d ($workDir + $weightPath)`)
	{
		string $confirm = `confirmDialog 
					-t "Create Missing Directory"
					-m "Create a 'skinWeights' folder at the current projects data path?"
					-ma center
					-b "OK" -b "Cancel"
					-db "OK" -cb "Cancel" -ds "Cancel"`;
		if ($confirm == "OK")
		{
			workspace -cr $weightPath;
			$workDir += $weightPath + "/";
		}
		else
			$workDir += "data/";
	}
	else
		$workDir += $weightPath + "/";

	print ("// Skin weights directory is set to '" + $workDir + "' //\\n");
	
	workspace -dir $tempDir;
	return $workDir;
}

//----------------------------------------------------------------------------------------------
//
// create the window
//
//----------------------------------------------------------------------------------------------

global proc icTransferSkinClusterWindow( string $win )
{
	if (`window -exists $win`)
		deleteUI $win;

	window -t "Import SkinCluster Weights" -w 300 -h 200 $win;
	if (`windowPref -exists $win`)
		windowPref -e -wh 300 200 $win;
	
	columnLayout -adj 1;
		textScrollList -ams 0 weightTSL;
		button -l "Import" bApply;
}

//----------------------------------------------------------------------------------------------
//
// button callbacks
//
//----------------------------------------------------------------------------------------------

global proc icTransferSkinClusterButtonCallback( string $workDir, int $order )
{
	button -e -c ("icTransferSkinClusterImportWeight \\"" + $workDir + "\\" " + $order) bApply;
}

//----------------------------------------------------------------------------------------------
//
// import the selected skinCluster
//
//----------------------------------------------------------------------------------------------

global proc icTransferSkinClusterImportWeight( string $workDir, int $order  )
{
	string $selection[] = `textScrollList -q -si weightTSL`;
	if (size($selection[0]))
		transferSkinCluster -m 1 -ro $order -f ($workDir + $selection[0]);
}

//----------------------------------------------------------------------------------------------
//
// find the weight files in the current project
//
//----------------------------------------------------------------------------------------------

global proc string icTransferSkinClusterFindWeights()
{
	string $weightPath = "data/skinWeights";
	string $dirContent[];
	string $workDir;
	int $exists;
	int $count = 0;

	string $workDir = `workspace -q -rd`;
	if (`filetest -d ($workDir + $weightPath)`)
		$workDir += $weightPath + "/";
	else
		$workDir += "data/";
	$dirContent = `getFileList -fld $workDir`;
	for ($item in $dirContent)
		if (`gmatch $item "*.scw"`)
			textScrollList -e -a $item weightTSL;

	return $workDir;
}

//----------------------------------------------------------------------------------------------
//
// creating the window
//
//----------------------------------------------------------------------------------------------

global proc icTransferSkinClusterImport( int $order )
{
	string $win = "icTransferSkinClusterUI";
	if (`window -exists $win`)
		deleteUI $win;
	icTransferSkinClusterWindow($win);
	string $workDir = `icTransferSkinClusterFindWeights`;
	icTransferSkinClusterButtonCallback( $workDir, $order );
	showWindow $win;
}

//----------------------------------------------------------------------------------------------
//
// find the skinCluster node
//
//----------------------------------------------------------------------------------------------

global proc string[] icTransferSkinClusterFindSkinCluster()
{
	string $return[];
	string $sel[] = `ls -sl -tr`;
	if (!size($sel))
		error ("Select a geometry to export weights.");
	for ($s in $sel)
	{
		string $his[] = `listHistory -f 0 -bf $s`;
		for ($h in $his)
		{
			if (`nodeType $h` == "skinCluster")
				$return[size($return)] = $h;
		}
	}
	return $return;
}

//----------------------------------------------------------------------------------------------
//
// main procedure
//
//----------------------------------------------------------------------------------------------

global proc icTransferSkinCluster( int $mode, int $order )
{
	if ($mode == 0)
	{
		string $workDir = `icTransferSkinClusterCheckDir`;
		string $sc[] = `icTransferSkinClusterFindSkinCluster`;
		for ($s in $sc)
		{
			select -r $s;
			transferSkinCluster -m 0 -f ($workDir + $s + ".scw");
		}
	}
	else
		icTransferSkinClusterImport $order;
}

'''
mel.eval(melProcs)
