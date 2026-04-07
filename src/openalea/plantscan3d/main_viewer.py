import math
import os
import sys
from collections import deque

import openalea.mtg.algo as mtgalgo
from openalea.plantgl.gui.editablectrlpoint import *
from OpenGL.GL import *
from PyQt5.Qt import *

from . import ui_compiler as cui
from .backup import *
from .editor.algorithms.pole_selection import PoleSelectionAlgorithm
from .editor.algorithms.soil_selection import SoilSelectionAlgorithm
from .editor.algorithms.wire_selection import WireSelectionAlgorithm
from .editor.cursor_selector import CursorSelector
from .history import FileHistory
from .pglnqgl import *
from .progress_dialog import ProgressDialog
from .serial import *
from .settings import Settings
from .shareddata import *

ldir = os.path.dirname(__file__)
cui.check_ui_generation(os.path.join(ldir, "propwidget.ui"))


class Pos3Setter:
    def __init__(self, ctrlpointset, index):
        self.ctrlpointset = ctrlpointset
        self.index = index

    def __call__(self, pos):
        self.ctrlpointset[self.index] = toV3(pos)


def pglalgoExists(algoName):
    return algoName in dir(sys.modules[__name__])


def createMTGRepresentation(
    mtg,
    segment_inf_material,
    segment_plus_material,
    translation=None,
    positionproperty="position",
):
    scene = Scene()
    shindex = {}
    positions = mtg.property(positionproperty)
    r = set(mtg.component_roots_at_scale(mtg.root, scale=mtg.max_scale()))

    def choose_mat(mtg, nid, segment_inf_material, segment_plus_material):
        if mtg.edge_type(nid) == "<":
            return segment_inf_material
        else:
            return segment_plus_material

    l = [
        createEdgeRepresentation(
            mtg.parent(nodeID),
            nodeID,
            positions,
            choose_mat(mtg, nodeID, segment_inf_material, segment_plus_material),
            translation,
        )
        for nodeID in mtg.vertices(scale=mtg.max_scale())
        if nodeID not in r
    ]
    scene = Scene(l)
    shindex = dict((sh.id, i) for i, sh in enumerate(l))
    # for nodeID in mtg.vertices(scale=2):
    # for son in mtg.children(nodeID):
    # shindex[son] = i
    # scene += createEdgeRepresentation(nodeID,son,positions,segment_material,translation)
    # i+=1

    return scene, shindex


def createEdgeRepresentation(begnode, endnode, positions, material, translation=None):
    if begnode is None or endnode is None:
        print("Pb with node ", begnode, endnode)
        return None
    res = Polyline([positions[begnode], positions[endnode]], width=3)
    # res = Group([res,Translated((positions[begnode]+positions[endnode])/2,Text(str(endnode)))])
    if translation:
        res = Translated(translation, res)
    return Shape(res, material, endnode)


def createRadiiRepresentation(
    mtg,
    material,
    translation=None,
    positionproperty="position",
    radiusproperty="radius",
):
    scene = Scene()
    shindex = {}
    positions = mtg.property(positionproperty)
    radii = mtg.property(radiusproperty)
    l = [
        createRadiusRepresentation(mtg, nodeID, positions, radii, material, translation)
        for nodeID in list(radii.keys())
    ]
    l = [x for x in l if x is not None]
    scene = Scene(l)
    shindex = dict((sh.id, i) for i, sh in enumerate(l))

    return scene, shindex


def createRadiusRepresentation(mtg, node, positions, radii, material, translation=None):
    radius = radii[node]
    if radius is not None and radius > 1e-5:
        res = Scaled(radius, Polyline2D.Circle(1, 16))
        if mtg.parent(node):
            d = direction(positions[node] - positions[mtg.parent(node)])
            i = direction(d.anOrthogonalVector())
            j = d ^ i
            res = Oriented(i, j, res)
        res = Translated(
            positions[node] + (translation if translation else Vector3(0, 0, 0)), res
        )
        return Shape(res, material, node)


def createCtrlPoints(mtg, color, positionproperty="position", callback=None):
    ctrlPoints = dict(
        (nodeID, createCtrlPoint(mtg, nodeID, color, positionproperty, callback))
        for nodeID in mtg.vertices(scale=mtg.max_scale())
    )
    return ctrlPoints


def createCtrlPoint(mtg, nodeID, color, positionproperty="position", callback=None):
    ccp = CtrlPoint(
        mtg.property(positionproperty)[nodeID],
        Pos3Setter(mtg.property(positionproperty), nodeID),
        color=color,
        id=nodeID,
    )
    if callback:
        ccp.setCallBack(callback)
    return ccp

    # shape and material to display the object


BlackTheme = {
    "Name": "Black",
    "BackGround": (0, 0, 0),
    "Points": (180, 180, 180),
    "ContractedPoints": (255, 0, 0),
    "CtrlPoints": (250, 250, 250),
    "NewCtrlPoints": (30, 250, 250),
    "SelectedCtrlPoints": (30, 250, 30),
    "EdgeInf": (255, 255, 255),
    "EdgePlus": (255, 0, 0),
    "Radius": (200, 200, 200),
    "Direction": (255, 255, 255),
    "3DModel": (128, 64, 0),
    "3DHull": (0, 200, 0),
    "LocalAttractors": (255, 255, 0),
    "Cone": (255, 255, 0),
    "TaggedCtrlPoint": (255, 0, 0),
    "UnTaggedCtrlPoint": (255, 255, 255),
    "UpscaleCtrlPoint": [
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
    ],
}

WhiteTheme = {
    "Name": "White",
    "BackGround": (255, 255, 255),
    "Points": (180, 180, 180),
    "ContractedPoints": (255, 0, 0),
    "CtrlPoints": (250, 30, 30),
    "NewCtrlPoints": (30, 250, 250),
    "SelectedCtrlPoints": (30, 250, 30),
    "EdgeInf": (0, 0, 0),
    "EdgePlus": (200, 200, 0),
    "Radius": (100, 100, 100),
    "Direction": (0, 0, 0),
    "3DModel": (128, 64, 0),
    "3DHull": (0, 200, 0),
    "LocalAttractors": (255, 255, 0),
    "Cone": (255, 255, 0),
    "TaggedCtrlPoint": (255, 0, 0),
    "UnTaggedCtrlPoint": (0, 0, 0),
    "UpscaleCtrlPoint": [
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
    ],
}

GreyTheme = {
    "Name": "Grey",
    "BackGround": (255, 255, 255),
    "Points": (180, 180, 180),
    "ContractedPoints": (255, 0, 0),
    "CtrlPoints": (250, 30, 30),
    "NewCtrlPoints": (30, 250, 250),
    "SelectedCtrlPoints": (30, 250, 30),
    "EdgeInf": (0, 0, 0),
    "EdgePlus": (0, 200, 0),
    "Radius": (100, 100, 100),
    "Direction": (0, 0, 0),
    "3DModel": (128, 64, 0),
    "3DHull": (0, 200, 0),
    "LocalAttractors": (255, 255, 0),
    "Cone": (255, 255, 0),
    "TaggedCtrlPoint": (255, 0, 0),
    "UnTaggedCtrlPoint": (0, 0, 0),
    "UpscaleCtrlPoint": [
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
    ],
}

ThemeDict = {"Black": BlackTheme, "White": WhiteTheme, "Grey": GreyTheme}


class PointInfo:
    def __init__(self):
        self.pointWidth = 2
        self.selectedPoint = Index([])
        self.connexPoints = []


class MainViewer(QGLViewer):
    Edit, Selection, TagScale, TagProperty, Rotate = 1, 2, 4, 8, 16
    # The Different selection modes
    HybridSelect, AddSelect = 1, 2

    # Qt Signals
    open_file = pyqtSignal()
    undoAvailable = pyqtSignal(bool)
    redoAvailable = pyqtSignal(bool)
    PointAttributeDisplay = pyqtSignal(bool)

    def __init__(self, parent, pointfile=None, mtgfile=None):
        QGLViewer.__init__(self, parent)
        self.setStateFileName(".plantscan3d.xml")

        self.setObjectName("PS3DMainWindow")

        self.mode = None
        self.selectMode = self.HybridSelect

        self.filehistory = FileHistory(None, self.openFile)

        settings = Settings()
        self.filehistory.retrieveSettings(settings)
        settings.beginGroup("Theme")
        themename = settings.value("Name", "Black")
        settings.endGroup()

        self.setTheme(ThemeDict[themename], False)

        self.pointDisplay = True
        self.pointAttributeDisplay = True
        self.mtgDisplay = True
        self.ctrlPointDisplay = True
        self.modelDisplay = True
        self.customObjDisplay = True
        self.radiusDisplay = True
        self.pointfilter = 0
        self.rectangleSelect = None

        # plantgl basic object
        self.discretizer = Discretizer()
        self.glrenderer = GLRenderer(self.discretizer)
        self.glrenderer.renderingMode = GLRenderer.Dynamic

        try:
            self.glrenderer.setGLFrame(self)
        except:
            print("No text on GL Display")

        self.modelRep = None

        self.points = None if pointfile is None else Scene(pointfile)[0].geometry
        self.pointinfo = PointInfo()

        self.selectBuffSize = 0

        self.mtgfile = mtgfile
        self.propertyposition = "position"
        self.propertyradius = "radius"
        self.nodelabel = "N"

        self.pointsRep = None
        self.shapePoints = None
        self.shapeSelection = None
        self.pointsAttributeRep = None
        self.customObjRep = None

        self.k = 16
        self.pointsKDTree = None

        self.mtg = None
        self.mtgrep = None
        self.mtgrepindex = None

        self.ctrlPoints = None
        self.ctrlPointPrimitive = None
        self.nodeWidth = 4
        self.ctrlPointsRep = None

        self.radiusRep = None
        self.radiusRepIndex = dict()

        if self.mtgfile:
            self.readMTG(mtgfile)

        self.focus = None
        self.selection = None
        self.selectionTrigger = None

        self.translation = None

        self.clippigPlaneEnabled = False
        self.frontVisibility = 0
        self.backVisibility = 1.0

        self.backup = Backup(self)
        self.backup.declare_backup(
            "mtg", [BackupObject("mtg", self)], lambda: self.__update_all_mtg__()
        )

        self.backup.declare_backup(
            "points",
            [
                BackupObject(
                    "points",
                    self,
                    getmethod=lambda o, n: {
                        "pointList": getattr(o, n).pointList,
                        "colorList": getattr(o, n).colorList,
                    },
                    setmethod=lambda o, n, no: setattr(
                        o, n, PointSet(no["pointList"], no["colorList"])
                    ),
                    copymethod=lambda o: {
                        "pointList": Point3Array(o.pointList),
                        "colorList": Color4Array(o.colorList),
                    },
                ),
                BackupObject("pointinfo", self),
            ],
            lambda: self.setPoints(self.points),
        )

        self.temporaryinfo2D = None
        self.temporaryinfo = None

        self.progressdialog = ProgressDialog(self)
        self.progressdialog.setMinimumDuration(0.75)
        self.progressdialog.setCancelButtonEnabled(False)

        pgl_register_progressstatus_func(self.showProgress)

        self.currenttagname = "ScaleTag"

        # if not os.path.exists(get_shared_data("mtg")):
        #            self.window().menuLoad.setEnabled(False)

        self.propertyeditor = None

        self.paramcache = dict()

        # Disable application exit when using Escape
        self.setShortcut(QGLViewer.EXIT_VIEWER, 0)

        self.setAcceptDrops(True)

        self.cursor = CursorSelector(self)

        # Algorithms
        self.poleSelection = PoleSelectionAlgorithm(self)
        self.soilSelection = SoilSelectionAlgorithm(self)
        self.wireSelection = WireSelectionAlgorithm(self)

        self.eventListeners = deque()

        self.bgimage = False
        self.textureId = None

        if not hasattr(self, "updateGL"):
            self.updateViewGL = self.update
        else:
            self.updateViewGL = self.updateGL

    def clearBackgroundImg(self):
        self.setBackgroundColor(QColor(*self.theme["BackGround"]))
        self.bgimage = False

    def loadBackgroundImg(self, imagefilename):
        # code taken from the backgroundImage.cpp file that is part of the QGLViewer library
        from math import log

        self.u_max = 1.0
        self.v_max = 1.0

        # load image
        img = QImage(imagefilename)

        if img.isNull():
            qWarning("Unable to load file, unsupported file format")
            return

        qWarning(
            "Loading "
            + imagefilename
            + " "
            + str(img.width())
            + "x"
            + str(img.height())
            + " pixels"
        )
        self.makeCurrent()
        glEnable(GL_TEXTURE_2D)

        self.imageWidth = float(img.width())
        self.imageHeight = float(img.height())
        qWarning(str(self.imageWidth) + " " + str(self.imageHeight))

        # 1E-3 needed. Just try with width=128 and see !
        newWidth = 1 << (int)(1 + log(self.imageWidth - 1 + 1e-3) / log(2.0))
        newHeight = 1 << (int)(1 + log(self.imageHeight - 1 + 1e-3) / log(2.0))

        self.u_max = self.imageWidth / float(newWidth)
        self.v_max = self.imageHeight / float(newHeight)

        if (self.imageWidth != newWidth) or (self.imageHeight != newHeight):
            qWarning(
                "Image size set to " + str(newWidth) + "x" + str(newHeight) + " pixels"
            )
            img = img.copy(0, 0, newWidth, newHeight)

        # glImg = QImage(QGLWidget.convertToGLFormat(img)) # flipped 32bit RGBA
        self.textureId = QOpenGLTexture(img)
        self.textureId.setMinificationFilter(QOpenGLTexture.Linear)
        self.textureId.setMagnificationFilter(QOpenGLTexture.Linear)
        self.textureId.create()
        assert self.textureId.isCreated()

        # Another way to bind img texture:
        # if self.textureId:
        #    self.deleteTexture(self.textureId)
        #    self.textureId = None
        # self.textureId = glGenTextures(1) # self.bindTexture(img,GL_TEXTURE_2D,GL_RGBA)
        # if self.textureId :
        #    glBindTexture(GL_TEXTURE_2D, self.textureId)
        # Bind the img texture...
        # glTexImage2D(GL_TEXTURE_2D, 0, 4, glImg.width(), glImg.height(), 0,
        #   GL_RGBA, GL_UNSIGNED_BYTE, glImg.bits().asstring(glImg.byteCount()))

        self.bgimage = True
        self.doneCurrent()

    def loadBackgroundImg(self, imagefilename):
        img = QImage(imagefilename)

        if img.isNull():
            qWarning("Unable to load file, unsupported file format")
            return

        qWarning(
            "Loading "
            + imagefilename
            + " "
            + str(img.width())
            + "x"
            + str(img.height())
            + " pixels"
        )
        self.imageWidth = float(img.width())
        self.imageHeight = float(img.height())

        centre_x = self.width() * 0.5 - self.imageWidth * 0.5
        centre_y = self.height() * 0.5 - self.imageHeight * 0.5

        points = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
        points = [
            (centre_x, centre_y),
            (centre_x, centre_y + self.imageHeight),
            (centre_x + self.imageWidth, centre_y + self.imageHeight),
            (centre_x + self.imageWidth, centre_y),
        ]
        points = [(x, y, 0.99) for x, y in points]
        uvs = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
        # uvs = [(0.0, 1.0-self.v_max),(0.0, 1.0),(self.u_max, 1.0),(self.u_max, 1.0-self.v_max)]
        self.bgscene = Scene(
            [
                Shape(
                    QuadSet(points, [list(range(4))], texCoordList=uvs),
                    Texture2D(ImageTexture(imagefilename)),
                )
            ]
        )
        self.bgscene.save("test.bgeom")
        self.bgimage = True

    def drawBackground(self):
        # code taken from the backgroundImage.cpp file that is part of the QGLViewer library
        print("drawBackground")
        # glBindTexture(GL_TEXTURE_2D, self.textureId)
        # set texturing for background image
        # glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        # Nice texture coordinate interpolation
        # glHint (GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        glDisable(GL_LIGHTING)
        glColor3f(0, 0, 0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # Draws the quad in (0,0) to (1.0,imageHeight/imageWidth)
        self.startScreenCoordinatesSystem(True)
        centre_x = self.width() * 0.5 - self.imageWidth * 0.5
        centre_y = self.height() * 0.5 - self.imageHeight * 0.5
        print(
            (centre_x, centre_y),
            (centre_x + self.imageWidth, centre_y + self.imageHeight),
        )

        depth = 0.99
        self.textureId.bind()
        points = [
            (centre_x, centre_y),
            (centre_x, centre_y + self.imageHeight),
            (centre_x + self.imageWidth, centre_y + self.imageHeight),
            (centre_x + self.imageWidth, centre_y),
        ]
        uvs = [
            (0.0, 1.0 - self.v_max),
            (0.0, 1.0),
            (self.u_max, 1.0),
            (self.u_max, 1.0 - self.v_max),
        ]
        print(points)
        print(uvs)
        glNormal3f(0.0, 0.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        for uv, pt in zip(uvs, points):
            glTexCoord2f(*uv)
            glVertex2f(*pt)
        glEnd()
        self.stopScreenCoordinatesSystem()

        # Depth clear is not absolutely needed. An other option would have been to draw the
        # QUAD with a 0.999 z value (z ranges in [0, 1[ with startScreenCoordinatesSystem()).
        glClear(GL_DEPTH_BUFFER_BIT)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)

    def drawBackground(self):
        # code taken from the backgroundImage.cpp file that is part of the QGLViewer library
        print("drawBackground")
        # glBindTexture(GL_TEXTURE_2D, self.textureId)
        # set texturing for background image
        # glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        # Nice texture coordinate interpolation
        # glHint (GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

        glDisable(GL_LIGHTING)
        glColor3f(0, 0, 0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.startScreenCoordinatesSystem(True)
        self.bgscene.apply(self.glrenderer)
        self.stopScreenCoordinatesSystem()

        # Depth clear is not absolutely needed. An other option would have been to draw the
        # QUAD with a 0.999 z value (z ranges in [0, 1[ with startScreenCoordinatesSystem()).
        glClear(GL_DEPTH_BUFFER_BIT)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)

    def showProgress(self, message, percent):
        self.progressdialog.setLabelText(
            message % percent if "%.2f%%" in message else message
        )
        self.progressdialog.setProgress(percent)

    def closeEvent(self, event):
        settings = Settings()
        self.filehistory.setSettings(settings)

        # Theme
        settings.beginGroup("Theme")
        settings.setValue("Name", self.theme["Name"])

        if self.theme["Name"] == "Custom":
            for name, val in list(self.theme.items()):
                if name != "Name":
                    settings.setValue(name, val)

        settings.endGroup()
        event.accept()

    def setNewPointset(self, pointSet):
        """
        Set a new point set.
        :param pointSet: The new point set.
        :return: None
        """
        self.pointinfo.selectedPoint = Index([])
        self.setPoints(pointSet)
        self.updateViewGL()

    def selectPoints(self, points):
        """
        Create a new selection.
        :param points: Points to select.
        :return: None
        """
        self.pointinfo.selectedPoint = points
        self.createPointsRepresentation()
        self.updateViewGL()

    def deselectPoints(self):
        """
        Deselect all points.
        :return: None
        """
        self.selectPoints(Index([]))

    def deleteSelection(self):
        """
        Delete all selected points.
        :return: None
        """
        if len(self.pointinfo.selectedPoint) == 0:
            # No point selected
            return

        self.createBackup("points")

        self.setNewPointset(
            PointSet(
                self.points.pointList.opposite_subset(self.pointinfo.selectedPoint),
                self.points.colorList.opposite_subset(self.pointinfo.selectedPoint),
            )
        )

    def keepSelection(self):
        """
        Delete non-selected points.
        :return: None
        """
        if len(self.pointinfo.selectedPoint) == 0:
            # No point selected
            return

        self.createBackup("points")

        self.setNewPointset(
            PointSet(
                self.points.pointList.subset(self.pointinfo.selectedPoint),
                self.points.colorList.subset(self.pointinfo.selectedPoint),
            )
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            self.openFile(str(url.toLocalFile()))
        self.updateViewGL()

    def setTheme(self, theme=BlackTheme, setBg=True):
        self.theme = theme

        if setBg:
            self.setBackgroundColor(QColor(*self.theme["BackGround"]))

        self.pointMaterial = Material(self.theme["Points"], 1)
        self.contractedpointMaterial = Material(self.theme["ContractedPoints"], 1)
        self.ctrlPointColor = self.theme["CtrlPoints"]
        self.newCtrlPointColor = self.theme["NewCtrlPoints"]
        self.edgeInfMaterial = Material(self.theme["EdgeInf"], 1)
        self.edgePlusMaterial = Material(self.theme["EdgePlus"], 1)
        self.selectedPointColor = Material(self.theme["SelectedCtrlPoints"], 1)
        self.radiusMaterial = Material(self.theme["Radius"], 1)
        self.modelMaterial = Material(self.theme["3DModel"], 1, transparency=0.2)
        self.hullMaterial = Material(self.theme["3DHull"], 1, transparency=0.2)

    def updateTheme(self, theme=BlackTheme):
        self.setTheme(theme)
        if self.mtg:
            self.updateMTGView()
        self.updateViewGL()

    def getparamcache(self, name, defaultvalue):
        if name in self.paramcache:
            return self.paramcache[name]
        else:
            return defaultvalue

    def setparamcache(self, name, value):
        self.paramcache[name] = value

    def createBackup(self, name):
        self.backup.make_backup(name)
        self.undoAvailable.emit(True)
        self.redoAvailable.emit(False)
        self.discardTempInfoDisplay()

    def undo(self):
        if self.backup.restore_backup():
            self.redoAvailable.emit(True)
            self.updateViewGL()
        else:
            self.showMessage("No backup available.")
            self.undoAvailable.emit(False)

    def redo(self):
        if self.backup.restore_redo():
            self.undoAvailable.emit(True)
            self.updateViewGL()
        else:
            self.showMessage("No redo available.")
            self.redoAvailable.emit(False)

    def enabledClippingPlane(self, enabled):
        self.clippigPlaneEnabled = enabled
        if enabled:
            self.showMessage("Enabled Clipping Plane")
        else:
            self.showMessage("Disabled Clipping Plane")
        if self.isVisible():
            self.updateViewGL()

    def setFrontVisibility(self, value):
        self.frontVisibility = value
        if self.isVisible():
            self.updateViewGL()

    def setBackVisibility(self, value):
        self.backVisibility = value
        if self.isVisible():
            self.updateViewGL()

    def applySelectionTrigger(self, node):
        if self.selectionTrigger:
            self.selectionTrigger(node)
        self.selectionTrigger = None

    def setSelectionTrigger(self, func):
        self.selectionTrigger = func

    def init(self):
        # self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.AltModifier)
        # self.setHandlerKeyboardModifiers(QGLViewer.FRAME,  Qt.NoModifier)
        # self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.ControlModifier)
        # self.setMouseBinding(Qt.LeftButton,QGLViewer.FRAME,QGLViewer.TRANSLATE)

        self.setMouseBindingDescription(
            Qt.ShiftModifier, Qt.LeftButton, "Rectangular selection"
        )
        self.setMouseBindingDescription(
            Qt.NoModifier, Qt.LeftButton, "Camera/Control Points manipulation"
        )
        self.setMouseBindingDescription(
            Qt.NoModifier,
            Qt.LeftButton,
            "When double clicking on a line, create a new line",
            True,
        )
        self.setMode(self.Rotate)
        self.camera().setViewDirection(Vec(0, -1, 0))
        self.camera().setUpVector(Vec(0, 0, 1))
        self.setBackgroundColor(QColor(*self.theme["BackGround"]))

    def setFocus(self, point):
        """Set focus to given control point"""
        if self.focus:
            self.focus.hasFocus = False
            self.__update_ctrlpoint__(self.focus.id)
        self.focus = point
        if self.focus:
            point.hasFocus = True
            self.__update_ctrlpoint__(self.focus.id)

    def setSelection(self, point):
        """Set focus to given control point"""
        if self.selection:
            self.selection.selected = False
            self.__update_ctrlpoint__(self.selection.id)
        self.selection = point
        if self.selection:
            point.selected = True
            self.__update_ctrlpoint__(point.id)
            self.camera().setRevolveAroundPoint(toVec(point.position()))

    def endSelection(self, p):
        selection = self.getMultipleSelection()
        selectIndex = Index([])
        selectAlreadySelectedPoint = False

        if self.poleSelection.isEnabled():
            self.poleSelection.execute(selection)
            return

        if selection is not None:
            for zmin, zmax, id in selection:
                if self.selectMode == self.AddSelect or id[0] == self.shapePoints.id:
                    selectIndex.append(id[1])
                elif (
                    len(self.pointinfo.selectedPoint) > 0
                    and id[0] == self.shapeSelection.id
                ):
                    if self.selectMode == self.HybridSelect:
                        selectAlreadySelectedPoint = True
                        break

            if selectAlreadySelectedPoint:
                selectIndex = Index([])
                for zmin, zmax, id in selection:
                    if id[0] == self.shapeSelection.id:
                        selectIndex.append(id[1])
                self.pointinfo.selectedPoint = (
                    self.pointinfo.selectedPoint.opposite_subset(selectIndex)
                )

        if not selectAlreadySelectedPoint:
            if self.selectMode == self.AddSelect:
                self.pointinfo.selectedPoint.append(selectIndex)
            else:
                self.pointinfo.selectedPoint = Index([])
                self.selectMode = self.AddSelect
                self.select(self.rectangleSelect.center())

    def fastDraw(self):
        """paint in opengl"""
        if self.bgimage:
            self.drawBackground()

        glDisable(GL_LIGHTING)

        if self.pointDisplay and self.points:
            self.pointsRep.apply(self.glrenderer)

        if self.mtgDisplay and self.mtgrep:
            self.mtgrep.apply(self.glrenderer)

        if self.ctrlPointDisplay and self.focus:
            scid = self.ctrlPointsRepIndex[self.focus.id]
            self.ctrlPointsRep[scid].apply(self.glrenderer)

    def draw(self):
        """paint in opengl"""
        if self.bgimage:
            self.drawBackground()

        if self.clippigPlaneEnabled:
            glPushMatrix()
            glLoadIdentity()
            zNear = self.camera().zNear()
            zFar = self.camera().zFar()
            zDelta = (zFar - zNear) / 2
            viewDir = self.camera().viewDirection()
            if self.frontVisibility > 0:
                eq = [0.0, 0.0, -1.0, -(zNear + zDelta * self.frontVisibility)]
                glClipPlane(GL_CLIP_PLANE0, eq)
                glEnable(GL_CLIP_PLANE0)
            if self.backVisibility < 1.0:
                eq2 = [0.0, 0.0, 1.0, (zNear + zDelta * self.backVisibility)]
                glClipPlane(GL_CLIP_PLANE1, eq2)
                glEnable(GL_CLIP_PLANE1)

            glPopMatrix()
        else:
            glDisable(GL_CLIP_PLANE0)
            glDisable(GL_CLIP_PLANE1)
        glDisable(GL_LIGHTING)

        if self.pointDisplay and self.pointsRep:
            self.pointsRep.apply(self.glrenderer)

        if self.pointAttributeDisplay and self.pointsAttributeRep:
            self.pointsAttributeRep.apply(self.glrenderer)

        if self.mtgDisplay and self.mtgrep:
            self.mtgrep.apply(self.glrenderer)

        if self.ctrlPointDisplay and self.ctrlPointsRep:
            if self.focus is None:
                self.ctrlPointsRep.apply(self.glrenderer)
            else:
                scid = self.ctrlPointsRepIndex[self.focus.id]
                self.ctrlPointsRep[scid].apply(self.glrenderer)

        if self.radiusDisplay and self.radiusRep:
            self.radiusRep.apply(self.glrenderer)

        glEnable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        if self.modelDisplay and self.modelRep:
            self.modelRep.apply(self.glrenderer)

        if self.customObjDisplay and self.customObjRep:
            self.customObjRep.apply(self.glrenderer)

        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)

        if self.temporaryinfo2D:
            self.startScreenCoordinatesSystem()
            self.temporaryinfo2D.apply(self.glrenderer)
            self.stopScreenCoordinatesSystem()

        if self.temporaryinfo:
            self.temporaryinfo.apply(self.glrenderer)

    def postDraw(self):
        if self.mode == self.Selection and self.rectangleSelect is not None:
            self.__drawSelectionRectangle()

    # Selection functions
    def drawWithNames(self):
        self.glrenderer.renderingMode = self.glrenderer.Selection
        self.glrenderer.selectionMode = self.glrenderer.SceneObjectNPrimitive
        if self.selectMode == self.AddSelect:
            Scene(
                [
                    Shape(
                        PointSet(self.points.pointList, self.points.colorList),
                        self.pointMaterial,
                    )
                ]
            ).apply(self.glrenderer)
        else:
            self.pointsRep.apply(self.glrenderer)

    def __drawSelectionRectangle(self):
        self.startScreenCoordinatesSystem()
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)

        glColor4f(0.0, 0.0, 0.3, 0.3)
        glBegin(GL_QUADS)
        glVertex2i(self.rectangleSelect.left(), self.rectangleSelect.top())
        glVertex2i(self.rectangleSelect.right(), self.rectangleSelect.top())
        glVertex2i(self.rectangleSelect.right(), self.rectangleSelect.bottom())
        glVertex2i(self.rectangleSelect.left(), self.rectangleSelect.bottom())
        glEnd()

        glLineWidth(2.0)
        glColor4f(0.4, 0.4, 0.5, 0.5)
        glBegin(GL_LINE_LOOP)
        glVertex2i(self.rectangleSelect.left(), self.rectangleSelect.top())
        glVertex2i(self.rectangleSelect.right(), self.rectangleSelect.top())
        glVertex2i(self.rectangleSelect.right(), self.rectangleSelect.bottom())
        glVertex2i(self.rectangleSelect.left(), self.rectangleSelect.bottom())
        glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        self.stopScreenCoordinatesSystem()

    def setTempInfoDisplay2D(self, sc):
        self.temporaryinfo2D = sc

    def setTempInfoDisplay(self, sc):
        self.temporaryinfo = sc

    def discardTempInfoDisplay(self):
        self.temporaryinfo2D = None
        self.temporaryinfo = None

    def setCustomGeometry(self, sc):
        if isinstance(sc, str):
            sc = Scene(sc)
        self.customObjRep = sc
        self.customObjDisplay = True

    def clearCustomGeometry(self):
        self.customObjRep = None
        self.customObjDisplay = False

    def setPointAttribute(self, sc):
        self.pointsAttributeRep = sc
        self.setPointAttributeDisplay(True)

    def setPointAttributeDisplay(self, enabled):
        if enabled != self.pointAttributeDisplay:
            self.pointAttributeDisplay = enabled
            self.PointAttributeDisplay.emit(enabled)

    def setclassicdata(self, dataedit, dataoriginal, pointname=None):
        from os.path import exists, join

        firstname = join(get_shared_data("mtg"), "edition", dataedit + ".bmtg")
        if exists(firstname):
            mtgname = firstname
        else:
            mtgname = join(get_shared_data("mtg"), dataoriginal + ".bmtg")
        self.readMTG(str(mtgname))
        self.mtgfile = firstname

        if pointname is None:
            pointname = dataedit
        pointfname = str(join(get_shared_data("pointset"), pointname + ".bgeom"))
        print(pointfname)
        self.readPoints(pointfname)

    def puu1(self):
        self.setclassicdata("puu1", "puu1")

    def puu3(self):
        self.setclassicdata("puu3", "puu3")
        self.reorient()

    def cherry(self):
        self.setclassicdata("cherry", "cherry", "cherry_200k")

    def arabido(self):
        self.setclassicdata("arabido", "arabido", "arabido-yassin-200k")
        self.reorient()

    def appletree(self):
        self.readMTG(
            "/Users/fboudon/Develop/oagit/plantscan3d/data/LidarPommier/digitmtg/X0342_r1.mtg",
            True,
        )
        self.readPoints(
            "/Users/fboudon/Develop/oagit/plantscan3d/data/LidarPommier/digitmtg/X0342_r1_004.xyz"
        )
        self.alignScaleAndCenter()

    def openFile(self, fname, ftype=None):
        if ftype == "MTG":
            self.readMTG(fname)
        elif ftype == "iMTG":
            self.readMTG(fname, True)
        elif ftype == "PTS":
            self.readPoints(fname)
        elif ftype is None:
            import os.path as op

            ext = op.splitext(fname)[1][1:]
            if ext in ["mtg", "bmtg"]:
                if self.mtg is not None:
                    self.createBackup("mtg")
                self.readMTG(fname)
                self.filehistory.add(fname, "MTG")
            elif ext in ["asc", "xyz", "pwn", "pts", "txt", "bgeom", "ply"]:
                if self.points is not None:
                    self.createBackup("points")
                self.readPoints(fname)
                self.filehistory.add(fname, "PTS")
            else:
                QMessageBox.warning(
                    self, "Unknow File", "Cannot read file " + repr(fname)
                )
                return
        else:
            QMessageBox.warning(self, "Unknow File", "Cannot read file " + repr(fname))
            return
        self.open_file.emit()

    def openMTG(self):
        lastfile = self.filehistory.getLastFile("MTG")
        initialname = (
            os.path.dirname(lastfile) if lastfile else get_shared_data("mtgdata")
        )
        fname = QFileDialog.getOpenFileName(
            self,
            "Open MTG file",
            initialname,
            "MTG Files (*.mtg;*.bmtg);;All Files (*.*)",
        )
        if not fname:
            return
        fname = str(fname[0])
        if len(fname) == 0:
            return
        self.filehistory.add(fname, "MTG")
        self.readMTG(fname)
        self.open_file.emit()

    def importMTG(self):
        lastfile = self.filehistory.getLastFile("iMTG")
        initialname = (
            os.path.dirname(lastfile) if lastfile else get_shared_data("mtgdata")
        )
        fname = QFileDialog.getOpenFileName(
            self, "Open MTG file", initialname, "MTG Files (*.mtg);;All Files (*.*)"
        )
        if not fname or len(fname):
            return
        fname = str(fname[0])
        if len(fname) == 0:
            return
        self.filehistory.add(fname, "iMTG")
        self.readMTG(fname, True)
        self.open_file.emit()

    def readMTG(self, fname, fromdigit=False):
        import os.path
        import sys
        import traceback as tb

        self.showMessage("Reading " + repr(fname))
        try:
            if os.path.splitext(fname)[1] == ".bmtg":
                mtg = readfile(fname)
            else:  # .mtg
                # readable mtg format from openalea.mtg module
                stdmtg = read_mtg_file(fname)
                if fromdigit:
                    convertStdMTGWithNode(stdmtg)
                else:
                    stdmtg = convertToMyMTG(stdmtg)
                mtg = stdmtg

            self.modelRep = None
            self.setMTG(mtg, fname)
            self.showEntireScene()
        except Exception as e:
            tb.print_exception(*sys.exc_info())
            QMessageBox.critical(self, "Import Error", "Import Error:" + repr(e))

    def setMTG(self, mtg, fname):
        self.mtg = mtg
        self.mtgfile = fname

        self.selection = None
        self.focus = None

        self.__update_all_mtg__()

    def updateMTGView(self):
        pt = self.camera().revolveAroundPoint()
        self.setMTG(self.mtg, self.mtgfile)
        self.camera().setRevolveAroundPoint(pt)

    def getUnitCtrlPointSize(self):
        scradius = self.sceneRadius()
        return scradius / 400

    def setNodeWidth(self, value):
        self.nodeWidth = value
        if self.ctrlPointPrimitive:
            self.ctrlPointPrimitive.radius = (
                self.nodeWidth * self.getUnitCtrlPointSize()
            )
        self.updateViewGL()

    def createCtrlPoints(self):
        self.ctrlPoints = createCtrlPoints(
            self.mtg, self.ctrlPointColor, self.propertyposition, self.__update_value__
        )
        if self.mode == self.TagScale:
            self.tagScaleRepresentation()
        elif self.mode == self.TagProperty:
            self.tagPropertyRepresentation()
        self.createCtrlPointRepresentation()

    def createCtrlPointRepresentation(self):
        self.ctrlPointsRep = Scene(
            [
                ctrlPoint.representation(self.ctrlPointPrimitive)
                for ctrlPoint in self.ctrlPoints.values()
            ]
        )
        self.ctrlPointsRepIndex = dict(
            [(sh.id, i) for i, sh in enumerate(self.ctrlPointsRep)]
        )
        # self.ctrlPointsRepIndex = {2:0, 3:1, ..., 4362: 4360}

    def save(self):
        if self.mtgfile:
            self.writeMTG(self.mtgfile)
        else:
            self.saveMTG()

    def saveMTG(self):
        initialname = (
            os.path.dirname(self.mtgfile)
            if self.mtgfile
            else get_shared_data("mtgdata")
        )
        fname = QFileDialog.getSaveFileName(
            self,
            "Save MTG file",
            initialname,
            "MTG Files (*.mtg;*.bmtg);;All Files (*.*)",
        )
        fname = str(fname[0])
        if len(fname) == 0:
            return
        self.filehistory.add(fname, "MTG")
        self.writeMTG(fname)

    def writeMTG(self, fname):
        fname = str(fname)
        import os.path
        import shutil

        if os.path.exists(fname):
            shutil.copy(fname, fname + "~")
        if os.path.splitext(fname)[1] == ".bmtg":
            writefile(fname, self.mtg)
        else:  # .mtg
            # readable mtg format from openalea.mtg module
            stdmtg = convertToStdMTG(self.mtg)
            writeMTGfile(fname, stdmtg)
        self.mtgfile = fname
        self.showMessage("Write MTG in " + repr(fname))
        self.updateViewGL()

    def filter_points(self, pointset, pointfilter=None, ignorednodes=None):
        if pointfilter is None:
            pointfilter = self.pointfilter
        if ignorednodes is not None:
            ignorednodes = set(ignorednodes)

        if pointfilter > 0 and self.mtg:
            if ignorednodes:
                nodeids = [
                    vid
                    for vid in self.mtg.vertices(scale=self.mtg.max_scale())
                    if vid not in ignorednodes
                ]
                nonone = lambda x, y: y if (x is None or x in ignorednodes) else x
            else:
                nodeids = list(self.mtg.vertices(scale=self.mtg.max_scale()))
                nonone = lambda x, y: y if (x is None) else x

            pos = self.mtg.property("position")
            nodes = [pos[i] for i in nodeids]

            nodeiddict = dict([(vid, i) for i, vid in enumerate(nodeids)])
            parents = [nodeiddict[nonone(self.mtg.parent(i), i)] for i in nodeids]

            print("points_at_distance_from_skeleton", pointfilter)
            distantpoints = points_at_distance_from_skeleton(
                pointset.pointList, nodes, parents, -pointfilter, 1
            )
            # print distantpoints
            if pointset.colorList:
                return pointset.pointList.subset(
                    distantpoints
                ), pointset.colorList.subset(distantpoints)
            else:
                return pointset.pointList.subset(distantpoints), pointset.colorList
        else:
            return pointset.pointList, pointset.colorList

    def createPointsRepresentation(self):
        pointList, colorList = self.filter_points(self.points)

        if len(self.pointinfo.selectedPoint) > 0:
            selectedPoints, otherPoints = pointList.split_subset(
                self.pointinfo.selectedPoint
            )
            selectedColors, otherColors = colorList.split_subset(
                self.pointinfo.selectedPoint
            )

            selectedColors = Color4Array(
                [Color4(255, 0, 0, 0) for i in range(len(selectedColors))]
            )

            self.shapePoints = Shape(
                PointSet(otherPoints, otherColors, width=self.pointinfo.pointWidth),
                self.pointMaterial,
            )
            self.shapeSelection = Shape(
                PointSet(
                    selectedPoints, selectedColors, width=self.pointinfo.pointWidth + 2
                ),
                self.pointMaterial,
            )
            self.pointsRep = Scene([self.shapePoints, self.shapeSelection])
        else:
            self.shapePoints = Shape(
                PointSet(pointList, colorList, width=self.pointinfo.pointWidth),
                self.pointMaterial,
            )
            self.pointsRep = Scene([self.shapePoints])

    def setPointFilter(self, value):
        self.pointfilter = self.sceneRadius() * value / 10.0
        if self.points:
            self.createPointsRepresentation()
        if self.isVisible():
            self.updateViewGL()

    def setPointWidth(self, value):
        self.pointinfo.pointWidth = value
        if self.pointsRep:
            self.pointsRep[0].geometry.width = value
            if len(self.pointinfo.selectedPoint) > 0:
                self.pointsRep[1].geometry.width = value + 2
        self.updateViewGL()

    def show3DModel(self):
        self.create3DModelRepresentation()
        self.modelDisplay = True
        self.updateViewGL()

    def create3DModelRepresentation(self, translation=None):
        scene = Scene()
        section = Polyline2D.Circle(1, 30)
        hulls = self.mtg.properties().get("hull", {})

        def get_radius(nodeid):
            val = self.mtg.property(self.propertyradius).get(nodeid, 0)
            if val is None:
                val = 0
            return val, val

        for vid in self.mtg.vertices(scale=self.mtg.max_scale()):
            if self.mtg.parent(vid) is None or self.mtg.edge_type(vid) == "+":
                axe = self.mtg.Axis(vid)
                if self.mtg.parent(vid) is not None:
                    axe.insert(0, self.mtg.parent(vid))
                if len(axe) > 2:
                    points = [
                        self.mtg.property(self.propertyposition)[nodeID]
                        for nodeID in axe
                    ]
                    radius = [get_radius(nodeID) for nodeID in axe]
                    geometry = Extrusion(Polyline(points), section, radius)
                    if translation:
                        geometry = Translated(translation, geometry)
                    scene += Shape(geometry, self.modelMaterial, vid)
            if vid in hulls:
                shape = hulls[vid]
                scene += Shape(shape, self.hullMaterial, vid)

        self.modelRep = scene

    def importPoints(self):
        lastfile = self.filehistory.getLastFile("PTS")
        initialname = (
            os.path.dirname(lastfile) if lastfile else get_shared_data("pointset")
        )

        fname = QFileDialog.getOpenFileName(
            self,
            "Open Points file",
            initialname,
            "Points Files (*.asc *.xyz *.pwn *.pts *.txt *.bgeom *.xyz *.ply);;All Files (*.*)",
        )
        fname = str(fname[0])
        if len(fname) == 0:
            return
        self.filehistory.add(fname, "PTS")
        self.readPoints(fname)
        self.open_file.emit()

    def readPoints(self, fname):
        self.progressdialog.setOneShot(True)
        try:
            sc = Scene(fname)
        finally:
            self.progressdialog.setOneShot(False)

        if len(sc) == 0:
            QMessageBox.warning(
                self, "file error", "Not able to read points from file " + repr(fname)
            )
            return
        try:
            points = sc[0].geometry.geometry
            self.translation = sc[0].geometry.translation
            points.pointList.translate(self.translation)
        except AttributeError:
            points = sc[0].geometry
            self.translation = Vector3(0, 0, 0)
        self.setPoints(points)
        self.showEntireScene()

    def RecalculateColors(self):
        self.points.colorList = generate_point_color(self.points)
        self.createPointsRepresentation()
        self.updateViewGL()

    def setPoints(self, points, keepInfo=False):
        self.points = points

        self.pointsAttributeRep = None
        if not keepInfo:
            self.pointinfo = PointInfo()

        if self.points.colorList is None:
            self.points.colorList = generate_point_color(self.points)

        self.selectBuffSize = len(self.points.pointList) * 5
        self.setSelectBufferSize(self.selectBuffSize)

        self.adjustTo(points)
        self.createPointsRepresentation()

    def exportPoints(self):
        lastfile = self.filehistory.getLastFile("PTS")
        initialname = (
            os.path.dirname(lastfile) if lastfile else get_shared_data("pointset")
        )

        fname = QFileDialog.getSaveFileName(
            self,
            "Save Points file",
            initialname,
            "Points Files (*.asc *.xyz *.pwn *.pts *.bgeom *.ply);;All Files (*.*)",
        )
        fname = str(fname[0])
        if len(fname) == 0:
            return
        self.filehistory.add(fname, "PTS")
        self.savePoints(fname, self.points)

    def savePoints(self, fname, points):
        Scene([points]).save(fname)

    def exportAsGeom(self):
        initialname = "out.bgeom"
        fname = QFileDialog.getSaveFileName(
            self,
            "Save 3D file",
            initialname,
            "GEOM Files (*.bgeom;*.geom);;OBJ Files (*.obj);;Other formats (*.*)",
        )
        fname = str(fname[0])
        if len(fname) == 0:
            return
        self.saveAsGeom(fname)

    def saveAsGeom(self, fname):
        sc = Scene()
        import os.path

        meshonly = False

        ext = os.path.splitext(fname)[1][1:]
        if ext in ["obj"]:
            meshonly = True

        if self.pointDisplay and self.points and not meshonly:
            sc += self.pointsRep
            # sc += Shape(Translated(self.translation,PointSet(self.points.pointList)), self.pointMaterial)

        if self.pointAttributeDisplay and self.pointsAttributeRep and not meshonly:
            sc += self.pointsAttributeRep

        if self.mtgDisplay and self.mtgrep and not meshonly:
            sc += self.mtgrep
            # mtgrep, mtgrepindex  = createMTGRepresentation(self.mtg,self.edgeInfMaterial,self.edgePlusMaterial, translation=self.translation)
            # sc += mtgrep

        if self.ctrlPointDisplay and self.ctrlPointsRep:
            sc += self.ctrlPointsRep
            # sc += Scene([ ctrlPoint.representation(self.ctrlPointPrimitive) for ctrlPoint in self.ctrlPoints.itervalues() ])

        if self.modelDisplay and self.modelRep:
            sc += self.modelRep  # self.create3DModelRepresentation(self.translation)

        if self.radiusDisplay and self.radiusRep and not meshonly:
            sc += self.radiusRep

        if self.temporaryinfo:
            sc += self.temporaryinfo

        sc.save(fname)

    def exportNodeList(self):
        initialname = (
            os.path.dirname(self.mtgfile)
            + "/"
            + os.path.basename(self.mtgfile)
            + ".txt"
            if self.mtgfile
            else get_shared_data("mtgdata")
        )
        fname = QFileDialog.getSaveFileName(
            self, "Save Geom file", initialname, "Txt Files (*.txt);;All Files (*.*)"
        )
        fname = str(fname[0])
        if len(fname) == 0:
            return
        self.saveNodeList(fname)
        self.showMessage("Export in " + fname + " done ...")

    def saveNodeList(self, fname):
        stream = open(fname, "w")
        position = self.mtg.property("position")
        radius = self.mtg.property("radius")
        stream.write("# automatically exported mtg\n")
        stream.write("# vid parentid edgetype XX YY ZZ Radius\n")
        stream.write(str(self.mtg.nb_vertices(scale=self.mtg.max_scale())) + "\n")
        for vid in self.mtg.vertices(scale=self.mtg.max_scale()):
            p = position[vid]
            stream.write(
                str(vid)
                + "\t"
                + ("" if self.mtg.parent(vid) is None else str(self.mtg.parent(vid)))
                + "\t"
                + str(self.mtg.edge_type(vid))
                + "\t"
                + str(p.x)
                + "\t"
                + str(p.y)
                + "\t"
                + str(p.z)
                + "\t"
                + str(radius.get(vid, ""))
                + "\n"
            )
        stream.close()

    def adjustTo(self, obj):
        bbx = BoundingBox(obj)
        self.setSceneBoundingBox(
            toVec(bbx.lowerLeftCorner), toVec(bbx.upperRightCorner)
        )

    def __update_ctrlpoint__(self, pid):
        scid = self.ctrlPointsRepIndex[pid]
        self.ctrlPointsRep[scid] = self.ctrlPoints[pid].representation(
            self.ctrlPointPrimitive
        )

    def __update_edges__(self, pid):
        eid = self.mtgrepindex.get(pid)
        positions = self.mtg.property(self.propertyposition)
        mat = (
            self.edgeInfMaterial
            if self.mtg.edge_type(pid) == "<"
            else self.edgePlusMaterial
        )
        if eid is not None:
            self.mtgrep[eid] = createEdgeRepresentation(
                self.mtg.parent(pid), pid, positions, mat
            )
        for son in self.mtg.children(pid):
            mat = (
                self.edgeInfMaterial
                if self.mtg.edge_type(son) == "<"
                else self.edgePlusMaterial
            )
            self.mtgrep[self.mtgrepindex[son]] = createEdgeRepresentation(
                pid, son, positions, mat
            )

    def __update_radius__(self, pid):
        positions = self.mtg.property(self.propertyposition)
        if self.mtg.property(self.propertyradius).get(pid):
            rep = createRadiusRepresentation(
                self.mtg,
                pid,
                positions,
                self.mtg.property(self.propertyradius),
                self.radiusMaterial,
            )
            if self.radiusRepIndex.get(pid) is not None:
                self.radiusRep[self.radiusRepIndex[pid]] = rep
            else:
                self.radiusRepIndex[pid] = len(self.radiusRep)
                self.radiusRep.add(rep)

    def __update_value__(self, pid):
        """update rep of mtg"""
        self.__update_ctrlpoint__(pid)
        self.__update_edges__(pid)
        self.__update_radius__(pid)

    def __update_all_mtg__(self):
        self.mtgrep, self.mtgrepindex = createMTGRepresentation(
            self.mtg, self.edgeInfMaterial, self.edgePlusMaterial
        )

        pointsize = self.nodeWidth * self.getUnitCtrlPointSize()
        self.ctrlPointPrimitive = Sphere(pointsize)
        self.createCtrlPoints()

        if self.points is None:
            self.adjustTo(self.ctrlPointsRep)

            pointsize = self.nodeWidth * self.getUnitCtrlPointSize()
            self.ctrlPointPrimitive.radius = (
                self.nodeWidth * self.getUnitCtrlPointSize()
            )

        self.radiusRep, self.radiusRepIndex = createRadiiRepresentation(
            self.mtg,
            self.radiusMaterial,
            positionproperty=self.propertyposition,
            radiusproperty=self.propertyradius,
        )

    def enablePointDisplay(self, enabled):
        if self.pointDisplay != enabled:
            self.pointDisplay = enabled
            self.updateViewGL()

    def enablePointAttributeDisplay(self, enabled):
        if self.pointAttributeDisplay != enabled:
            self.pointAttributeDisplay = enabled
            self.updateViewGL()

    def enableMTGDisplay(self, enabled):
        if self.mtgDisplay != enabled:
            self.mtgDisplay = enabled
            self.updateViewGL()

    def enableControlPointsDisplay(self, enabled):
        if self.ctrlPointDisplay != enabled:
            self.ctrlPointDisplay = enabled
            self.updateViewGL()

    def enable3DModelDisplay(self, enabled):
        if self.modelDisplay != enabled:
            self.modelDisplay = enabled
            self.updateViewGL()

    def enableRadiusDisplay(self, enabled):
        if self.radiusDisplay != enabled:
            self.radiusDisplay = enabled
            self.updateViewGL()

    def isPointDisplayEnabled(self):
        return self.pointDisplay

    def isPointAttributeDisplayEnabled(self):
        return self.pointAttributeDisplay

    def isMTGDisplayEnabled(self):
        return self.mtgDisplay

    def isControlPointsDisplayEnabled(self):
        return self.ctrlPointDisplay

    def is3DModelDisplayEnabled(self):
        return self.modelDisplay

    def isRadiusDisplayEnabled(self):
        return self.radiusDisplay

    def adjustView(self):
        self.showEntireScene()

    def refreshView(self):
        self.setMTG(self.mtg, self.mtgfile)

    def getSelection(self, pos):
        possibles = []
        if self.ctrlPoints and self.ctrlPointDisplay:
            for cCtrlPoint in self.ctrlPoints.values():
                cCtrlPoint.checkIfGrabsMouse(pos.x(), pos.y(), self.camera())
                if cCtrlPoint.grabsMouse():
                    pz = self.camera().viewDirection() * (
                        cCtrlPoint.position() - self.camera().position()
                    )
                    z = (pz - self.camera().zNear()) / (
                        self.camera().zFar() - self.camera().zNear()
                    )
                    if (
                        z > 0
                        and not self.clippigPlaneEnabled
                        or self.frontVisibility <= z * 2 <= self.backVisibility
                    ):
                        possibles.append((z, cCtrlPoint))
        if len(possibles) > 0:
            possibles.sort(key=lambda x: x[0])
            return possibles[0][1]
        return None

    def registerEventListener(self, module):
        """
        Register a module as an event listener.
        :param module: The module to register.
        :return: None
        """
        if self.eventListeners.count(module) == 0:
            # The module is not registered yet
            self.eventListeners.append(module)

    def unregisterEventListener(self, module):
        """
        Unregister a module from being an event listener.
        :param module: The module to unregister.
        :return: None
        """
        try:
            self.eventListeners.remove(module)
        except:
            pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # Cancel pole selection
            if self.poleSelection.isEnabled():
                self.poleSelection.stop()

            # Cancel wire selection
            if self.wireSelection.isEnabled():
                self.wireSelection.cancel()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Continue the wire selection process
            if self.wireSelection.isEnabled():
                self.wireSelection.useSelection()

        globalpos = self.geometry().topLeft()
        p = self.parent()
        while p:
            globalpos += p.geometry().topLeft()
            p = p.parent()

        mousepos = QCursor.pos() - globalpos
        cCtrlPoint = self.getSelection(mousepos)
        if cCtrlPoint:
            if event.key() == Qt.Key_T:
                self.setSelection(cCtrlPoint)
                self.stickToPoints()
            elif event.key() == Qt.Key_G:
                self.setSelection(cCtrlPoint)
                self.stickSubtree()
            elif event.key() == Qt.Key_R:
                self.setSelection(cCtrlPoint)
                self.revolveAroundSelection()
            elif event.key() == Qt.Key_N:
                self.setSelection(cCtrlPoint)
                self.newChild()
            elif event.key() == Qt.Key_M:
                self.setSelection(cCtrlPoint)
                self.setAxialPoint()
            elif event.key() == Qt.Key_P:
                self.setSelection(cCtrlPoint)
                self.beginReparentSelection()
            elif event.key() == Qt.Key_E:
                self.setSelection(cCtrlPoint)
                self.splitEdge()
            elif event.key() == Qt.Key_Delete:
                self.setSelection(cCtrlPoint)
                self.removeSelection()
            elif event.key() == Qt.Key_A:
                self.setSelection(cCtrlPoint)
                self.increaseSelectionRadius()
            elif event.key() == Qt.Key_Q:
                self.setSelection(cCtrlPoint)
                self.decreaseSelectionRadius()
            else:
                QGLViewer.keyPressEvent(self, event)
        else:
            print("default key press")
            QGLViewer.keyPressEvent(self, event)

    def mousePressEvent(self, event):
        """Check for eventual operations the user.old asks:
        shift start rectangular selection
        else check for which point is selected
        :type event: QMouseEvent
        """
        nompe = False
        if self.poleSelection.isEnabled():
            nompe = True
        elif self.mode == self.TagScale:
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setSelection(cCtrlPoint)
                if event.button() == Qt.RightButton:
                    self.setSelection(cCtrlPoint)
                    self.updateViewGL()
                    self.contextMenu(event.globalPos())
                    nompe = True
                else:
                    self.tagScaleToNode()
                    self.updateViewGL()
            else:
                self.setMode(self.Rotate | self.TagScale)

        elif self.mode == self.TagProperty:
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setSelection(cCtrlPoint)
                if event.button() == Qt.RightButton:
                    self.setSelection(cCtrlPoint)
                    self.updateViewGL()
                    self.contextMenu(event.globalPos())
                    nompe = True
                else:
                    self.tagPropertyToNode()
                    self.updateViewGL()
            else:
                self.setMode(self.Rotate | self.TagProperty)

        elif self.mode == self.Selection:
            # Selection of a second point to finish a previous action
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.applySelectionTrigger(cCtrlPoint)
            else:
                QMessageBox.warning(self, "Selection", "Cannot find a node to select")
        elif event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
            self.selectMode = self.HybridSelect
            self.rectangleSelect = QRect(event.pos(), event.pos())
            self.mode = self.Selection
            nompe = True
        elif event.button() == Qt.LeftButton and event.modifiers() == (
            Qt.ShiftModifier | Qt.ControlModifier
        ):
            self.selectMode = self.AddSelect
            self.rectangleSelect = QRect(event.pos(), event.pos())
            self.mode = self.Selection
            nompe = True
        elif event.modifiers() & Qt.ControlModifier:
            # only rotation
            self.setSelection(None)
            self.setMode(self.Edit)
        elif event.button() == Qt.RightButton:
            # context menu asked
            self.setSelection(None)
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setSelection(cCtrlPoint)
                self.updateViewGL()
                self.contextMenu(event.globalPos())
                nompe = True
            else:
                self.setMode(self.Rotate)
        else:
            # move selection or rotate
            self.setSelection(None)
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setFocus(cCtrlPoint)
                self.createBackup("mtg")
                self.camera().setRevolveAroundPoint(toVec(cCtrlPoint.position()))
                self.setManipulatedFrame(cCtrlPoint)
                self.showMessage("Move point " + str(cCtrlPoint.id))
                # move manipulated frame
                self.setMode(self.Edit)
                self.updateViewGL()
            else:  # if no point is selected, then move camera
                self.setMode(self.Rotate)
        if not nompe:
            QGLViewer.mousePressEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        cCtrlPoint = self.getSelection(event.pos())
        if cCtrlPoint:
            print("Select point ", cCtrlPoint.id)
            if self.mode == self.Selection:
                self.applySelectionTrigger(cCtrlPoint)
            else:
                self.camera().setRevolveAroundPoint(toVec(cCtrlPoint.position()))

    def mouseMoveEvent(self, event):
        """On mouse release, we release every grabbed objects"""
        if event.buttons() == Qt.NoButton:
            return

        if self.mode == self.Selection:
            # Updates rectangle_ coordinates and redraws rectangle
            if self.rectangleSelect:
                self.rectangleSelect.setBottomRight(event.pos())
            self.updateViewGL()
        else:
            QGLViewer.mouseMoveEvent(self, event)

    def leaveEvent(self, event):
        self.cursor.setIsMouseOver(False)

    def enterEvent(self, event):
        self.cursor.setIsMouseOver(True)

    def mouseReleaseEvent(self, event):
        """On mouse release, we release every grabbed objects"""
        QGLViewer.mouseReleaseEvent(self, event)

        # clear manipulated object
        self.setManipulatedFrame(None)
        self.setFocus(None)
        if self.poleSelection.isEnabled():
            if event.button() == Qt.LeftButton:
                self.poleSelection.select(event.pos())
        elif self.mode & self.TagScale:
            self.setMode(self.TagScale)
        elif self.mode & self.TagProperty:
            self.setMode(self.TagProperty)
        elif self.mode == self.Selection:
            if self.rectangleSelect:
                self.rectangleSelect.setBottomRight(event.pos())
                self.rectangleSelect = self.rectangleSelect.normalized()
                # Define selection window dimensions
                self.setSelectRegionWidth(self.rectangleSelect.width())
                self.setSelectRegionHeight(self.rectangleSelect.height())
                # Compute rectangle center and perform selection

                if self.selectBuffSize != self.selectBufferSize():
                    print("setSelectBufferSize")
                    self.setSelectBufferSize(self.selectBuffSize)
                self.select(self.rectangleSelect.center())
                self.rectangleSelect = None
                # Update display to show new selected objects
                self.createPointsRepresentation()
                self.glrenderer.renderingMode = self.glrenderer.Dynamic
            self.setMode(self.Rotate)
        else:
            self.setMode(self.Rotate)
        self.updateViewGL()

    def contextMenu(self, pos):
        menu = QMenu(self)
        action = menu.addAction("Node " + str(self.selection.id))
        f = QFont()
        f.setBold(True)
        action.setFont(f)
        if self.mode not in [self.TagScale, self.TagProperty]:
            menu.addSeparator()
            menu.addAction("Remove node (DEL)", self.removeSelection)
            if len(list(self.mtg.children(self.selection.id))) > 0:
                menu.addAction("Remove subtree", self.removeSubtree)
            menu.addSeparator()
            menu.addAction("New child (N)", self.newChild)
            menu.addAction("Reparent (P)", self.beginReparentSelection)
            menu.addAction("Split Edge (E)", self.splitEdge)
            menu.addMenu(self.mainwindow.menuSkeletization)
        menu.addSeparator()
        menu.addAction("Set Branching Points", self.setBranchingPoint)
        menu.addAction("Set Axial Points (M)", self.setAxialPoint)
        menu.addSeparator()
        if self.points and self.mode not in [self.TagScale, self.TagProperty]:
            menu.addAction("S&tick to points (T)", self.stickToPoints)
            menu.addAction("Stick subtree (G)", self.stickSubtree)
            menu.addSeparator()
            submenu = menu.addMenu("Estimate radius")
            if self.selection.id in self.mtg.property(self.propertyradius):
                submenu.addAction("Increase (A)", self.increaseSelectionRadius)
                submenu.addAction("Decrease (Q)", self.decreaseSelectionRadius)
            submenu.addAction("Set", self.setSelectionRadius)
            submenu.addSeparator()
            submenu.addAction("As Mean Point Distance", self.estimateMeanRadius)
            submenu.addAction("As Max Point Distance", self.estimateMaxRadius)
            submenu.addAction("As Convex Hull Distance", self.estimateConvexHullRadius)
            submenu.addSeparator()
            submenu.addAction("Using Pipe Model", self.pipeModelOnSelection)
            menu.addSeparator()
            submenu = menu.addMenu("Hull")
            submenu.addAction("Convex Hull", self.convexHullOfSelection)
            submenu.addAction("Remove", self.removeHullOfSelection)
        else:
            submenu = menu.addMenu("Estimate radius")
            if self.selection.id in self.mtg.property(self.propertyradius):
                submenu.addAction("Increase (A)", self.increaseSelectionRadius)
                submenu.addAction("Decrease (Q)", self.decreaseSelectionRadius)
            submenu.addAction("Set", self.setSelectionRadius)

        menu.addSeparator()
        menu.addAction("Revolve Around (R)", self.revolveAroundSelection)
        menu.addSeparator()
        menu.addAction("Properties", self.editProperty)
        if self.mode == self.TagScale:
            menu.addSeparator()
            menu.addAction("Tag (A)", self.tagScaleToNode)
        elif self.mode == self.TagProperty:
            menu.addSeparator()
            menu.addAction("Tag (A)", self.tagPropertyToNode)
        menu.exec_(pos)

    def setMode(self, mode):
        if self.mode != mode:
            if mode == self.Edit or mode == self.Selection:
                self.mode = mode
                self.setMouseBinding(
                    Qt.NoModifier, Qt.LeftButton, QGLViewer.FRAME, QGLViewer.TRANSLATE
                )
                self.setMouseBinding(
                    Qt.NoModifier,
                    Qt.RightButton,
                    QGLViewer.FRAME,
                    QGLViewer.NO_MOUSE_ACTION,
                )

                self.setMouseBinding(
                    Qt.ControlModifier,
                    QtCore.Qt.LeftButton,
                    QGLViewer.CAMERA,
                    QGLViewer.ROTATE,
                )
                self.setMouseBinding(
                    Qt.ControlModifier,
                    QtCore.Qt.RightButton,
                    QGLViewer.CAMERA,
                    QGLViewer.TRANSLATE,
                )
                self.setMouseBinding(
                    Qt.ControlModifier,
                    QtCore.Qt.MiddleButton,
                    QGLViewer.CAMERA,
                    QGLViewer.ZOOM,
                )

                # self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.AltModifier)
                # self.setHandlerKeyboardModifiers(QGLViewer.FRAME,  Qt.NoModifier)
                # self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.ControlModifier)
            elif (
                mode == self.Rotate or mode == self.TagScale or mode == self.TagProperty
            ):
                self.mode = mode

                self.setMouseBinding(
                    QtCore.Qt.ControlModifier,
                    QtCore.Qt.LeftButton,
                    QGLViewer.FRAME,
                    QGLViewer.TRANSLATE,
                )
                self.setMouseBinding(
                    QtCore.Qt.ControlModifier,
                    QtCore.Qt.RightButton,
                    QGLViewer.FRAME,
                    QGLViewer.NO_MOUSE_ACTION,
                )
                self.setMouseBinding(
                    Qt.NoModifier,
                    QtCore.Qt.LeftButton,
                    QGLViewer.CAMERA,
                    QGLViewer.ROTATE,
                )
                self.setMouseBinding(
                    Qt.NoModifier,
                    QtCore.Qt.RightButton,
                    QGLViewer.CAMERA,
                    QGLViewer.TRANSLATE,
                )
                self.setMouseBinding(
                    Qt.NoModifier,
                    QtCore.Qt.MiddleButton,
                    QGLViewer.CAMERA,
                    QGLViewer.ZOOM,
                )

                # self.setHandlerKeyboardModifiers(QGLViewer.FRAME, Qt.AltModifier)
                # self.setHandlerKeyboardModifiers(QGLViewer.CAMERA,  Qt.NoModifier)
                # self.setHandlerKeyboardModifiers(QGLViewer.FRAME, Qt.ControlModifier)
            self.actionTagProperty.setChecked(self.mode & self.TagProperty)
            self.actionEditScale.setChecked(self.mode & self.TagScale)

    # ---------------------------- Checking ----------------------------------------
    def check_input_points(self):
        if self.points is None:
            QMessageBox.warning(self, "Points", "No points loaded")
            return False
        return True

    def check_input_mtg(self, msg=""):
        if self.mtg is None:
            QMessageBox.warning(self, "MTG", "No mtg loaded. " + msg)
            return False
        return True

    def check_input_data(self):
        if not self.check_input_points():
            return False
        return self.check_input_mtg()

    def createParamDialog(self, text, listparam):
        class MDialog(QDialog):
            def __init__(self, parent):
                QDialog.__init__(self, parent)
                self.resultgetter = []
                self.mparent = parent

            def getParams(self):
                result = [box() for box in self.resultgetter]
                self.mparent.setparamcache(text, result)
                return result

        prevparam = self.getparamcache(text, None)
        if prevparam and len(prevparam) != len(listparam):
            prevparam = None

        Dialog = MDialog(self)
        gridLayout = QGridLayout(Dialog)
        sectionLabel = QLabel(Dialog)
        sectionLabel.setText(text)
        gridLayout.addWidget(sectionLabel, 0, 0, 1, 2)
        space = QSpacerItem(1, 10)
        gridLayout.addItem(space, 1, 0, 1, 2)
        row = 2

        nbparam = 0
        for paraminfo in listparam:
            if len(paraminfo) == 3:
                pname, ptype, pdefvalue = paraminfo
                pparam = {}
            else:
                pname, ptype, pdefvalue, pparam = paraminfo
            if prevparam:
                pdefvalue = prevparam[nbparam]
            sectionLabel = QLabel(Dialog)
            sectionLabel.setText(pname)
            gridLayout.addWidget(sectionLabel, row, 0, 1, 1)
            if ptype == int:
                valuebox = QSpinBox(Dialog)
                if "range" in pparam:
                    valuebox.setRange(*pparam["range"])
                else:
                    valuebox.setMinimum(-9999999999)
                    valuebox.setMaximum(9999999999)
                valuebox.setValue(pdefvalue)
                gridLayout.addWidget(valuebox, row, 1, 1, 1)
                Dialog.resultgetter.append(valuebox.value)
            elif ptype == float:
                valuebox = QDoubleSpinBox(Dialog)
                if "decimals" in pparam:
                    valuebox.setDecimals(pparam["decimals"])
                else:
                    valuebox.setDecimals(5)
                valuebox.setMinimum(-9999999999)
                valuebox.setMaximum(9999999999)
                valuebox.setValue(pdefvalue)
                gridLayout.addWidget(valuebox, row, 1, 1, 1)
                Dialog.resultgetter.append(valuebox.value)
            elif ptype == bool:
                valuebox = QCheckBox(Dialog)
                valuebox.setValue(pdefvalue)
                gridLayout.addWidget(valuebox, row, 1, 1, 1)
                Dialog.resultgetter.append(valuebox.isChecked)
            elif ptype == str:
                valuebox = QTextEdit(Dialog)
                gridLayout.addWidget(valuebox, row, 1, 1, 1)
                valuebox.setPlainText(pdefvalue)
                Dialog.resultgetter.append(valuebox.toPlainText)
            elif ptype == QuantisedFunction:
                from openalea.plantgl.gui.curve2deditor import (
                    Curve2DEditor,
                    FuncConstraint,
                )

                valuebox = Curve2DEditor(Dialog)
                valuebox.pointsConstraints = FuncConstraint()
                if pdefvalue:
                    valuebox.setCurve(pdefvalue)
                row += 1
                gridLayout.addWidget(valuebox, row, 0, 1, 2)
                Dialog.resultgetter.append(valuebox.getCurve)
            row += 1
            nbparam += 1

        buttonBox = QDialogButtonBox(Dialog)
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttonBox.accepted.connect(Dialog.accept)
        buttonBox.rejected.connect(Dialog.reject)
        gridLayout.addWidget(buttonBox, row, 1, 1, 1)

        return Dialog

    # ---------------------------- MTG edition ----------------------------------------

    def removeSubtree(self):
        assert self.selection is not None
        self.createBackup("mtg")
        nid = self.selection.id
        self.showMessage("Remove subtree rooted in " + str(nid) + ". Repaint.")
        self.mtg.remove_tree(nid)
        self.updateMTGView()
        self.updateViewGL()

    def removeSelection(self):
        assert self.selection is not None
        self.createBackup("mtg")
        nid = self.selection.id
        self.showMessage("Remove " + str(nid) + ".")
        parent = self.mtg.parent(nid)
        for son in self.mtg.children(nid):
            self.mtg.replace_parent(son, parent)
        self.mtg.remove_vertex(nid)

        del self.ctrlPoints[nid]
        del self.ctrlPointsRep[self.ctrlPointsRepIndex[nid]]
        self.ctrlPointsRepIndex = dict(
            [(sh.id, i) for i, sh in enumerate(self.ctrlPointsRep)]
        )

        del self.mtgrep[self.mtgrepindex[nid]]
        self.mtgrepindex = dict([(sh.id, i) for i, sh in enumerate(self.mtgrep)])

        self.selection = None
        self.focus = None
        self.__update_value__(parent)
        self.updateViewGL()

    def newChild(self):
        assert self.selection is not None
        self.createBackup("mtg")
        nid = self.selection.id
        self.showMessage("Add child to " + str(nid) + ".")
        positions = self.mtg.property(self.propertyposition)
        if self.mtg.parent(nid):
            l = positions[nid] - positions[self.mtg.parent(nid)]
            norml = norm(l)
        else:
            l = Vector3.OZ
            norml = 1.0
        nbchild = len(list(self.mtg.children(nid)))
        if nbchild == 0:
            npos = positions[nid] + l
            npos, nbg = self.stickPosToPoints(npos)
        elif nbchild >= 1:
            ipos = positions[nid]
            dirl = direction(l)
            dirView = toV3(self.camera().viewDirection())
            nbcandidates = 10
            candidates = [
                ipos
                + Matrix3.axisRotation(dirView, ang * 2 * math.pi / nbcandidates) * l
                for ang in range(nbcandidates)
            ]
            ocandidates = candidates
            candidates = [self.stickPosToPoints(c)[0] for c in candidates]
            siblings = list(self.mtg.siblings(nid)) + list(self.mtg.children(nid))
            if self.mtg.parent(nid):
                siblings += [self.mtg.parent(nid)]
            siblingpos = [
                ipos + norml * direction(positions[sib] - ipos) for sib in siblings
            ]
            # point set at a given distance criteria
            factor1 = [abs(norm(c - ipos) - norml) for c in candidates]
            # distance to other nodes criteria
            factor2 = [sum([norm(pos - c) for pos in siblingpos]) for c in candidates]
            max1, max2 = max(factor1), max(factor2)
            cmplist = [
                (i, (factor1[i] / max1) + 2 * (1 - (factor2[i] / max2)))
                for i in range(nbcandidates)
            ]
            # self.setTempInfoDisplay(Scene([Shape(PointSet(ocandidates,width = self.pointWidth+2),Material((255,0,255))),
            # Shape(PointSet(candidates,width = self.pointWidth+2),Material((255,255,0))),
            # Shape(PointSet(siblingpos,width = self.pointWidth+8),Material((255,255,255))),
            # Shape(Group([Translated(ocandidates[i],Text(str(int(100*cmplist[i][1])))) for i in xrange(len(candidates))]),Material((255,255,0)))
            # ]))
            cmplist.sort(key=lambda x: x[1])
            npos = candidates[cmplist[0][0]]

        if self.mtg.is_leaf(nid):
            cid = self.mtg.add_child(
                nid, position=npos, edge_type="<", label=self.nodelabel
            )
        else:
            cid = self.mtg.add_child(
                nid, position=npos, edge_type="+", label=self.nodelabel
            )

        ctrlPoint = createCtrlPoint(
            self.mtg,
            cid,
            self.ctrlPointColor,
            self.propertyposition,
            self.__update_value__,
        )
        self.ctrlPoints[cid] = ctrlPoint
        self.ctrlPointsRep += ctrlPoint.representation(self.ctrlPointPrimitive)
        self.ctrlPointsRepIndex[cid] = len(self.ctrlPointsRep) - 1
        self.mtgrep += createEdgeRepresentation(
            nid, cid, positions, self.edgePlusMaterial
        )
        self.mtgrepindex[cid] = len(self.mtgrep) - 1
        self.setSelection(ctrlPoint)
        if (
            self.points is None
            and len(self.mtg.vertices(scale=self.mtg.max_scale())) < 100
        ):
            self.refreshView()
        self.updateViewGL()

    def splitEdge(self):
        assert self.selection is not None
        self.createBackup("mtg")
        nid = self.selection.id
        self.showMessage("Split edge before " + str(nid) + ".")
        positions = self.mtg.property(self.propertyposition)
        cposition = positions[nid]
        pposition = positions[self.mtg.parent(nid)]
        newposition = (cposition + pposition) / 2
        edge_type = self.mtg.edge_type(nid)
        cid = self.mtg.insert_parent(
            nid, edge_type=edge_type, position=newposition, label=self.nodelabel
        )
        self.mtg.property("edge_type")[nid] = "<"
        ctrlPoint = createCtrlPoint(
            self.mtg,
            cid,
            self.ctrlPointColor,
            self.propertyposition,
            self.__update_value__,
        )
        self.ctrlPoints[cid] = ctrlPoint
        self.ctrlPointsRep += ctrlPoint.representation(self.ctrlPointPrimitive)
        self.ctrlPointsRepIndex[cid] = len(self.ctrlPointsRep) - 1
        self.mtgrep += createEdgeRepresentation(
            nid, cid, positions, self.edgePlusMaterial
        )
        self.mtgrepindex[cid] = len(self.mtgrep) - 1
        self.__update_value__(cid)
        self.setSelection(ctrlPoint)
        self.updateViewGL()

    def beginReparentSelection(self):
        self.setSelectionTrigger(self.endReparentSelection)
        self.setMode(self.Selection)
        self.showMessage("Select Parent")
        self.displayMessage("Select Parent", 5000)

    def endReparentSelection(self, node):
        self.createBackup("mtg")
        nid = self.selection.id
        if node.id in mtgalgo.descendants(self.mtg, nid):
            QMessageBox.warning(
                self,
                "Invalid parent",
                "Cannot reparent a node with one of its descendants",
            )
            return
        nsons = list(self.mtg.children(node.id))
        ndirectsons = [son for son in nsons if self.mtg.edge_type(son) == "<"]

        self.mtg.replace_parent(nid, node.id)
        if len(ndirectsons) > 0:
            self.mtg.property("edge_type")[nid] = "+"
        else:
            self.mtg.property("edge_type")[nid] = "<"
        self.mtg.property("label")[nid] = self.nodelabel
        self.showMessage("Parent selected : " + str(node.id) + ".")
        self.__update_value__(nid)
        self.updateViewGL()
        # self.updateMTGView()

    def setBranchingPoint(self):
        assert self.selection is not None
        self.createBackup("mtg")
        nid = self.selection.id
        self.mtg.property("edge_type")[nid] = "+"
        self.mtg.property("label")[nid] = self.nodelabel
        self.__update_value__(nid)
        self.updateViewGL()

    def setAxialPoint(self):
        assert self.selection is not None
        self.createBackup("mtg")
        nid = self.selection.id
        edge_type = self.mtg.property("edge_type")
        edge_type[nid] = "<"
        self.mtg.property("label")[nid] = self.nodelabel
        siblings = self.mtg.siblings(nid)
        self.__update_value__(nid)
        for sib in siblings:
            if edge_type[sib] == "<":
                edge_type[sib] = "+"
                self.mtg.property("label")[sib] = self.nodelabel
                self.__update_value__(sib)

        self.updateViewGL()

    def stickPosToPoints(self, initpos):
        if not self.pointsRep:
            return initpos, ()
        if not self.pointsKDTree or len(self.pointsKDTree) != len(
            self.pointsRep[0].geometry.pointList
        ):
            self.pointsKDTree = ANNKDTree3(self.pointsRep[0].geometry.pointList)

        nbg = self.pointsKDTree.k_closest_points(initpos, 5)
        newposition = centroid_of_group(self.pointsRep[0].geometry.pointList, nbg)
        return newposition, nbg

    def stickNodeToPoints(self, nid):
        initpos = self.mtg.property(self.propertyposition)[nid]
        newposition, nbg = self.stickPosToPoints(initpos)
        self.ctrlPoints[nid].setPosition(toVec(newposition))
        self.__update_value__(nid)
        return nbg

    def stickToPoints(self, withupdate=True):
        assert self.selection is not None
        if not self.points:
            return
        nid = self.selection.id

        self.createBackup("mtg")
        nbg = self.stickNodeToPoints(nid)
        self.setTempInfoDisplay(
            Scene(
                [
                    Shape(
                        PointSet(
                            self.pointsRep[0].geometry.pointList.subset(nbg),
                            width=self.pointinfo.pointWidth + 2,
                        ),
                        Material((255, 0, 255)),
                    )
                ]
            )
        )
        self.showMessage("Stick " + str(nid) + " to points.")
        self.updateViewGL()

    def stickSubtree(self):
        assert self.selection is not None
        if not self.points:
            return
        nid = self.selection.id

        self.createBackup("mtg")
        self.stickNodeToPoints(nid)
        nbg = []
        for ci in mtgalgo.descendants(self.mtg, nid):
            nbg += self.stickNodeToPoints(ci)
        self.setTempInfoDisplay(
            Scene(
                [
                    Shape(
                        PointSet(
                            self.pointsRep[0].geometry.pointList.subset(nbg),
                            width=self.pointinfo.pointWidth + 2,
                        ),
                        Material((255, 0, 255)),
                    )
                ]
            )
        )
        self.showMessage("Stick subtree of " + str(nid) + " to points.")
        self.updateViewGL()

    def smoothPosition(self):
        from .mtgmanip import gaussian_filter

        self.createBackup("mtg")
        self.showMessage("Applied gaussian filter to positions.")
        gaussian_filter(self.mtg, self.propertyposition)
        self.__update_all_mtg__()
        self.updateViewGL()

    def revolveAroundSelection(self):
        self.camera().setRevolveAroundPoint(toVec(self.selection.position()))
        self.showMessage("Revolve around " + str(self.selection.id))

    def revolveAroundScene(self):
        self.camera().setRevolveAroundPoint(self.sceneCenter())
        self.showMessage("Revolve around scene center")

    def showMessage(self, message, timeout=0):
        if self.statusBar:
            self.statusBar.showMessage(message, timeout)
        else:
            self.displayMessage(message, timeout)
        print(message)

    # ---------------------------- Point edition ----------------------------------------

    def reorient(self):
        if not self.check_input_points():
            return

        self.points.pointList.swapCoordinates(1, 2)
        if (
            self.pointsRep[0].geometry.pointList.getPglId()
            != self.points.pointList.getPglId()
        ):
            self.pointsRep[0].geometry.pointList.swapCoordinates(1, 2)
        self.updateViewGL()

    def sortZ(self):
        if not self.check_input_points():
            return
        self.createBackup("points")
        self.points.pointList.sortZ()
        self.setPoints(PointSet(self.points.pointList))
        self.updateViewGL()

    def estimateKDensity(self):
        if not self.check_input_points():
            return

        kclosests = self.estimateKClosest()
        densities = densities_from_k_neighborhood(
            self.points.pointList, kclosests, self.k
        )
        self.pointinfo.densities = densities

        return densities

    def estimateKClosest(self):
        if not self.check_input_points():
            return

        if hasattr(self.pointinfo, "kclosests"):
            kclosests = self.pointinfo.kclosests
        else:
            kclosests = k_closest_points_from_ann(self.points.pointList, self.k, True)
            kclosests = connect_all_connex_components(
                self.points.pointList, kclosests, True
            )
            self.pointinfo.kclosests = kclosests
        return kclosests

    def estimateRNeigbor(self, radius, multithreaded=True):
        if not self.check_input_points():
            return

        if not hasattr(self.pointinfo, "rnbg") or radius not in self.pointinfo.rnbg:
            kclosests = self.estimateKClosest()
            r_neighborhoods_func = (
                r_neighborhoods_mt if multithreaded else r_neighborhoods
            )
            rnbgs = r_neighborhoods_func(self.points.pointList, kclosests, radius, True)
            if not hasattr(self.pointinfo, "rnbg"):
                self.pointinfo.rnbg = dict()
            self.pointinfo.rnbg[radius] = rnbgs
        else:
            rnbgs = self.pointinfo.rnbg[radius]
        return rnbgs

    def estimateDirections(self, neigbors=None):
        directions = pointsets_orientations(self.points.pointList, neigbors)
        self.pointinfo.directions = directions
        return directions

    def estimateNormals(self, neigbors=None):
        if neigbors is None:
            neigbors = self.estimateKClosest()
        normals = pointsets_normals(self.points.pointList, neigbors)
        source = 0
        normals = pgl.pointsets_orient_normals(normals, source, neigbors)
        self.pointinfo.normals = normals
        return normals

    def get_colormap(self):
        try:
            from matplotlib.cm import get_cmap

            p = get_cmap("jet")
            ncmap = [p(i) for i in range(p.N)]
            print("Use matplotlib")
            return [
                Color4(int(round(255 * r)), int(round(255 * g)), int(round(255 * b)), 0)
                for r, g, b, a in ncmap
            ]
        except Exception as e:
            print(e)
            print("use qt colormap")

            def makeColor4(h):
                q = QColor()
                q.setHsv(h, 255, 255)
                return Color4(q.red(), q.green(), q.blue(), 0)

            minhue, maxhue = 255, 0
            stephue = -1
            return [makeColor4(minhue + i * stephue) for i in range(256)]

    def pointDensityDisplay(self, densities):
        cmap = self.get_colormap()
        self.points.colorList = apply_colormap(cmap, densities)

        self.createPointsRepresentation()
        self.updateViewGL()

    def pointKDensity(self):
        if not self.check_input_points():
            return
        k, ok = QInputDialog.getInt(
            self, "K Neighborhood", "Select a k for neighborhood", self.k, 0, 100
        )
        if ok:
            self.k = k
            from time import time

            t = time()
            densities = self.estimateKDensity()
            t = time() - t
            self.pointDensityDisplay(densities)
            self.showMessage(
                "Density range for K="
                + str(self.k)
                + " : "
                + str((min(densities), max(densities)))
                + ". Computed in {}".format(t)
            )

    def pointRDensityMT(self, display=True):
        if not self.check_input_points():
            return
        mini, maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(
            self,
            "Density Radius",
            "Select a radius of density (Pointset height : %f)" % zdist,
            zdist / 100.0,
            0,
            decimals=3,
        )
        if ok:
            from time import time

            t = time()
            rnbgs = self.estimateRNeigbor(radius, True)
            densities = densities_from_r_neighborhood(rnbgs, radius)
            t = time() - t
            self.pointinfo.densities = densities
            if display:
                self.pointDensityDisplay(densities)
                self.showMessage(
                    "Density range for R="
                    + str(radius)
                    + " : "
                    + str(densities.getMinAndMax(True))
                    + ". Computed in {}".format(t)
                )

    def pointClusters(self):
        if not self.check_input_data():
            return

        points = self.points.pointList
        nodes = list(self.mtg.property(self.propertyposition).values())
        from numpy.random import shuffle

        shuffle(nodes)
        clusterid = points_clusters(points, nodes)
        self.pointDensityDisplay(clusterid)
        self.showMessage("Show point clusters")

    def densityHistogram(self):
        if not self.check_input_points():
            return
        try:
            import matplotlib.pyplot as plt
        except ImportError as e:
            QMessageBox.critical(
                self, "MatPlotLib", "MatPlotLib not available !\n" + str(e)
            )
            return
        if not hasattr(self.pointinfo, "densities"):
            if not self.pointRDensityMT():
                return
        densities = self.pointinfo.densities
        n, bins, patches = plt.hist(densities)
        cmap = self.get_colormap()
        nbcolor = len(cmap)
        itcol = nbcolor / (len(bins))
        for i, p in enumerate(patches):
            col = cmap[int(itcol * (i + 0.5))]
            col = (
                col.red / 255.0,
                col.green / 255.0,
                col.blue / 255.0,
                1 - col.alpha / 255.0,
            )
            p.set_facecolor(col)
        plt.show()

    def pointDirections(self):
        if not pglalgoExists("pointsets_orientations"):
            QMessageBox.warning(
                self, "Directions", "Directions computation algorithm is not available."
            )
            return
        if not self.check_input_points():
            return
        mini, maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(
            self,
            "Direction Radius",
            "Select a radius to estimate point direction (Pointset height : %f)"
            % zdist,
            zdist / 100.0,
            0,
            decimals=3,
        )
        if ok:
            rnbgs = self.estimateRNeigbor(radius)
            directions = self.estimateDirections(rnbgs)
            dl = zdist / 200
            s = Scene(
                [
                    Shape(
                        Group(
                            [
                                Polyline([p + d * dl, p - d * dl])
                                for p, d in zip(self.points.pointList, directions)
                            ]
                        ),
                        Material(self.theme["Direction"], 1),
                    )
                ]
            )
            self.setPointAttribute(s)
            self.updateViewGL()
            return True
        else:
            return False

    def pointNormals(self):
        if not pglalgoExists("pointsets_normals"):
            QMessageBox.warning(
                self, "Normals", "Normals computation algorithm is not available."
            )
            return
        kclosests = self.estimateKClosest()
        directions = self.estimateNormals(kclosests)
        mini, maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z
        dl = zdist / 200
        s = Scene(
            [
                Shape(
                    Group(
                        [
                            Polyline([p + d * dl, p - d * dl])
                            for p, d in zip(self.points.pointList, directions)
                        ]
                    ),
                    Material(self.theme["Direction"], 1),
                )
            ]
        )
        self.setPointAttribute(s)
        self.updateViewGL()

    def filterPointsMin(self):
        if not self.check_input_points():
            return
        if not hasattr(self.pointinfo, "densities"):
            self.pointKDensity()
        densityratio, ok = QInputDialog.getInt(
            self,
            "Density Ratio",
            "Select the minimum density (percentage ratio) to select points to remove",
            5,
            1,
            100,
        )
        if ok:
            self.createBackup("points")
            subset = filter_min_densities(self.pointinfo.densities, densityratio)
            self.setPoints(
                PointSet(
                    self.points.pointList.opposite_subset(subset),
                    self.points.colorList.opposite_subset(subset),
                )
            )
            self.updateViewGL()
            self.showMessage(
                "Applied density filtering. Nb of points : "
                + str(len(self.points.pointList))
                + "."
            )

    def filterPointsMax(self):
        if not self.check_input_points():
            return
        if not hasattr(self.pointinfo, "densities"):
            self.pointKDensity()
        densityratio, ok = QInputDialog.getInt(
            self,
            "Density Ratio",
            "Select a maximum density (percentage ratio) to select points to remove",
            5,
            1,
            100,
        )

        if ok:
            self.createBackup("points")
            subset = filter_max_densities(self.pointinfo.densities, densityratio)
            self.setPoints(
                PointSet(
                    self.points.pointList.opposite_subset(subset),
                    self.points.colorList.opposite_subset(subset),
                )
            )
            self.updateViewGL()
            self.showMessage(
                "Applied density filtering. Nb of points : "
                + str(len(self.points.pointList))
                + "."
            )

    def subSampling(self):
        if not self.check_input_points():
            return
        nbPoints = len(self.points.pointList)
        ratio = 50 if nbPoints < 2000000 else 2000000.0 / nbPoints
        pointsStr = "{:,}".format(nbPoints).replace(",", " ")
        pointratio, ok = QInputDialog.getInt(
            self,
            "Point Ratio",
            "Select a percentage ratio of points to keep.\nCurrent number of points: "
            + pointsStr
            + ".",
            ratio,
            1,
            100,
        )
        if ok:
            from random import sample

            subset = sample(range(nbPoints), int(nbPoints * pointratio / 100))
            self.createBackup("points")
            self.setPoints(
                PointSet(
                    self.points.pointList.subset(subset),
                    self.points.colorList.subset(subset),
                )
            )
            self.updateViewGL()
            self.showMessage(
                "Sub-sampling applied. Number of points: "
                + str(len(self.points.pointList))
                + "."
            )

    def displaySelectedPoint(self, position):
        """
        Display the selected point at the given position.
        :param position: The position of the selected point.
        :return: None
        """
        material = Material((0, 255, 0))
        scene = Scene([Shape(PointSet([position], width=10), material)])
        self.pointsAttributeRep = scene
        self.updateViewGL()

    def getNearestSelectedPoint(self, selection):
        """
        Get the nearest selected point from the camera.
        :param selection: The list of selected points.
        :return: Vector3
        """
        selection.sort(key=lambda x: x[0])
        nearestPoint = selection[0]
        index = nearestPoint[2][1]
        return self.points.pointList[index]

    def euclidianContraction(self):
        if not self.check_input_points():
            return
        mini, maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(
            self,
            "Contraction Radius",
            "Select a radius of contraction (Pointset height : %f)" % zdist,
            zdist / 100.0,
            0,
            decimals=3,
        )
        if ok:
            self.createBackup("points")
            from time import time

            t = time()
            self.points.pointList = contract_point3(self.points.pointList, radius)
            t = time() - t
            self.setPoints(self.points, True)
            self.updateViewGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

    def riemannianContraction(self):
        if not self.check_input_points():
            return
        mini, maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(
            self,
            "Contraction Radius",
            "Select a radius of contraction (Pointset height : %f)" % zdist,
            zdist / 100.0,
            0,
            decimals=3,
        )
        if ok:
            self.createBackup("points")
            from time import time

            t = time()
            rnbgs = self.estimateRNeigbor(radius)
            self.points.pointList = centroids_of_groups(self.points.pointList, rnbgs)
            t = time() - t
            self.setPoints(self.points, True)
            self.updateViewGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

    def laplacianContraction(self):
        if not self.check_input_points():
            return
        self.createBackup("points")
        points = self.points.pointList
        from time import time

        t = time()
        kclosests = self.estimateKClosest()
        self.points.pointList = centroids_of_groups(points, kclosests)
        t = time() - t
        self.setPoints(self.points)
        self.updateViewGL()
        self.showMessage("Applied contraction in {} sec.".format(t))

    def adaptiveRadialContraction(self):
        if not self.check_input_points():
            return
        if not hasattr(self.pointinfo, "densities"):
            self.pointRDensityMT()
        if not hasattr(self.pointinfo, "directions"):
            if not self.pointDirections():
                return

        kclosests = self.estimateKClosest()
        points = self.points.pointList

        from numpy import mean

        mini, maxi = points.getZMinAndMaxIndex()
        zdist = points[maxi].z - points[mini].z
        mdistance = mean(pointset_mean_distances(points, points, kclosests))

        Rfunc = NurbsCurve2D([(0, 0, 1), (0.3, 0.3, 1), (0.7, 0.7, 1), (1, 1, 1)])
        dialog = self.createParamDialog(
            "Parameterizing the Adaptive Radial Contraction",
            [
                ("Section Width", float, mdistance),
                ("Minimum Contraction Radius", float, zdist / 200),
                ("Maximum Contraction Radius", float, zdist / 50),
                ("Density - Radius Relationship", QuantisedFunction, Rfunc),
            ],
        )

        if dialog.exec_():
            param = dialog.getParams()
            sectionwidth, minradius, maxradius, radiusfunc = param
            self.createBackup("points")
            points = self.points.pointList
            kclosests = self.estimateKClosest()
            from math import pi
            from time import time

            t = time()
            orientations = self.pointinfo.directions
            densities = self.pointinfo.densities
            densityradiusmap = QuantisedFunction(radiusfunc.__deepcopy__({}))
            radii = pgl.adaptive_radii(
                densities, minradius * pi, maxradius * pi, densityradiusmap
            )
            cpoints2, radii2 = adaptive_section_circles(
                points, kclosests, orientations, sectionwidth, radii
            )

            self.points.pointList = cpoints2
            t = time() - t
            self.setPoints(self.points, True)
            self.updateViewGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

    def pathBasedContraction(self):
        if not self.check_input_mtg("Require a root position."):
            return
        livnycontractionnb, ok = QInputDialog.getInt(
            self,
            "Number of Contraction Steps",
            "Select a number of contraction step",
            self.getparamcache("livnycontractionnb", 3),
            0,
            50,
        )
        if ok:
            self.setparamcache("livnycontractionnb", livnycontractionnb)
            self.createBackup("points")
            points = self.points.pointList
            if self.mtg:
                startfrom = self.mtg.component_roots_at_scale(
                    self.mtg.root, self.mtg.max_scale()
                )[0]
                rootpos = Vector3(self.mtg.property("position")[startfrom])
                root = len(points)
                points.append(rootpos)
            else:
                root = 0
            from time import time

            from .livnymethod import livny_contraction

            t = time()
            newPointList = points
            for i in range(livnycontractionnb):
                newPointList, parents, weights = livny_contraction(newPointList, root)
            if self.mtg:
                del newPointList[root]
            self.points.pointList = newPointList
            t = time() - t
            self.setPoints(self.points, True)
            self.updateViewGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

    def rosaContraction(self):
        if not hasattr(self.pointinfo, "directions"):
            if not self.pointDirections():
                return

        import numpy as np

        kclosests = self.estimateKClosest()
        points = self.points.pointList
        mdistance = np.mean(pointset_mean_distances(points, points, kclosests))

        dialog = self.createParamDialog(
            "Parameterizing the Rosa Contraction. (Pointset neigborhood mean distance : %f)"
            % mdistance,
            [
                ("Section Width", float, mdistance),
                ("Number of Steps", int, 3, {"range": (0, 50)}),
            ],
        )

        if dialog.exec_():
            param = dialog.getParams()
            sectionwidth, rosastepnb = param

            self.createBackup("points")
            from time import time

            t = time()
            normals = self.estimateNormals()
            directions = self.pointinfo.directions
            sections = points_sections(points, kclosests, directions, radius)
            for i in range(rosastepnb):
                directions = sections_normals(normals, sections)
                sections = points_sections(points, kclosests, directions, radius)

            newPointList = centroids_of_groups(points, sections)
            self.points.pointList = newPointList
            t = time() - t
            self.setPoints(self.points, True)
            self.pointinfo.directions = directions
            self.updateViewGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

    # ---------------------------- Align ----------------------------------------

    def convexHullOfSelection(self):
        if not self.check_input_data():
            return

        assert self.selection is not None
        nid = self.selection.id
        print("Add hull of nid")

        points = self.points.pointList
        nodes = list(self.mtg.property(self.propertyposition).values())
        node2nid = dict(
            [
                (node, i)
                for i, node in enumerate(
                    self.mtg.property(self.propertyposition).keys()
                )
            ]
        )
        clusters = cluster_points(points, nodes)

        from openalea.mtg.traversal import post_order2

        pointids = sum(
            [clusters[node2nid[n]] for n in post_order2(self.mtg, nid)], Index([])
        )

        shape = Fit(points.subset(pointids)).convexHull()
        self.mtg.property("hull")[nid] = shape
        self.mtg.property("volume")[nid] = volume(shape)

        sh = Shape(shape, self.hullMaterial, nid)

        if self.modelRep is not None:
            self.modelRep += sh
        else:
            self.modelRep = Scene([sh])

        self.modelDisplay = True
        self.updateViewGL()

    def removeHullOfSelection(self):
        if not self.check_input_data():
            return

        assert self.selection is not None
        nid = self.selection.id
        print("Remove hull of nid")

        try:
            del self.mtg.property("hull")[nid]
        except:
            pass

        self.modelRep = Scene([sh for sh in self.modelRep if sh.id != nid])
        self.updateViewGL()

    # ---------------------------- Align ----------------------------------------

    def applyAlignement(self, funcname, *params):
        if not self.check_input_data():
            return

        print("apply", funcname)

        self.createBackup("mtg")

        if type(funcname) == str:
            from . import alignement

            func = alignement.__dict__[funcname]

        if len(params):
            func(self.points.pointList, self.mtg, *params)
        else:
            func(self.points.pointList, self.mtg)

        self.__update_all_mtg__()
        self.updateViewGL()

    def alignGlobally(self):
        self.applyAlignement("alignGlobally")

    def alignOptimizeAll(self):
        self.applyAlignement("optimizeAlignementAll")

    def alignOptimizeOrientation(self):
        self.applyAlignement("optimizeAlignementOrientation")

    def alignOptimizePosition(self):
        mtgextent = Point3Array(
            list(self.mtg.property(self.propertyposition).values())
        ).getExtent()
        distanceratio, ok = QInputDialog.getInt(
            self,
            "Distance Ratio",
            "Select a percentage ratio of distance to optimize (size={})".format(
                str(list(mtgextent))
            ),
            10,
            1,
            100,
        )
        if ok:
            self.applyAlignement("optimizeAlignementPosition", distanceratio)

    def alignScaleAndCenter(self):
        self.applyAlignement("scale_and_center")

    # ---------------------------- Radius Reconstruction ----------------------------------------

    def determine_radius(self, pid, strategy="mean"):
        if not self.check_input_data():
            return

        mtg = self.mtg

        nbgs = list(mtg.children(pid))
        if mtg.parent(pid):
            nbgs.append(mtg.parent(pid))

        pos = mtg.property(self.propertyposition)
        spos = pos[pid]

        meandist = sum([norm(pos[nbg] - spos) for nbg in nbgs]) / len(nbgs)

        selection = points_at_distance_from_skeleton(
            self.points.pointList, [spos], [0], meandist * 0.75, 1
        )
        if selection:
            if mtg.parent(pid):
                dir = spos - pos[nbgs[-1]]
            else:
                apicalchild = [
                    vid for vid in mtg.children(pid) if mtg.edge_type(vid) == "<"
                ]
                if len(apicalchild) > 0:
                    dir = direction(
                        Point3Array(
                            [pos[vid] - spos for vid in apicalchild]
                        ).getCenter()
                    )
                elif len(mtg.children(pid)) > 0:
                    dir = direction(
                        Point3Array(
                            [pos[vid] - spos for vid in mtg.children(pid)]
                        ).getCenter()
                    )
                else:
                    dir = (0, 0, 1)

            if strategy == "mean":
                radius = pointset_mean_radial_distance(
                    spos, dir, self.points.pointList, selection
                )
                return radius
            elif strategy == "max":
                radius = pointset_max_radial_distance(
                    spos, dir, self.points.pointList, selection
                )
                return radius
            elif strategy == "convexhull":
                from numpy import dot
                from openalea.plantgl.all import Fit

                # Get subsample selection of points
                points_subset = self.points.pointList.subset(selection)
                # Define a 2D plane, with a normal dir defined above
                # Apply a projection of points on this plance
                dir = dir.normed()
                i = direction(dir.anOrthogonalVector())
                j = dir ^ i
                points_subset_projected = Point2Array(
                    [(dot(i, p - spos), dot(j, p - spos)) for p in points_subset]
                )
                # Compute the convexhull on this plance
                contour = Fit.convexPolyline(points_subset_projected)
                # Compute the circle and radius from this convexhull
                x_c, y_c, radius = self.computeCircle(contour)
                # Reproject the new center onto the 3D space
                c = spos + x_c * i + y_c * j
                return c, radius
            else:
                print("unknown radius reconstruction strategy")
            print("radius[", pid, "]:", radius)

    def computeCircle(self, contour):
        def getXMinXMaxYMinYMax(contour):
            points = [(p[0], p[1]) for p in contour]
            xmin = min(points, key=lambda p: p[0])[0]
            xmax = max(points, key=lambda p: p[0])[0]
            ymin = min(points, key=lambda p: p[1])[1]
            ymax = max(points, key=lambda p: p[1])[1]
            return xmin, xmax, ymin, ymax

        perimeter = contour.getLength()
        xmin, xmax, ymin, ymax = getXMinXMaxYMinYMax(contour)
        x_c, y_c = [(xmin + xmax) / 2.0, (ymin + ymax) / 2.0]
        r = perimeter / (2 * pi)
        return x_c, y_c, r

    ##    def computeCircle(self, contour):
    ##        area = contour.surface()
    ##        x_c, y_c = [(contour.xmin() + contour.xmax()) / 2., (contour.ymin() + contour.ymax()) / 2.]
    ##        r = (area / pi)**0.5
    ##        return x_c, y_c, r

    def increaseSelectionRadius(self):
        assert self.selection is not None
        sid = self.selection.id

        currentRadius = self.mtg.property(self.propertyradius)[sid]
        self.mtg.property(self.propertyradius)[sid] = currentRadius * 1.05

        self.__update_radius__(sid)
        self.updateViewGL()

    def decreaseSelectionRadius(self):
        assert self.selection is not None
        sid = self.selection.id

        currentRadius = self.mtg.property(self.propertyradius)[sid]
        self.mtg.property(self.propertyradius)[sid] = currentRadius * 0.95

        self.__update_radius__(sid)
        self.updateViewGL()

    def setSelectionRadius(self):
        assert self.selection is not None
        sid = self.selection.id

        currentRadius = self.mtg.property(self.propertyradius)[sid]
        dialog = self.createParamDialog(
            "Set Radius", [("Radius", float, currentRadius)]
        )
        if dialog.exec_():
            currentRadius = dialog.getParams()[0]
            self.mtg.property(self.propertyradius)[sid] = currentRadius

        self.__update_radius__(sid)
        self.updateViewGL()

    def estimateMeanRadius(self):
        assert self.selection is not None
        sid = self.selection.id

        self.mtg.property(self.propertyradius)[sid] = self.determine_radius(sid, "mean")

        self.__update_radius__(sid)
        self.updateViewGL()

    def estimateMaxRadius(self):
        assert self.selection is not None
        sid = self.selection.id

        self.mtg.property(self.propertyradius)[sid] = self.determine_radius(sid, "max")

        self.__update_radius__(sid)
        self.updateViewGL()

    def estimateConvexHullRadius(self):
        assert self.selection is not None
        sid = self.selection.id

        (
            self.mtg.property(self.propertyposition)[sid],
            self.mtg.property(self.propertyradius)[sid],
        ) = self.determine_radius(sid, "convexhull")

        self.__update_radius__(sid)
        self.updateViewGL()

    def estimateAllRadius(self, maxmethod=True, overwrite=True):
        if not self.check_input_data():
            return

        from .mtgmanip import mtg2pgltree

        nodes, parents, vertex2node = mtg2pgltree(self.mtg)

        estimatedradii = estimate_radii_from_points(
            self.points.pointList, nodes, parents, maxmethod=maxmethod
        )

        radii = self.mtg.property(self.propertyradius)
        for vid, nid in list(vertex2node.items()):
            if vid not in radii or overwrite:
                radii[vid] = estimatedradii[nid]

        self.radiusRep, self.radiusRepIndex = createRadiiRepresentation(
            self.mtg,
            self.radiusMaterial,
            positionproperty=self.propertyposition,
            radiusproperty=self.propertyradius,
        )
        self.updateViewGL()

    def smoothRadius(self):
        from .mtgmanip import gaussian_filter

        self.createBackup("mtg")
        self.showMessage("Applied gaussian filter to radius.")
        gaussian_filter(self.mtg, self.propertyradius, False)
        self.__update_all_mtg__()
        self.updateViewGL()

    def thresholdRadius(self):
        from .mtgmanip import threshold_filter

        self.createBackup("mtg")
        self.showMessage("Applied threshold filter to radius.")
        threshold_filter(self.mtg, self.propertyradius)
        self.__update_all_mtg__()
        self.updateViewGL()

    def pipeModel(self, startfrom=None):
        from .mtgmanip import get_first_param_value, pipemodel

        self.check_input_mtg()
        if startfrom is False:
            startfrom = None

        if startfrom in self.mtg.property(self.propertyradius):
            defrootradius = self.mtg.property(self.propertyradius)[startfrom]
        else:
            defrootradius = get_first_param_value(self.mtg, self.propertyradius)
        if defrootradius is None:
            defrootradius = 1
        defleaveradius = defrootradius / 100.0

        dialog = self.createParamDialog(
            "Parameterizing the Pipe Model",
            [
                ("Root Radius", float, defrootradius),
                ("Leaves Radius", float, defleaveradius),
            ],
        )
        if dialog.exec_():
            params = dialog.getParams()
            rootradius, leaveradius = params
            estimatedradii = pipemodel(self.mtg, rootradius, leaveradius, startfrom)
            self.mtg.property(self.propertyradius).update(estimatedradii)

            self.radiusRep, self.radiusRepIndex = createRadiiRepresentation(
                self.mtg,
                self.radiusMaterial,
                positionproperty=self.propertyposition,
                radiusproperty=self.propertyradius,
            )
            self.updateViewGL()

    def pipeModelOnSelection(self):
        assert self.selection is not None
        sid = self.selection.id
        self.pipeModel(sid)

    def pipeModelAverageDistance(self):
        pipeexponent, ok = QInputDialog.getDouble(
            self,
            "Pipe Exponent",
            "Select a pipe exponent",
            self.getparamcache("pipeexponent", 2.0),
            0.5,
            4,
            2,
        )
        if ok:
            self.setparamcache("pipeexponent", pipeexponent)
            from .mtgmanip import mtg2pgltree

            nodes, parents, vertex2node = mtg2pgltree(self.mtg)
            avgradius = average_radius(self.points.pointList, nodes, parents)
            print("average distance to points :", avgradius)
            weights = carried_length(nodes, parents)
            weights += 1
            print("compute radii")
            estimatedradii = estimate_radii_from_pipemodel(
                nodes, parents, weights.log(), avgradius, pipeexponent
            )

            radii = self.mtg.property(self.propertyradius)
            for vid, nid in list(vertex2node.items()):
                radii[vid] = estimatedradii[nid]
            print(estimatedradii[0])

            self.radiusRep, self.radiusRepIndex = createRadiiRepresentation(
                self.mtg,
                self.radiusMaterial,
                positionproperty=self.propertyposition,
                radiusproperty=self.propertyradius,
            )
            self.updateViewGL()

    # ---------------------------- Check MTG ----------------------------------------

    def checkMTG(self):
        error_vtx = []
        for vtx in self.mtg.vertices(scale=self.mtg.max_scale()):
            if (
                len([i for i in self.mtg.children(vtx) if self.mtg.edge_type(i) == "<"])
                > 1
            ):
                error_vtx.append(vtx)

        if len(error_vtx) != 0:
            QMessageBox.warning(
                self, "Multiple direct sons of nodes of the MTG :" + str(error_vtx)
            )

        s = []
        for ctrlPoint in self.ctrlPoints.values():
            shape = ctrlPoint.representation(self.ctrlPointPrimitive)
            if shape.id in error_vtx:
                shape.appearance.ambient = (255, 0, 0)  # blue
            s.append(shape)

        self.ctrlPointsRep = Scene(s)

    # ---------------------------- Root ----------------------------------------

    def addBottomRoot(self):
        if self.points is None:
            root = Vector3(0, 0, 0)
        else:
            root = Vector3(self.points.pointList[self.points.pointList.getZMinIndex()])
        self.addRoot(root)

    def addBottomCenterRoot(self):
        if self.points is None:
            root = Vector3(0, 0, 0)
        else:
            points = self.points.pointList
            pmin, pmax = points.getBounds()
            initp = (pmax + pmin) / 2
            initp.z = pmin.z
            root = points.findClosest(initp)[0]
        self.addRoot(root)

    def addTopRoot(self):
        if self.points is None:
            root = Vector3(0, 0, 0)
        else:
            root = Vector3(self.points.pointList[self.points.pointList.getZMaxIndex()])
        self.addRoot(root)

    def addRoot(self, position):
        from . import mtgmanip as mm

        self.setMTG(mm.initialize_mtg(position), None)
        self.showEntireScene()

    # ---------------------------- Reconstruction ----------------------------------------

    def getStartFrom(self, startfrom):
        if type(startfrom) != int:
            if self.selection is not None:
                startfrom = self.selection.id
                points = None
                return startfrom, points
            else:
                if self.mtg is None:
                    QMessageBox.warning(self, "Root", "Create a root node")
                    return None, None
                vtx = list(self.mtg.vertices(self.mtg.max_scale()))
                if len(vtx) > 1:
                    QMessageBox.warning(self, "Root", "Select a node")
                    return None, None
                elif len(vtx) == 0:
                    QMessageBox.warning(self, "Root", "Add a root node")
                    return None, None
                else:
                    startfrom = vtx[0]
                points = self.points.pointList
                return startfrom, points
        else:
            return None, None

    def xuReconstruction(self, startfrom=None):
        print("Xu Reconstruction")

        startfrom, points = self.getStartFrom(startfrom)
        if startfrom is None:
            return

        binratio, ok = QInputDialog.getInt(
            self,
            "Bin Ratio",
            "Select a bin ratio",
            self.getparamcache("binratio", 50),
            10,
            1000,
        )

        if ok:
            self.setparamcache("binratio", binratio)
            self.createBackup("mtg")
            self.showMessage(
                "Apply Xu et al. reconstruction from  node " + str(startfrom) + "."
            )
            mini, maxi = self.points.pointList.getZMinAndMaxIndex()
            zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z
            binlength = zdist / binratio
            if points is None:
                print(
                    "filter",
                    len(self.points.pointList),
                    "points with distance",
                    binlength,
                )
                points, emptycolor = self.filter_points(
                    PointSet(self.points.pointList), binlength
                )  # ,[startfrom])
                if len(points) < 10:
                    self.showMessage(
                        "Not enough points ("
                        + str(len(points))
                        + ") to apply reconstruction from "
                        + str(startfrom)
                        + "."
                    )
                    return
            from .xumethod import xu_method

            xu_method(self.mtg, startfrom, points, binlength)
            self.updateMTGView()
            self.updateViewGL()

    def graphColonization(self, startfrom=None):
        if not self.check_input_points():
            return
        if not hasattr(self.pointinfo, "densities"):
            self.pointRDensityMT()

        print("Graph Colonization Reconstruction")
        startfrom, points = self.getStartFrom(startfrom)
        if startfrom is None:
            return

        points = self.points.pointList
        mini, maxi = points.getZMinAndMaxIndex()
        zdist = points[maxi].z - points[mini].z

        Rfunc = NurbsCurve2D([(0, 0, 1), (0.3, 0.3, 1), (0.7, 0.7, 1), (1, 1, 1)])
        dialog = self.createParamDialog(
            "Parameterizing the Space Colonization Algorithm",
            [
                ("Minimum Bin Length", float, zdist / 200, {"decimals": 5}),
                ("Maximum Bin Length", float, zdist / 50, {"decimals": 5}),
                (
                    "Density - Bin Length Relationship",
                    QuantisedFunction,
                    Rfunc,
                    {"decimals": 5},
                ),
            ],
        )
        if dialog.exec_():
            param = dialog.getParams()
            minlength, maxlength, radiusfunc = param
            self.createBackup("mtg")
            self.showMessage(
                "Apply Adaptive Graph Colonization et al. reconstruction from  node "
                + str(startfrom)
                + "."
            )
            if points is None:
                print(
                    "filter",
                    len(self.points.pointList),
                    "points with distance",
                    maxlength,
                )
                points, emptycolor = self.filter_points(
                    PointSet(self.points.pointList), maxlength
                )  # ,[startfrom])
                if len(points) < 10:
                    self.showMessage(
                        "Not enough points ("
                        + str(len(points))
                        + ") to apply reconstruction from "
                        + str(startfrom)
                        + "."
                    )
                    return
            from .xumethod import graphcolonization_method

            densities = self.pointinfo.densities
            graphcolonization_method(
                self.mtg,
                startfrom,
                points,
                densities,
                minlength,
                maxlength,
                QuantisedFunction(radiusfunc.__deepcopy__({})),
            )
            self.updateMTGView()
            self.updateViewGL()

    def scaReconstruction(self, startfrom=None):
        if not self.check_input_points():
            return

        print("Space Colonization Reconstruction")
        startfrom, points = self.getStartFrom(startfrom)
        if startfrom is None:
            return

        mini, maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z

        dialog = self.createParamDialog(
            "Parameterizing the Space Colonization Algorithm",
            [
                ("Growth Length", float, zdist / 50, {"decimals": 5}),
                ("Kill Distance Ratio", float, 0.9, {"decimals": 5}),
                ("Perception Distance Ratio", float, 2.5, {"decimals": 5}),
                ("Minimum number of attractors", int, 5, {"range": (0, 100)}),
            ],
        )
        if dialog.exec_():
            param = dialog.getParams()
            growthlength, killratio, perceptionratio, min_nb_pt_per_bud = param
            self.createBackup("mtg")
            self.showMessage(
                "Apply Space Colonization reconstruction from node "
                + str(startfrom)
                + "."
            )
            if points is None:
                print(
                    "filter",
                    len(self.points.pointList),
                    "points with distance",
                    growthlength,
                )
                points, emptycolor = self.filter_points(
                    PointSet(self.points.pointList), growthlength
                )  # ,[startfrom])
                if len(points) < 10:
                    self.showMessage(
                        "Not enough points ("
                        + str(len(points))
                        + ") to apply reconstruction from "
                        + str(startfrom)
                        + "."
                    )
                    return
            from .sca import spacecolonization_method

            spacecolonization_method(
                self.mtg,
                startfrom,
                points,
                growthlength,
                killratio,
                perceptionratio,
                min_nb_pt_per_bud,
            )
            self.updateMTGView()
            self.updateViewGL()

    def adaptivescaReconstruction(self, startfrom=None):
        if not self.check_input_points():
            return
        if not hasattr(self.pointinfo, "densities"):
            self.pointRDensityMT()

        print("Adaptive Space Colonization Reconstruction")
        startfrom, points = self.getStartFrom(startfrom)
        if startfrom is None:
            return

        mini, maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z - self.points.pointList[mini].z

        Rfunc = NurbsCurve2D([(0, 0, 1), (0.3, 0.3, 1), (0.7, 0.7, 1), (1, 1, 1)])
        dialog = self.createParamDialog(
            "Parameterizing the Space Colonization Algorithm",
            [
                ("Maximum Growth Length", float, zdist / 50, {"decimals": 5}),
                ("Minimum Growth Length", float, zdist / 100, {"decimals": 5}),
                (
                    "Density - Growth Length Relationship",
                    QuantisedFunction,
                    Rfunc,
                    {"decimals": 5},
                ),
                ("Kill Distance Ratio", float, 0.9, {"decimals": 5}),
                ("Perception Distance Ratio", float, 2.5, {"decimals": 5}),
                ("Minimum number of attractors", int, 5, {"range": (0, 100)}),
            ],
        )
        if dialog.exec_():
            param = dialog.getParams()
            (
                maxlength,
                minlength,
                radiusfunc,
                killratio,
                perceptionratio,
                min_nb_pt_per_bud,
            ) = param
            self.createBackup("mtg")
            self.showMessage(
                "Apply Adaptive Space Colonizatio reconstruction from node "
                + str(startfrom)
                + "."
            )
            if points is None:
                print(
                    "filter",
                    len(self.points.pointList),
                    "points with distance",
                    maxlength,
                )
                points, emptycolor = self.filter_points(
                    PointSet(self.points.pointList), maxlength
                )  # ,[startfrom])
                if len(points) < 10:
                    self.showMessage(
                        "Not enough points ("
                        + str(len(points))
                        + ") to apply reconstruction from "
                        + str(startfrom)
                        + "."
                    )
                    return
            from .sca import adaptivespacecolonization_method

            densities = self.pointinfo.densities

            adaptivespacecolonization_method(
                self.mtg,
                startfrom,
                points,
                densities,
                minlength,
                maxlength,
                QuantisedFunction(radiusfunc.__deepcopy__({})),
                killratio,
                perceptionratio,
                min_nb_pt_per_bud,
            )
            self.updateMTGView()
            self.updateViewGL()

    def livnyReconstruction(self, startfrom=None):
        print("Livny Reconstruction")

        startfrom, points = self.getStartFrom(startfrom)
        if startfrom is None:
            return

        dialog = self.createParamDialog(
            "Parameterizing Livny Algorithm",
            [
                ("Number of Contraction Steps", int, 3, {"range": (0, 50)}),
                ("Number of Filtering Steps", int, 5, {"range": (0, 50)}),
                ("Ratio for min edge size filter", int, 15, {"range": (0, 100)}),
            ],
        )

        if dialog.exec_():
            param = dialog.getParams()
            livnycontractionnb, livnyfilteringnb, livnyminedgeratio = param

            self.createBackup("mtg")
            self.showMessage(
                "Apply Livny et al. reconstruction from  node " + str(startfrom) + "."
            )
            verbose = False
            if points is None:
                print(
                    "filter",
                    len(self.points.pointList),
                    "points with distance",
                    binlength,
                )
                points, emptycolor = self.filter_points(
                    PointSet(self.points.pointList), binlength
                )  # ,[startfrom])
                verbose = False
                if len(points) < 10:
                    self.showMessage(
                        "Not enough points ("
                        + str(len(points))
                        + ") to apply reconstruction from "
                        + str(startfrom)
                        + "."
                    )
                    return
            from .livnymethod import livny_method_mtg

            livny_method_mtg(
                self.mtg,
                startfrom,
                points,
                livnycontractionnb,
                livnyfilteringnb,
                livnyminedgeratio / 100.0,
            )
            self.updateMTGView()
            self.updateViewGL()

    # ---------------------------- Tagging ----------------------------------------

    def angleEstimate(self):
        from .angleanalysis import (
            lines_estimation,
            lines_representation,
            phylo_angles,
            write_phylo_angles,
        )

        tdegree, ok = QInputDialog.getInt(
            self,
            "Degree of trunk line",
            "Select a degree for the trunk line estimation",
            1,
            1,
            5,
        )
        if ok:
            trunk_line, lateral_lines, nodelength = lines_estimation(self.mtg, tdegree)
            print(type(trunk_line), trunk_line)
            if hasattr(trunk_line, "isValid") and not trunk_line.isValid():
                QMessageBox.error(
                    self, "Invalid approximation", "Invalid approximation"
                )
                return
            self.setTempInfoDisplay(lines_representation(trunk_line, lateral_lines))
            self.updateViewGL()
            phyangles = phylo_angles(trunk_line, lateral_lines)
            self.setTempInfoDisplay(
                lines_representation(trunk_line, lateral_lines, phyangles)
            )
            self.updateViewGL()
            fname = QFileDialog.getSaveFileName(
                self, "Save Angles", "angles.txt", "Txt Files (*.txt);;All Files (*.*)"
            )
            fname = str(fname[0])
            if len(fname) == 0:
                return
            write_phylo_angles(str(fname[0]), phyangles, nodelength)

    # ---------------------------- Tagging ----------------------------------------

    def tagColor(self, tag):
        if tag == True:
            return self.theme["TaggedCtrlPoint"]
        elif tag == False:
            return self.theme["UnTaggedCtrlPoint"]
        else:
            assert tag < 0
            return self.theme["UpscaleCtrlPoint"][-1 - tag]

    def tagScaleToNode(self):
        assert self.selection is not None
        sid = self.selection.id
        tagprop = self.mtg.property(self.currenttagname)
        tagvalue = tagprop.get(sid, False)
        if tagvalue in [True, False]:
            tagvalue = not tagvalue
            tagprop[sid] = tagvalue
            self.selection.color = self.tagColor(tagvalue)
            self.setSelection(None)
            self.__update_value__(sid)
            self.showMessage("Tag " + str(sid))

    def tagScale(self):
        if self.mode != self.TagScale:
            self.setMode(self.TagScale)
            self.tagScaleRepresentation()
            self.tagUpdateVisu()
            self.showMessage("Tag Scale Mode.")
        else:
            self.endTagRepresentation()
            self.setMode(self.Rotate)
        self.updateViewGL()

    def tagScaleRepresentation(self):
        tagprop = self.mtg.property(self.currenttagname)
        if len(tagprop) == 0:
            mscale = self.mtg.max_scale()
            for scale in range(1, mscale):
                for uvid in self.mtg.vertices(scale):
                    for vid in self.mtg.component_roots_at_scale(uvid, mscale):
                        if vid not in tagprop:
                            tagprop[vid] = -(mscale - scale)
        for cid, cpoint in list(self.ctrlPoints.items()):
            tag = tagprop.get(cid, False)
            cpoint.color = self.tagColor(tag)

    def tagUpdateVisu(self):
        self.createCtrlPointRepresentation()
        self.prevVisu = self.pointDisplay
        self.pointDisplay = False

    def endTagRepresentation(self):
        self.pointDisplay = self.prevVisu
        for cid, cpoint in list(self.ctrlPoints.items()):
            cpoint.color = self.ctrlPointColor
        self.createCtrlPointRepresentation()

    def commitScale(self):
        if not len(self.mtg.property(self.currenttagname)):
            QMessageBox.warning(self, "Data error", "No tagged node to create scale.")

        if self.mode != self.TagScale:
            QMessageBox.warning(self, "Data error", "Select Tag Scale Mode first.")

        default_label, ok = QInputDialog.getText(
            self, "Scale Label", "Select a label for nodes at the new scale"
        )
        default_label = str(default_label)
        if not ok:
            return
        self.createBackup("mtg")

        self.mtg.insert_scale(
            self.mtg.max_scale(),
            lambda vid: self.mtg.property(self.currenttagname).get(vid, False) != False,
            default_label=default_label,
        )
        self.mtg.property(self.currenttagname).clear()
        self.showMessage(
            "New scale " + str(self.mtg.max_scale() - 1) + " commited in the MTG."
        )
        self.tagScaleRepresentation()
        self.createCtrlPointRepresentation()
        self.updateViewGL()

    def createProperty(self, vid=None):
        from . import propwidget_ui

        main = self

        class PDialog(QDialog):
            def __init__(self, parent):
                QDialog.__init__(self, parent)
                self.main = parent
                self.widget = propwidget_ui.Ui_Dialog()
                self.widget.setupUi(self)
                self.init(self.widget)

            def init(self, widget):
                widget.actionAdd.clicked.connect(self.add_item)
                widget.actionMinus.clicked.connect(self.remove_item)
                widget.buttonBox.accepted.connect(self.commit)

            def add_item(self, propname="prop", value="value", model=None):
                if model is None:
                    model = self.models[self.widget.tabWidget.currentIndex()]
                model.appendRow(
                    [
                        QStandardItem(propname),
                        QStandardItem(repr(value) if value else ""),
                    ]
                )

            def remove_item(self):
                ci = self.widget.tabWidget.currentIndex()
                mi = self.tableViews[ci].selectedIndexes()
                if mi:
                    r = mi[0].row()
                    print(r)
                    self.models[ci].removeRows(r, 1)

            def set_properties(self, mtg, vid, model=None):
                for propname, propval in list(mtg.properties().items()):
                    if propval is not None:
                        self.add_item(propname, propval.get(vid), model)

                for propname, propval in list(mtg.properties().items()):
                    if propval is None:
                        self.add_item(propname, propval.get(vid), model)

            def retrieve_properties(self):
                props = dict()
                for vid, model in zip(self.vids, self.models):
                    vidprops = dict()
                    for i in range(model.rowCount()):
                        propname = model.item(i, 0).text()
                        valuerepr = model.item(i, 1).text()
                        print(propname, valuerepr)
                        if len(valuerepr) > 0:
                            try:
                                value = eval(valuerepr)
                                vidprops[propname] = value
                            except Exception as e:
                                QMessageBox.warning(
                                    self,
                                    "Data error",
                                    "Error with vertex "
                                    + str(vid)
                                    + " for "
                                    + propname
                                    + "="
                                    + repr(valuerepr)
                                    + "\n"
                                    + str(e),
                                )
                                raise ValueError(e)
                        else:
                            vidprops[propname] = None
                    props[vid] = vidprops
                return props

            def apply_properties(self):
                mtg = self.main.mtg
                try:
                    props = self.retrieve_properties()
                    print(props)
                    main.createBackup("mtg")
                    for vid, vidprop in list(props.items()):
                        print(vid, vidprop)
                        for pname, pvalue in list(vidprop.items()):
                            if pvalue is None:
                                if vid in mtg.property(pname):
                                    del mtg.property(pname)[vid]
                            else:
                                mtg.property(pname)[vid] = pvalue
                        if mtg.scale(vid) == mtg.max_scale():
                            self.main.__update_value__(vid)
                    return True
                except ValueError:
                    return False

            def create_tab_for_vertex(self, mtg, vid):
                newwidget = QWidget()
                gridLayout = QGridLayout(newwidget)
                newtableview = QTableView(self)
                gridLayout.addWidget(newtableview, 1, 0, 1, 5)
                newtableview.setEditTriggers(QAbstractItemView.AllEditTriggers)
                newtableview.setSortingEnabled(False)

                newmodel = QStandardItemModel(0, 1)
                newmodel.setHorizontalHeaderLabels(["Parameter", "Value"])
                newtableview.setModel(newmodel)

                self.tableViews.append(newtableview)
                self.models.append(newmodel)
                self.vids.append(vid)

                self.set_properties(mtg, vid, newmodel)
                self.widget.tabWidget.addTab(
                    newwidget, str(mtg.scale(vid)) + " : " + str(vid)
                )

            def edit(self, vid):
                self.widget.tabWidget.clear()
                self.tableViews = []
                self.models = []
                self.vids = []

                while vid is not None and vid != self.main.mtg.root:
                    self.create_tab_for_vertex(self.main.mtg, vid)
                    vid = self.main.mtg.complex(vid)

            def commit(self):
                self.widget.tableView.clearSelection()

                if hasattr(self, "vids"):
                    if not self.apply_properties():
                        return

                self.accept()

        if self.propertyeditor is None:
            dialog = PDialog(self)
            self.propertyeditor = dialog

        if vid is not None:
            self.propertyeditor.edit(vid)
        self.propertyeditor.show()

    def editProperty(self):
        assert self.selection is not None
        self.createProperty(self.selection.id)

    def startTagProperty(self):
        if self.mode != self.TagProperty:
            self.createProperty()
            self.propertyeditor.accepted.connect(self.launchTagProperty)
        else:
            self.endTagRepresentation()
            self.setMode(self.Rotate)
        self.updateViewGL()

    def launchTagProperty(self):
        self.setMode(self.TagProperty)
        self.propertiestotag = self.propertyeditor.retrieve_properties()
        self.tagPropertyRepresentation()
        self.tagUpdateVisu()
        self.showMessage("Tag Properties Mode.")

    def tagPropertyRepresentation(self):
        proptarget = self.propertyeditor.retrieve_properties()
        props = [self.mtg.property(propname) for propname in list(proptarget.keys())]
        mscale = self.mtg.max_scale()
        for cid, cpoint in list(self.ctrlPoints.items()):
            tag = True
            for pvalues in props:
                if cid not in pvalues:
                    tag = False
                    break
            cpoint.color = self.tagColor(tag)

    def tagPropertyToNode(self):
        assert self.selection is not None
        sid = self.selection.id
        self.propertyeditor.apply_properties(sid)
        self.selection.color = self.tagColor(True)
        self.setSelection(None)
        self.__update_value__(sid)
        self.showMessage("Tag " + str(sid))


# ---------------------------- End Property ----------------------------------------
