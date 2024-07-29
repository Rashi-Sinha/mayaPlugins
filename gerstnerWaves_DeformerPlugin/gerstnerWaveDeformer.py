"""
Author: Rashi Sinha
Date Created: 20 July 2024
Versio: 1.0

Plug-In Type: Deformer Node

Description: This plugin creates a Gerstner Wave deformation on
the selected meshes.

Gerstner Wave Algorithm Reference: https://catlikecoding.com/unity/tutorials/flow/waves/

This can be used to depict water surfaces.

Inputs: Movement Factor, Wave Direction, Steepness, 
and Wavelength for 3 Waves (A, B, C)

Ouput: Deformed Mesh Geometry
"""

import sys
import maya.OpenMaya as om
import maya.OpenMayaMPx as omMPx
import maya.OpenMayaAnim as omA
import math


nodeName = "GerstnerWaveDeformer"
nodeId = om.MTypeId(0x106fff)

class Ripple(omMPx.MPxDeformerNode):

    # deforme Node custon Input Attributes
    mObj_inMovement = om.MObject()

    mObj_inWaveA_DirSteep = om.MObject()
    mObj_inWaveA_Wavelength = om.MObject()

    mObj_inWaveB_DirSteep = om.MObject()
    mObj_inWaveB_Wavelength = om.MObject()

    mObj_inWaveC_DirSteep = om.MObject()
    mObj_inWaveC_Wavelength = om.MObject()


    def __init__(self):
        omMPx.MPxDeformerNode.__init__(self)

    def gerstnerWave(self, wave, wavelength, position, movementVal):

        '''
        Method to caculate the current point's position displacement 
        for one gerstner wave 

        Parameters:
        Wave (float3): Wave Direction X, Wave Direction Y, Steepness (Deformer Node custom Input Attribute)
        Wavelength (float): Wavelength of the wave (Deformer Node custom Input Attribute)
        poisition (MPoint): Current vertex's position (inputGeom information)
        movementVal (float): movement factor to move the waves (Deformer Node custom Input Attribute)

        '''
        
        steepness = wave[2]
        k = float(2 * math.pi / wavelength)
        c = float(math.sqrt(9.8 / k))
        floatVectorDirection = om.MFloatVector(wave[0], wave[1])
        d = floatVectorDirection.normal()
        dotDirectionPositon = (d.x * position.x) + (d.y * position.z)
        f = k * (dotDirectionPositon - c * movementVal)
        a = steepness / k

        # tangent and binormal formula for calculating the updated normal of a point
        # Not needed as Maya updates the normals, and this is a deformer node, and not a shader.
        # tangent += float3(
        #     -d.x * d.x * (steepness * sin(f)),
        #     d.x * (steepness * cos(f)),
        #     -d.x * d.y * (steepness * sin(f))
        # )
        # binormal += float3(
        #     -d.x * d.y * (steepness * sin(f)),
        #     d.y * (steepness * cos(f)),
        #     -d.y * d.y * (steepness * sin(f))
        # )
        
        pointPosition = om.MPoint((d.x * (a * math.cos(f))),(a * math.sin(f)),(d.y * (a * math.cos(f))))
        return pointPosition
    

    def addToPosition(self, pointPosition, pointToAdd, evaluateVal):

        """
        Helper method to add the result from the gerstner wave to the current point position

        Parameters:
        pointPosition (MPoint): Current vertex's position (inputGeom information)
        pointToAdd (MPoint): Result of gerstnerWave() method
        evaluateVal (float): Deformer node blend/affect value
        """

        pointPosition.x = pointPosition.x + pointToAdd.x * evaluateVal
        pointPosition.y = pointPosition.y + pointToAdd.y * evaluateVal
        pointPosition.z = pointPosition.z + pointToAdd.z * evaluateVal


    def deform(self, dataBlock, geoIterator, matrix, geometryIndex):
        
        # input array
        inputArr = omMPx.cvar.MPxGeometryFilter_input
        # attach a data handle to input array attribute
        dataHandleInputArray = dataBlock.outputArrayValue(inputArr)
        # jump to geometryIndex
        dataHandleInputArray.jumpToElement(geometryIndex)
        # attach a data handle to the specific data block
        dataHandleInputElement = dataHandleInputArray.inputValue()
        # reach to child - input geom
        # first get inputGeom attribute from default deformer node.
        inputGeom = omMPx.cvar.MPxGeometryFilter_inputGeom
        # get child using data handle. Which child? inputGeom child.
        dataHandleInputGeom = dataHandleInputElement.child(inputGeom)
        # get the mesh using this new handle
        inMesh = dataHandleInputGeom.asMesh()


        # envelope - read float value
        envelope = omMPx.cvar.MPxGeometryFilter_envelope
        dataHandleEnvelope = dataBlock.inputValue(envelope)
        envelopeVal = dataHandleEnvelope.asFloat()

        # attach handles and read input values of custom attributes

        # Movement Factor
        dataHandle_Movement = dataBlock.inputValue(Ripple.mObj_inMovement)
        movementVal = dataHandle_Movement.asFloat()

        # Wave 
        dataHandleWaveA_DirStp = dataBlock.inputValue(Ripple.mObj_inWaveA_DirSteep)
        waveA_DirStpVal = dataHandleWaveA_DirStp.asFloat3()
        dataHandleWaveA_Wavelength = dataBlock.inputValue(Ripple.mObj_inWaveA_Wavelength)
        waveA_WavelengthVal = dataHandleWaveA_Wavelength.asFloat()

        # Wave B
        dataHandleWaveB_DirStp = dataBlock.inputValue(Ripple.mObj_inWaveB_DirSteep)
        waveB_DirStpVal = dataHandleWaveB_DirStp.asFloat3()
        dataHandleWaveB_Wavelength = dataBlock.inputValue(Ripple.mObj_inWaveB_Wavelength)
        waveB_WavelengthVal = dataHandleWaveB_Wavelength.asFloat()

        # Wave C
        dataHandleWaveC_DirStp = dataBlock.inputValue(Ripple.mObj_inWaveC_DirSteep)
        waveC_DirStpVal = dataHandleWaveC_DirStp.asFloat3()
        dataHandleWaveC_Wavelength = dataBlock.inputValue(Ripple.mObj_inWaveC_Wavelength)
        waveC_WavelengthVal = dataHandleWaveC_Wavelength.asFloat()

        # create mPointArray to append all pointPositions and use to set all point positions at once.
        mPointArray_meshVert = om.MPointArray()
        # use geoIterators to iterate over mesh data

        while not geoIterator.isDone():

            pointPosition = geoIterator.position()

            # add gerstnerWave result to pointPosition for each of the 3 waves.
            self.addToPosition(pointPosition, self.gerstnerWave(waveA_DirStpVal, waveA_WavelengthVal, pointPosition, movementVal), envelopeVal)
            self.addToPosition(pointPosition, self.gerstnerWave(waveB_DirStpVal, waveB_WavelengthVal, pointPosition, movementVal), envelopeVal)
            self.addToPosition(pointPosition, self.gerstnerWave(waveC_DirStpVal, waveC_WavelengthVal, pointPosition, movementVal), envelopeVal)
            
            # append new poisiton to MPointArray
            mPointArray_meshVert.append(pointPosition)
            geoIterator.next()

        # optimize by setting all point positions at once.
        geoIterator.setAllPositions(mPointArray_meshVert)
    
def deformerCreator():
    return omMPx.asMPxPtr(Ripple())

def nodeInitializer():

    '''
    Create Attributes
    Attach Attributes to Node
    Design Circuitry
    '''

    mFnAttr = om.MFnNumericAttribute()

    # move factor
    Ripple.mObj_inMovement = mFnAttr.create("Movement","Move", om.MFnNumericData.kFloat,1.0)
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(1.0)
    mFnAttr.setMax(100.0)

    # Wave A
    # direction and Steepness, in float3
    Ripple.mObj_inWaveA_DirSteep = mFnAttr.create("WaveA(DirX,DirY,Steepness)","ADirStp", om.MFnNumericData.k3Float)
    # set properties. Attributes are by default readable, writable and storable.
    mFnAttr.setKeyable(1)
    # mFnAttr.default = (1.0,0.0,0.5)
    mFnAttr.setMin(0.0,0.0,0.0)
    mFnAttr.setMax(10.0,10.0,10.0)


    Ripple.mObj_inWaveA_Wavelength = mFnAttr.create("AWavelength","AWav", om.MFnNumericData.kFloat,1.0)
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(1.0)
    mFnAttr.setMax(100.0)

    # Wave B
    # direction and Steepness, in float3
    Ripple.mObj_inWaveB_DirSteep = mFnAttr.create("WaveB","BDirStp", om.MFnNumericData.k3Float)
    mFnAttr.setKeyable(1)
    # mFnAttr.default = (0.0,1.0,0.25)
    mFnAttr.setMin(0.0,0.0,0.0)
    mFnAttr.setMax(10.0,10.0,10.0)

    Ripple.mObj_inWaveB_Wavelength = mFnAttr.create("BWavelength","BWav", om.MFnNumericData.kFloat,1.0)
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(1.0)
    mFnAttr.setMax(100.0)

    # Wave C
    # direction and Steepness, in float3
    Ripple.mObj_inWaveC_DirSteep = mFnAttr.create("WaveC","CDirStp", om.MFnNumericData.k3Float)
    mFnAttr.setKeyable(1)
    # mFnAttr.default = (1.0,1.0,0.15)
    mFnAttr.setMin(0.0,0.0,0.0)
    mFnAttr.setMax(10.0,10.0,10.0)

    Ripple.mObj_inWaveC_Wavelength = mFnAttr.create("CWavelength","CWav", om.MFnNumericData.kFloat,1.0)
    # set properties. Attributes are by default readable, writable and storable.
    mFnAttr.setKeyable(1)
    mFnAttr.setMin(1.0)
    mFnAttr.setMax(100.0)

    # attach attributes
    Ripple.addAttribute(Ripple.mObj_inMovement)
    Ripple.addAttribute(Ripple.mObj_inWaveA_DirSteep)
    Ripple.addAttribute(Ripple.mObj_inWaveA_Wavelength)
    Ripple.addAttribute(Ripple.mObj_inWaveB_DirSteep)
    Ripple.addAttribute(Ripple.mObj_inWaveB_Wavelength)
    Ripple.addAttribute(Ripple.mObj_inWaveC_DirSteep)
    Ripple.addAttribute(Ripple.mObj_inWaveC_Wavelength)

    '''
    SWIG - Simplified Wrapper Interface Generator (to access outputGeom for circuitry)
    '''
    outputGeom = omMPx.cvar.MPxGeometryFilter_outputGeom
    Ripple.attributeAffects(Ripple.mObj_inMovement, outputGeom)
    Ripple.attributeAffects(Ripple.mObj_inWaveA_DirSteep, outputGeom)
    Ripple.attributeAffects(Ripple.mObj_inWaveA_Wavelength, outputGeom)
    Ripple.attributeAffects(Ripple.mObj_inWaveB_DirSteep, outputGeom)
    Ripple.attributeAffects(Ripple.mObj_inWaveB_Wavelength, outputGeom)
    Ripple.attributeAffects(Ripple.mObj_inWaveC_DirSteep, outputGeom)
    Ripple.attributeAffects(Ripple.mObj_inWaveC_Wavelength, outputGeom)


# funtion for initialization of the plugin
def initializePlugin(mobject):
    
    mplugin = omMPx.MFnPlugin(mobject, "Rashi Sinha", "1.0")
    
    try:
        # try to register command.
        mplugin.registerNode(nodeName, nodeId, deformerCreator, nodeInitializer, omMPx.MPxNode.kDeformerNode)
    except:
        # show error if plugin couldn't be registered
        sys.stderr.write("Failed to register command: "+ nodeName)
        
# funtion for Un-initialization of the plugin
def uninitializePlugin(mobject):

    mplugin = omMPx.MFnPlugin(mobject)
    
    try:
        # try to de-register command. Function only takes the command name
        mplugin.deregisterNode(nodeId)
    except:
        # show error if plugin couldn't be registered
        sys.stderr.write("Failed to de-register command: "+ nodeName)
    

