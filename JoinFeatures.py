#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Victor Titov (DeepSOIC)                          *
#*                                               <vv.titov@gmail.com>      *  
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import FreeCAD, Part

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

__title__="JoinFeatures module"
__author__ = "DeepSOIC"
__url__ = "http://www.freecadweb.org"

# -------------------------- common stuff --------------------------------------------------
def shapeOfMaxVol(compound):
    if compound.ShapeType == 'Compound':
        maxVol = 0
        cntEq = 0
        shMax = None
        for sh in compound.childShapes():
            v = sh.Volume
            if v > maxVol + 1e-8 :
                maxVol = v
                shMax = sh
                cntEq = 1
            elif abs(v - maxVol) <= 1e-8 :
                cntEq = cntEq + 1
        if cntEq > 1 :
            raise ValueError("Equal volumes, can't figure out what to cut off!")
        return shMax
    else:
        return compound


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- ConnectObjectsFeature --------------------------------------------------

def makeConnectObjectsFeature(name):
    '''makeConnectObjectsFeature(name): makes an ConnectObjectsFeature object'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _ConnectObjectsFeature(obj)
    _ViewProviderConnectObjectsFeature(obj.ViewObject)
    #FreeCAD.ActiveDocument.recompute()
    return obj

class _CommandConnectObjectsFeature:
    "the Fem InvoluteGear command definition"
    def GetResources(self):
        return {'Pixmap'  : 'PartDesign_InternalExternalGear',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Part_ConnectObjectsFeature","Connect objects..."),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Part_ConnectObjectsFeature","Fuses objects, taking care to preserve voids.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            FreeCAD.ActiveDocument.openTransaction("Create ConnectObjectsFeature")
            FreeCADGui.addModule("JoinFeatures")
            FreeCADGui.doCommand("j = JoinFeatures.makeConnectObjectsFeature('Connect')")
            FreeCADGui.doCommand("j.Feature1 = FreeCADGui.Selection.getSelection()[0]")
            FreeCADGui.doCommand("j.Feature2 = FreeCADGui.Selection.getSelection()[1]")
            FreeCADGui.doCommand("j.Proxy.execute(j)")
            FreeCADGui.doCommand("j.purgeTouched()")
            FreeCADGui.doCommand("j.Feature1.ViewObject.hide()")
            FreeCADGui.doCommand("j.Feature2.ViewObject.hide()")
            FreeCAD.ActiveDocument.commitTransaction()
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(QtCore.QTranslator().tr("Two solids need to be selected, first!"))
            mb.setWindowTitle(QtCore.QTranslator().tr("Bad selection"))
            mb.exec_()
            
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False


class _ConnectObjectsFeature:
    "The ConnectObjectsFeature object"
    def __init__(self,obj):
        self.Type = "ConnectObjectsFeature"
        obj.addProperty("App::PropertyLink","Feature1","Join","First object of two objects to be joined")
        obj.addProperty("App::PropertyLink","Feature2","Join","Second object of two objects to be joined")
        obj.addProperty("App::PropertyBool","Refine","Join","True = refine resulting shape. False = output as is.")
        
        obj.Proxy = self
        

    def execute(self,obj):
        cut1 = obj.Feature1.Shape.cut(obj.Feature2.Shape)
        cut1 = shapeOfMaxVol(cut1)
        cut2 = obj.Feature2.Shape.cut(obj.Feature1.Shape)
        cut2 = shapeOfMaxVol(cut2)
        rst =  cut1.multiFuse([cut2, obj.Feature2.Shape.common(obj.Feature1.Shape)])
        if obj.Refine:
            rst = rst.removeSplitter()
        obj.Shape = rst
        return
        
        
class _ViewProviderConnectObjectsFeature:
    "A View Provider for the ConnectObjectsFeature object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return ":/icons/PartDesign_InternalExternalGear.svg"

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

FreeCADGui.addCommand('Part_ConnectObjectsFeature',_CommandConnectObjectsFeature())

# -------------------------- /ConnectObjectsFeature --------------------------------------------------


# -------------------------- EmbedFeature --------------------------------------------------

def makeEmbedFeature(name):
    '''makeEmbedFeature(name): makes an EmbedFeature object'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _EmbedFeature(obj)
    _ViewProviderEmbedFeature(obj.ViewObject)
    #FreeCAD.ActiveDocument.recompute()
    return obj

class _CommandEmbedFeature:
    "the Part EmbedFeature command definition"
    def GetResources(self):
        return {'Pixmap'  : 'PartDesign_InternalExternalGear',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Part_EmbedFeature","Embed object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Part_EmbedFeature","Fuses one object into another, taking care to preserve voids.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            FreeCAD.ActiveDocument.openTransaction("Create EmbedFeature")
            FreeCADGui.addModule("JoinFeatures")
            FreeCADGui.doCommand("j = JoinFeatures.makeEmbedFeature('Embed')")
            FreeCADGui.doCommand("j.Base = FreeCADGui.Selection.getSelection()[0]")
            FreeCADGui.doCommand("j.Tool = FreeCADGui.Selection.getSelection()[1]")
            FreeCADGui.doCommand("j.Proxy.execute(j)")
            FreeCADGui.doCommand("j.purgeTouched()")
            FreeCADGui.doCommand("j.Base.ViewObject.hide()")
            FreeCADGui.doCommand("j.Tool.ViewObject.hide()")
            FreeCAD.ActiveDocument.commitTransaction()
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(QtCore.QTranslator().tr("Select base object, then the object to embed, and invoke this tool."))
            mb.setWindowTitle(QtCore.QTranslator().tr("Bad selection"))
            mb.exec_()

        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False


class _EmbedFeature:
    "The EmbedFeature object"
    def __init__(self,obj):
        self.Type = "EmbedFeature"
        obj.addProperty("App::PropertyLink","Base","Join","Base object, the one to embed the other object into.")
        obj.addProperty("App::PropertyLink","Tool","Join","The object to be embedded")
        obj.addProperty("App::PropertyBool","Refine","Join","True = refine resulting shape. False = output as is.")
        
        obj.Proxy = self
        

    def execute(self,obj):
        cut1 = obj.Base.Shape.cut(obj.Tool.Shape)
        cut1 = shapeOfMaxVol(cut1)
        rst = cut1.fuse(obj.Tool.Shape)
        if obj.Refine:
            rst = rst.removeSplitter()
        obj.Shape = rst

        return
        
        
class _ViewProviderEmbedFeature:
    "A View Provider for the EmbedFeature object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return ":/icons/PartDesign_InternalExternalGear.svg"

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

FreeCADGui.addCommand('Part_EmbedFeature',_CommandEmbedFeature())

# -------------------------- /EmbedFeature --------------------------------------------------



# -------------------------- CutoutFeature --------------------------------------------------

def makeCutoutFeature(name):
    '''makeCutoutFeature(name): makes an CutoutFeature object'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _CutoutFeature(obj)
    _ViewProviderCutoutFeature(obj.ViewObject)
    #FreeCAD.ActiveDocument.recompute()
    return obj

class _CommandCutoutFeature:
    "the Part CutoutFeature command definition"
    def GetResources(self):
        return {'Pixmap'  : 'PartDesign_InternalExternalGear',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Part_CutoutFeature","Cutout for object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Part_CutoutFeature","Makes a cutout in one object to fit another object.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            FreeCAD.ActiveDocument.openTransaction("Create CutoutFeature")
            FreeCADGui.addModule("JoinFeatures")
            FreeCADGui.doCommand("j = JoinFeatures.makeCutoutFeature('Cutout')")
            FreeCADGui.doCommand("j.Base = FreeCADGui.Selection.getSelection()[0]")
            FreeCADGui.doCommand("j.Tool = FreeCADGui.Selection.getSelection()[1]")
            FreeCADGui.doCommand("j.Proxy.execute(j)")
            FreeCADGui.doCommand("j.purgeTouched()")
            FreeCADGui.doCommand("j.Base.ViewObject.hide()")
            FreeCADGui.doCommand("j.Tool.ViewObject.hide()")
            FreeCAD.ActiveDocument.commitTransaction()
        else:
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Warning)
            mb.setText(QtCore.QTranslator().tr("Select the object to make a cutout in, then the object that should fit into the cutout, and invoke this tool."))
            mb.setWindowTitle(QtCore.QTranslator().tr("Bad selection"))
            mb.exec_()

        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False


class _CutoutFeature:
    "The CutoutFeature object"
    def __init__(self,obj):
        self.Type = "CutoutFeature"
        obj.addProperty("App::PropertyLink","Base","Join","Base object, the one to embed the other object into.")
        obj.addProperty("App::PropertyLink","Tool","Join","The object to be embedded")
        obj.addProperty("App::PropertyBool","Refine","Join","True = refine resulting shape. False = output as is.")
        
        obj.Proxy = self
        

    def execute(self,obj):
        cut1 = obj.Base.Shape.cut(obj.Tool.Shape)
        cut1 = shapeOfMaxVol(cut1)
        if obj.Refine:
            cut1 = cut1.removeSplitter()
        obj.Shape = cut1
        return
        
        
class _ViewProviderCutoutFeature:
    "A View Provider for the CutoutFeature object"

    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return ":/icons/PartDesign_InternalExternalGear.svg"

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

FreeCADGui.addCommand('Part_CutoutFeature',_CommandCutoutFeature())

# -------------------------- /CutoutFeature --------------------------------------------------
