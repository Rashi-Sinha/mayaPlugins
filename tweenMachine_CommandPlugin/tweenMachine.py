"""
Author: Rashi Sinha
Date Created: 28 July 2024
Versio: 1.0

Plug-In Type: Command Plug-In

Description: This plugin creates a Maya command to create a new key at the current time.
It uses the values of the previous and next keys, and adjusts them using the "weight" 
input value to set the value of the new key.

It lets a user set a new key between two existing keys to adjust the animation to be
closer to either of the surrounding key poses at the current time. 

New Key Value is calculated as follows:
newVal = (Prev_Key_Val * (1 - weight)) + (Next_Key_Val * weight)


Inputs (Flags): Help (-h) flag, Weight (-w) flag (value between 0 to 100)

Run Command:
1. Use Maya.cmds directly to run this command
    maya.cmds.tweenMachine(weight=20.0)
2. Use the interactive UI (tweenMachine.py) (Recommended)
"""

import maya.OpenMaya as om
import maya.OpenMayaMPx as omMPx
import maya.OpenMayaAnim as omA
import sys


commandName = "tweenMachine"

# define variables for command flags
kHelpFlag = "-h" # help flag
kHelpLongFlag = "-help" 

kWeightFlag = "-w"
kWeightLongFlag = "-weight"

helpMessage = "This command is used to add a key at the current time frame between 2 existing keys, with weigth input defining the value of the key"

class tweenMachinePlugin(omMPx.MPxCommand):
    # define member variables for flag arguments
    weight = None
    mAnimCurveChangeCache = omA.MAnimCurveChange()

    def __init__(self):
        omMPx.MPxCommand.__init__(self)
        
    def argumentParser(self, argList):
        
        # get syntax object, stored in base class' syntax variable after registeration of the command
        syntax = self.syntax()
        
        # parse arguments
        parsedArguments = om.MArgDatabase(syntax, argList)
        
        # check if a flag is set
        if parsedArguments.isFlagSet(kWeightFlag):
            # get value of that flag, here in double. 0 is the index
            self.weight = parsedArguments.flagArgumentDouble(kWeightFlag,0)
        if parsedArguments.isFlagSet(kWeightLongFlag):
            self.weight = parsedArguments.flagArgumentDouble(kWeightLongFlag,0)
        
        if parsedArguments.isFlagSet(kHelpFlag):
            # setResult is a method of the base class MPxCommand
            self.setResult(helpMessage)
        if parsedArguments.isFlagSet(kHelpLongFlag):
            self.setResult(helpMessage)


    def getAnimCurves(self, mSel, mItSelectionList, mObjArray_Anim):

        """
        Method to extract the animation curves from the currently selected objects in the Maya Scene

        Parameters:
        mSel (MSelectionList) : Active Selection List
        mItSelectionList (MItSelectionList) : Iterator for selection List filtered on animation curves
        mObjArray_Anim (MObjArray) : Array to store MObjects of animation curves (implicit return)

        """

        # loop through the selection list of animation curves and add them to mObjArray_Anim list
        while not mItSelectionList.isDone():
            mObj = om.MObject()
            mItSelectionList.getDependNode(mObj)
            mObjArray_Anim.append(mObj)

            mItSelectionList.next()


        # if no curves are selected, check if a DAG Node is selected.
        if mObjArray_Anim.length() <= 0:
            mItSelectionList = om.MItSelectionList(mSel, om.MFn.kDagNode)
        
            # loop through the selected DAG Nodes
            while not mItSelectionList.isDone():
                mObj = om.MObject()
                mItSelectionList.getDependNode(mObj)
                
                # if the selected object is animated
                if omA.MAnimUtil.isAnimated(mObj, False): 
                    
                    # get all plugs
                    mPlugArray_animated = om.MPlugArray()
                    omA.MAnimUtil.findAnimatedPlugs(mObj, mPlugArray_animated, False)
                
                    for i in range(mPlugArray_animated.length()):
                        # Loop through each plug of the selected item and get all of it's connections
                        mPlugArray2 = om.MPlugArray()
                        mPlugArray_animated[i].connectedTo(mPlugArray2, True, True)
                        
                        # loop through each connection for the current plug
                        for j in range(mPlugArray2.length()):  
                            # if the connection's node is an animation curve, add it to the mObjArray_Anim list
                            if "kAnimCurve" in mPlugArray2[j].node().apiTypeStr():
                                mObjArray_Anim.append(mPlugArray2[j].node())
                
                mItSelectionList.next()


    def addKeyToAnimCurves(self, mObjArray_Anim, currTime):
        """
        Method to loop through all animation curves and add keys on the current time frame according to weight input.

        Parameters:
        mObjArray_Anim (MObjArray) : array of animation curves MObjects extracted from the selected objects in the Maya scene
        (results from self.getAnimationCurves() method)
        curreTime (MTime) : Current Time on the Time slider in Maya
        """
        mFnAnimCurve = omA.MFnAnimCurve()

        for i in range(mObjArray_Anim.length()):

            mFnAnimCurve.setObject(mObjArray_Anim[i])
            numKeys = mFnAnimCurve.numKeys()

            # if curve is Time Input, we can set a new keyframe
            if mFnAnimCurve.isTimeInput():
                
                # find the index of the key closest to the current time
                closest_ind = mFnAnimCurve.findClosest(currTime)
                # find the time that the closest key is set at
                closest_Time = mFnAnimCurve.time(closest_ind)
                
                # if no key exists at current time, add a new key
                if closest_Time != currTime:
                    # set previous and next key indices
                    if closest_Time < currTime and closest_ind < numKeys-1:
                        prev_Key_Ind = closest_ind
                        next_Key_Ind = closest_ind + 1
                    elif closest_Time > currTime and closest_ind > 0:
                        prev_Key_Ind = closest_ind - 1
                        next_Key_Ind = closest_ind
                    else:
                        # if the selected time frame does not lie between two existing keyframes, throw error and break
                        om.MGlobal.displayError("Previous or Next keyframe does not exist for this time for at least one of the animation curves.")
                        break
                
                    # set in and out tangent types for new key based on prev and next keys   
                    new_Key_inTangent = mFnAnimCurve.outTangentType(prev_Key_Ind) # prev key's out-tangent is new key's in-tangent        
                    new_Key_outTangent = mFnAnimCurve.inTangentType(next_Key_Ind) # next key's in-tangent is new key's out-tangent

                    # if new in and out tangents are "fixed" type, set then as them global in and out tangent types
                    if new_Key_inTangent == omA.MFnAnimCurve.kTangentFixed or new_Key_outTangent == omA.MFnAnimCurve.kTangentFixed:
                        new_Key_inTangent = omA.MAnimControl.globalInTangentType()
                        new_Key_outTangent = omA.MAnimControl.globalOutTangentType()
                    
                    # evaluate value of the new key based on the weight input (provided from the UI slider)
                    new_Key_Value = (mFnAnimCurve.value(prev_Key_Ind) * (1-self.weight)) + (mFnAnimCurve.value(next_Key_Ind) * self.weight)

                    # add a new key and store operation in anim curve change cache to allow undo
                    mFnAnimCurve.addKey(currTime, new_Key_Value, new_Key_inTangent, new_Key_outTangent, self.mAnimCurveChangeCache)

                # if key exists at current time, update it's value (required when UI slider is pressed and value is changes till it's released)
                else:
                    # closest_ind is the index of the key at current time
                    new_Key_Value = (mFnAnimCurve.value(closest_ind-1) * (1-self.weight)) + (mFnAnimCurve.value(closest_ind+1) * self.weight)
                    mFnAnimCurve.setValue(closest_ind,new_Key_Value)
                

    def redoIt(self):

        # get the current time on the Time Slider
        currTime = omA.MAnimControl.currentTime()
        # remap weight value to be between 0 and 1
        self.weight/=100.0

        # get the active selection list
        mSel = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(mSel)

        if not mSel.isEmpty():
            mItSelectionList = om.MItSelectionList(mSel, om.MFn.kAnimCurve)
            mObjArray_Anim = om.MObjectArray()

            # get the animation curves from the currently selected objects.
            self.getAnimCurves(mSel, mItSelectionList, mObjArray_Anim)
            if mObjArray_Anim.length() > 0:
                # add keyframe to those animation curves
                self.addKeyToAnimCurves(mObjArray_Anim, currTime)
            else:
                # if nothing is animated, throw error
                om.MGlobal.displayError("No animated object selected")
        
        else:
            # if nothing is selected, throw error
            om.MGlobal.displayError("No DAG Object or Anim Curve Slected")


    def isUndoable(self):
        return True
    

    def undoIt(self):

        # undo all curve change operations from the anim curve change cache
        self.mAnimCurveChangeCache.undoIt()

   
    def doIt(self, argList):
        # parse the argument list
        self.argumentParser(argList)
    
        # if weight variable has value, call redoIt
        if self.weight != None and self.weight <= 100.0 and self.weight >= 0.0:
            self.redoIt()
        else:
            # if nothing is selected, throw error
            om.MGlobal.displayError("Weight value is required. Should be Between 0.0 - 100.0")


def commandCreator():
    return omMPx.asMPxPtr(tweenMachinePlugin())


def syntaxCreator():
    
    # create MSyntax object
    syntax = om.MSyntax()
    
    # collect/add all flags
    syntax.addFlag(kHelpFlag, kHelpLongFlag) # does not accept any flag argument
    syntax.addFlag(kWeightFlag, kWeightLongFlag, om.MSyntax.kDouble)
    
    # return MSyntax
    return syntax   

# funtion for initialization of the plugin
def initializePlugin(monject):
    
    mplugin = omMPx.MFnPlugin(monject, "Rashi Sinha", "1.0")
    try:   
        mplugin.registerCommand(commandName, commandCreator, syntaxCreator)
    except:
        # show error if plugin couldn't be registered  
        sys.stderr.write("Failed to register command: ", commandName)
        
# funtion for Un-initialization of the plugin
def uninitializePlugin(monject):

    mplugin = omMPx.MFnPlugin(monject)
    try:
        mplugin.deregisterCommand(commandName)
    except:
        # show error if plugin couldn't be registered
        sys.stderr.write("Failed to de-register command: ", commandName)
    