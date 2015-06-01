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
def getParamRefine():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part/Boolean").GetBool("RefineModel")

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

def makePartJoinFeature(name, mode = 'bypass'):
    '''makePartJoinFeature(name, mode = 'bypass'): makes an PartJoinFeature object.'''
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _PartJoinFeature(obj)
    obj.Mode = mode
    obj.Refine = getParamRefine()
    _ViewProviderPartJoinFeature(obj.ViewObject)
    return obj

class _PartJoinFeature:
    "The PartJoinFeature object"
    def __init__(self,obj):
        self.Type = "PartJoinFeature"
        obj.addProperty("App::PropertyEnumeration","Mode","Join","The mode of operation. bypass = make compound (fast)")
        obj.Mode = ['bypass','Connect','Embed','Cutout']
        obj.addProperty("App::PropertyLink","Base","Join","First object")
        obj.addProperty("App::PropertyLink","Tool","Join","Second object")
        obj.addProperty("App::PropertyBool","Refine","Join","True = refine resulting shape. False = output as is.")
        
        obj.Proxy = self
        

    def execute(self,obj):
        rst = None
        if obj.Mode == 'bypass':
            rst = Part.makeCompound([obj.Base.Shape, obj.Tool.Shape])
        else:
            cut1 = obj.Base.Shape.cut(obj.Tool.Shape)
            cut1 = shapeOfMaxVol(cut1)
            if obj.Mode == 'Connect':
                cut2 = obj.Tool.Shape.cut(obj.Base.Shape)
                cut2 = shapeOfMaxVol(cut2)
                rst = cut1.multiFuse([cut2, obj.Tool.Shape.common(obj.Base.Shape)])
            elif obj.Mode == 'Embed':
                rst = cut1.fuse(obj.Tool.Shape)
            elif obj.Mode == 'Cutout':
                rst = cut1
            if obj.Refine:
                rst = rst.removeSplitter()
        obj.Shape = rst
        return
        
        
class _ViewProviderPartJoinFeature:
    "A View Provider for the PartJoinFeature object"

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

def CreateJoinFeature(name, mode):
    FreeCAD.ActiveDocument.openTransaction("Create "+mode+"ObjectsFeature")
    FreeCADGui.addModule("JoinFeatures")
    FreeCADGui.doCommand("j = JoinFeatures.makePartJoinFeature(name = '"+name+"', mode = '"+mode+"' )")
    FreeCADGui.doCommand("j.Base = FreeCADGui.Selection.getSelection()[0]")
    FreeCADGui.doCommand("j.Tool = FreeCADGui.Selection.getSelection()[1]")
    FreeCADGui.doCommand("j.Proxy.execute(j)")
    FreeCADGui.doCommand("j.purgeTouched()")
    FreeCADGui.doCommand("j.Base.ViewObject.hide()")
    FreeCADGui.doCommand("j.Tool.ViewObject.hide()")
    FreeCAD.ActiveDocument.commitTransaction()

# -------------------------- /common stuff --------------------------------------------------

# -------------------------- ConnectObjectsFeature --------------------------------------------------

class _CommandConnectFeature:
    "Command to create PartJoinFeature in Connect mode"
    def GetResources(self):
        return {'Pixmap'  : 'PartDesign_InternalExternalGear',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Part_ConnectFeature","Connect objects..."),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Part_ConnectFeature","Fuses objects, taking care to preserve voids.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateJoinFeature(name = "Connect", mode = "Connect")
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
            
FreeCADGui.addCommand('Part_ConnectFeature',_CommandConnectFeature())

# -------------------------- /PartJoinFeature --------------------------------------------------


# -------------------------- EmbedFeature --------------------------------------------------

class _CommandEmbedFeature:
    "Command to create PartJoinFeature in Embed mode"
    def GetResources(self):
        return {'Pixmap'  : 'PartDesign_InternalExternalGear',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Part_EmbedFeature","Embed object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Part_EmbedFeature","Fuses one object into another, taking care to preserve voids.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateJoinFeature(name = "Embed", mode = "Embed")
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

FreeCADGui.addCommand('Part_EmbedFeature',_CommandEmbedFeature())

# -------------------------- /EmbedFeature --------------------------------------------------



# -------------------------- CutoutFeature --------------------------------------------------

class _CommandCutoutFeature:
    "Command to create PartJoinFeature in Cutout mode"
    def GetResources(self):
        return {'Pixmap'  : 'PartDesign_InternalExternalGear',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Part_CutoutFeature","Cutout for object"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Part_CutoutFeature","Makes a cutout in one object to fit another object.")}
        
    def Activated(self):
        if len(FreeCADGui.Selection.getSelection()) == 2 :
            CreateJoinFeature(name = "Cutout", mode = "Cutout")
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

FreeCADGui.addCommand('Part_CutoutFeature',_CommandCutoutFeature())

# -------------------------- /CutoutFeature --------------------------------------------------
