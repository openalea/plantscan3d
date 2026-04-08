try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print("Py2ExeRelease")
except ImportError:
    py2exe_release = False
    print("StdRelease")

import os
from os.path import join

from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.qt.QtWidgets import *

ldir = os.path.dirname(__file__)

if not py2exe_release:
    from . import ui_compiler as cui

    cui.check_ui_generation(join(ldir, "main_window.ui"))
    cui.check_rc_generation(join(ldir, "plantscan3d.qrc"))

from . import main_window_ui
from .__version__ import version as psc_version
from .database import db_connection, dbeditor
from .module_loader import ModuleLoader
from .segmenteditor import SegmentEditor
from .settings import Settings
from .shareddata import *


class MainWindow(QMainWindow, main_window_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        """
        @param parent : parent window
        """
        QMainWindow.__init__(self, parent)
        main_window_ui.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        # if not os.path.exists(get_shared_data("mtg")):
        #    self.menuLoad.setEnabled(False)
        self.pointSizeSlider.setValue(self.mtgeditor.pointinfo.pointWidth)
        self.nodeSizeSlider.setValue(self.mtgeditor.nodeWidth)
        self.actionOpenMTG.triggered.connect(self.mtgeditor.openMTG)
        self.actionImportMTG.triggered.connect(self.mtgeditor.importMTG)
        self.actionSaveMTG.triggered.connect(self.mtgeditor.saveMTG)
        self.actionSave.triggered.connect(self.mtgeditor.save)
        self.actionSaveSnapshot.triggered.connect(self.mtgeditor.saveSnapshot)
        self.actionImportPoints.triggered.connect(self.mtgeditor.importPoints)
        self.actionExportPoints.triggered.connect(self.mtgeditor.exportPoints)
        self.actionExportGeom.triggered.connect(self.mtgeditor.exportAsGeom)
        self.actionExportNodeList.triggered.connect(self.mtgeditor.exportNodeList)
        self.actionAboutPsc3d.triggered.connect(self.about)
        self.actionDocumentation.triggered.connect(self.documentation)
        self.actionExit.triggered.connect(self.close)
        self.actionSetBackgroundImg.triggered.connect(self.setBackgroundImg)
        self.actionClearBackgroundImg.triggered.connect(self.clearBackgroundImg)
        self.actionImportCustomGeometry.triggered.connect(self.importCustomGeometry)
        self.actionClearCustomGeometry.triggered.connect(
            self.mtgeditor.clearCustomGeometry
        )

        self.db_connection = db_connection.DatabaseConnection(self)
        self.actionConnect_to_Database.triggered.connect(self.db_connection.show)
        self.db_connection.accepted.connect(self.db_connection_validated)

        if not py2exe_release:
            self.actionPuu1.triggered.connect(self.mtgeditor.puu1)
            self.actionPuu3.triggered.connect(self.mtgeditor.puu3)
            self.actionCherry.triggered.connect(self.mtgeditor.cherry)
            self.actionArabido.triggered.connect(self.mtgeditor.arabido)
            self.actionAppleTree.triggered.connect(self.mtgeditor.appletree)
        else:
            self.menuFile.removeAction(self.menuLoad.menuAction())

        self.actionUndo.triggered.connect(self.mtgeditor.undo)
        self.actionRedo.triggered.connect(self.mtgeditor.redo)
        self.mtgeditor.undoAvailable.connect(self.actionUndo.setEnabled)
        self.mtgeditor.redoAvailable.connect(self.actionRedo.setEnabled)
        self.actionRevolveAroundScene.triggered.connect(
            self.mtgeditor.revolveAroundScene
        )
        self.actionShowAll.triggered.connect(self.mtgeditor.showEntireScene)
        self.actionRecalculate_Colors.triggered.connect(
            self.mtgeditor.RecalculateColors
        )

        from .main_viewer import ThemeDict

        self.menuTheme.clear()

        def gen_updatetheme(theme):
            def updateTheme():
                print("Update theme", theme["Name"])
                self.mtgeditor.updateTheme(theme)

            return updateTheme

        for name, theme in ThemeDict.items():
            ai = QAction(name, self.menuTheme)
            self.menuTheme.addAction(ai)
            ai.triggered.connect(gen_updatetheme(theme))
        # self.actionWhiteTheme.triggered.connect(lambda: self.mtgeditor.updateTheme(WhiteTheme))
        # self.actionBlackTheme.triggered.connect(lambda: self.mtgeditor.updateTheme(BlackTheme))

        self.actionReorient.triggered.connect(self.mtgeditor.reorient)
        self.actionSortZ.triggered.connect(self.mtgeditor.sortZ)
        self.actionAlignGlobal.triggered.connect(self.mtgeditor.alignGlobally)
        self.actionAlignOptimizeAll.triggered.connect(self.mtgeditor.alignOptimizeAll)
        self.actionAlignOptimizeOrientation.triggered.connect(
            self.mtgeditor.alignOptimizeOrientation
        )
        self.actionAlignOptimizePosition.triggered.connect(
            self.mtgeditor.alignOptimizePosition
        )
        self.actionScaleAndCenter.triggered.connect(self.mtgeditor.alignScaleAndCenter)
        self.actionFilterMinDensity.triggered.connect(self.mtgeditor.filterPointsMin)
        self.actionFilterMaxDensity.triggered.connect(self.mtgeditor.filterPointsMax)
        self.actionKDensity.triggered.connect(self.mtgeditor.pointKDensity)
        self.actionRDensity.triggered.connect(self.mtgeditor.pointRDensityMT)
        self.actionDensityHistogram.triggered.connect(self.mtgeditor.densityHistogram)

        self.actionSubSampling.triggered.connect(self.mtgeditor.subSampling)

        self.actionDelete_Selection.triggered.connect(self.mtgeditor.deleteSelection)
        self.actionKeep_Selection.triggered.connect(self.mtgeditor.keepSelection)
        self.actionDeselect.triggered.connect(self.mtgeditor.deselectPoints)
        self.actionSoil.triggered.connect(self.mtgeditor.soilSelection.select)
        self.actionWire.triggered.connect(self.mtgeditor.wireSelection.start)
        self.actionPole.triggered.connect(self.mtgeditor.poleSelection.start)
        self.segment_editor = SegmentEditor(parent=self)
        self.actionSegment.triggered.connect(self.segment_points)
        # self.mtgeditor.nextSegmentedTreeAvailable.connect(self.actionNext_Segmented_Tree.setEnabled)
        # self.actionNext_Segmented_Tree.triggered.connect(self.mtgeditor.nextSegmentedTree)

        self.actionEuclidianContraction.triggered.connect(
            self.mtgeditor.euclidianContraction
        )
        self.actionLaplacianContraction.triggered.connect(
            self.mtgeditor.laplacianContraction
        )
        self.actionRiemannianContraction.triggered.connect(
            self.mtgeditor.riemannianContraction
        )
        self.actionAdaptiveRadialContraction.triggered.connect(
            self.mtgeditor.adaptiveRadialContraction
        )
        self.actionPathBasedContraction.triggered.connect(
            self.mtgeditor.pathBasedContraction
        )
        self.actionROSAContraction.triggered.connect(self.mtgeditor.rosaContraction)

        self.actionPointDirections.triggered.connect(self.mtgeditor.pointDirections)
        self.actionPointNormals.triggered.connect(self.mtgeditor.pointNormals)
        self.actionPointClusters.triggered.connect(self.mtgeditor.pointClusters)

        self.actionViewPoints.setChecked(self.mtgeditor.isPointDisplayEnabled())
        self.actionViewPointAttributes.setChecked(
            self.mtgeditor.isPointAttributeDisplayEnabled()
        )
        self.actionViewMTG.setChecked(self.mtgeditor.isMTGDisplayEnabled())
        self.actionViewControlPoints.setChecked(
            self.mtgeditor.isControlPointsDisplayEnabled()
        )
        self.actionViewRadius.setChecked(self.mtgeditor.isRadiusDisplayEnabled())
        self.actionView3DModel.setChecked(self.mtgeditor.is3DModelDisplayEnabled())

        self.mtgeditor.PointAttributeDisplay.connect(
            self.actionViewPointAttributes.setChecked
        )

        self.actionViewPoints.triggered.connect(self.mtgeditor.enablePointDisplay)
        self.actionViewPointAttributes.triggered.connect(
            self.mtgeditor.enablePointAttributeDisplay
        )
        self.actionViewMTG.triggered.connect(self.mtgeditor.enableMTGDisplay)
        self.actionViewControlPoints.triggered.connect(
            self.mtgeditor.enableControlPointsDisplay
        )
        self.actionViewRadius.triggered.connect(self.mtgeditor.enableRadiusDisplay)
        self.actionView3DModel.triggered.connect(self.mtgeditor.enable3DModelDisplay)
        self.actionRefreshView.triggered.connect(self.mtgeditor.refreshView)
        self.actionAdjustView.triggered.connect(self.mtgeditor.adjustView)

        self.actionComputeMaxRadius.triggered.connect(
            lambda: self.mtgeditor.estimateAllRadius(maxmethod=True)
        )
        self.actionComputeMeanRadius.triggered.connect(
            lambda: self.mtgeditor.estimateAllRadius(maxmethod=False)
        )
        self.actionComputeMeanRadius.triggered.connect(
            lambda: self.mtgeditor.estimateAllRadius(maxmethod=False)
        )
        self.actionSmoothRadius.triggered.connect(self.mtgeditor.smoothRadius)
        self.actionThresholdRadius.triggered.connect(self.mtgeditor.thresholdRadius)
        self.actionPipeModel.triggered.connect(self.mtgeditor.pipeModel)
        self.actionPipeModelAverageDistance.triggered.connect(
            self.mtgeditor.pipeModelAverageDistance
        )

        # self.actionAverageRadius.triggered.connect(self.mtgeditor.averageNodesRadius) # TODO
        # self.actionFilterRadius.triggered.connect(self.mtgeditor.filterNodesRadius) # TODO

        self.actionCheckMTG.triggered.connect(self.mtgeditor.checkMTG)
        self.actionSmoothPosition.triggered.connect(self.mtgeditor.smoothPosition)

        self.actionRootBottom.triggered.connect(self.mtgeditor.addBottomRoot)
        self.actionRootBottomCenter.triggered.connect(
            self.mtgeditor.addBottomCenterRoot
        )
        self.actionRootTop.triggered.connect(self.mtgeditor.addTopRoot)

        self.actionXuReconstruction.triggered.connect(self.mtgeditor.xuReconstruction)
        self.actionLivnyReconstruction.triggered.connect(
            self.mtgeditor.livnyReconstruction
        )
        self.actionAdaptiveScaReconstruction.triggered.connect(
            self.mtgeditor.adaptivescaReconstruction
        )
        self.actionScaReconstruction.triggered.connect(self.mtgeditor.scaReconstruction)
        self.actionGraphColonization.triggered.connect(self.mtgeditor.graphColonization)

        self.actionAngleEstimation.triggered.connect(self.mtgeditor.angleEstimate)
        self.actionEditScale.triggered.connect(self.mtgeditor.tagScale)
        self.actionCommitScale.triggered.connect(self.mtgeditor.commitScale)
        self.actionTagProperty.triggered.connect(self.mtgeditor.startTagProperty)
        self.action3DRepresentation.triggered.connect(self.mtgeditor.show3DModel)

        self.visibilityEnabled.clicked.connect(self.mtgeditor.enabledClippingPlane)
        self.backVisibilitySlider.valueFloatChanged.connect(
            self.mtgeditor.setBackVisibility
        )
        self.frontVisibilitySlider.valueFloatChanged.connect(
            self.mtgeditor.setFrontVisibility
        )
        self.pointSizeSlider.valueChanged.connect(self.mtgeditor.setPointWidth)
        self.nodeSizeSlider.valueChanged.connect(self.mtgeditor.setNodeWidth)
        self.pointFilterSlider.valueFloatChanged.connect(self.mtgeditor.setPointFilter)

        self.mtgeditor.actionEditScale = self.actionEditScale
        self.mtgeditor.actionTagProperty = self.actionTagProperty
        self.actionEditScale.setCheckable(True)
        self.actionTagProperty.setCheckable(True)

        self.mtgeditor.mainwindow = self
        self.mtgeditor.filehistory.setMenu(self.menuRecents)

        self.mtgeditor.statusBar = QStatusBar(self)
        self.setStatusBar(self.mtgeditor.statusBar)

        self.openDBObject = None

        self.pointSizeSlider.setup("Point Size", 1, 10, 2)
        self.pointFilterSlider.setup("Point Filter", 0, 1, 0, 3)
        self.nodeSizeSlider.setup("Node Size", 1, 10, 1)
        self.frontVisibilitySlider.setup("Near", 0.01, 1, 0.01, 2)
        self.backVisibilitySlider.setup("Far", 0, 0.99, 0.99, 2)

        self.resizeDocks([self.dockDisplay, self.dockRender], [240, 240], Qt.Horizontal)

        try:
            self.restoreWindowState()
        except:
            pass

        self.moduleLoader = ModuleLoader(join(ldir, "modules.conf"))

    def setBackgroundImg(self):
        # name, selection = QFileDialog.getOpenFileName(self, "Select an image", ".", "Images (*.png *.xpm *.jpg)");

        # In case of Cancel
        # if not name :  return
        name = "/Users/fboudon/Desktop/oakleaf.png"

        self.mtgeditor.loadBackgroundImg(name)
        self.mtgeditor.updateViewGL()
        return

    def clearBackgroundImg(self):
        self.mtgeditor.clearBackgroundImg()

    def importCustomGeometry(self):
        name, selection = QFileDialog.getOpenFileName(
            self,
            "Select an 3D shape",
            ".",
            "PGL file (*.bgeom *.geom *.obj);All files (*.*)",
        )
        if not name:
            return
        self.mtgeditor.setCustomGeometry(name)
        self.mtgeditor.updateViewGL()

    def about(self):
        if not hasattr(self, "splash"):
            pix = QImage("images/icon.png").convertToFormat(QImage.Format_RGB32)
            self.splash = QSplashScreen(QPixmap(pix))
        else:
            splash = self.splash
        aboutTxt = (
            """<b>PlantScan3D</b><br>
<it>An open-source editor for reconstructing 3D plant architecture from laser scans</it>.<br><br>Version :"""
            + psc_version
            + """<br>
Licence: CeCILL-C<br><br><br>
Implemented by F. Boudon et al. <br>Copyright: CIRAD-INRIA-INRA.<br>
<br><br><br><br><br>"""
        )
        self.splash.showMessage(aboutTxt, Qt.AlignBottom | Qt.AlignLeft)
        self.splash.show()

    def documentation(self):
        import webbrowser

        webbrowser.open("https://plantscan3d.readthedocs.io/")

    def restoreWindowState(self):
        """
        Restore the previous previous window state (position and size).
        :return: None
        """
        settings = Settings()
        settings.beginGroup("Window")

        self.restoreGeometry(settings.value("Geometry"))
        self.restoreState(settings.value("State"))

        settings.endGroup()

    def loadModules(self):
        """
        Load all modules.
        :return: None
        """
        self.moduleLoader.load()

    def closeEvent(self, event):
        """
        Close event.
        :param event:
        :return: None
        """
        settings = Settings()

        # Window State
        settings.beginGroup("Window")
        settings.setValue("Geometry", self.saveGeometry())
        settings.setValue("State", self.saveState())
        settings.endGroup()

        from .database.server_manip import server_info

        server_info.save_register_ids()

        self.mtgeditor.closeEvent(event)

    def segment_points(self):
        self.segment_editor.gleditor.setSegmentPoints(self.mtgeditor.points.pointList)
        self.segment_editor.show()

    def test_connection_callback(self, status):
        if status:

            def delete_request(id):
                if self.openDBObject == id:
                    self.openDBObject = None

                    msgBox = QMessageBox()
                    msgBox.setText(
                        "The current opened scan has been deleted from the database, do you want to clean the viewer ?"
                    )
                    msgBox.setStandardButtons(QMessageBox.Apply | QMessageBox.Cancel)
                    msgBox.setDefaultButton(QMessageBox.Cancel)

                    if msgBox.exec_() == QMessageBox.Apply:
                        from openalea.plantgl.all import (
                            Color4Array,
                            Point3Array,
                            PointSet,
                        )

                        self.mtgeditor.setPoints(PointSet(Point3Array(), Color4Array()))

            def open_request(id, file_path):
                from zipfile import ZIP_DEFLATED, ZipFile

                if not os.path.exists(file_path):
                    return

                path, fname = os.path.split(str(file_path))

                zip = ZipFile(file_path, mode="r", compression=ZIP_DEFLATED)
                zip.extractall(path)

                if "point_cloud.ply" in zip.namelist():
                    self.mtgeditor.readPoints(str(path + "/point_cloud.ply"))
                if "skeleton.bmtg" in zip.namelist():
                    self.mtgeditor.readMTG(str(path + "/skeleton.bmtg"))

                self.openDBObject = id
                zip.close()

            def save_request(file_path):
                from zipfile import ZIP_DEFLATED, ZipFile

                path, fname = os.path.split(str(file_path))
                try:
                    os.makedirs(path)
                except:
                    pass

                zip = ZipFile(file_path, mode="w", compression=ZIP_DEFLATED)

                if (
                    self.mtgeditor.points is not None
                    and len(self.mtgeditor.points.pointList) > 0
                ):
                    self.mtgeditor.savePoints(
                        path + "/point_cloud.ply", self.mtgeditor.points
                    )
                    zip.write(path + "/point_cloud.ply", "point_cloud.ply")
                if self.mtgeditor.mtg is not None:
                    self.mtgeditor.writeMTG(path + "/skeleton.bmtg")
                    zip.write(path + "/skeleton.bmtg", "skeleton.bmtg")
                zip.close()

            def set_object_request(id):
                self.openDBObject = id

            def size_callback():
                return len(self.mtgeditor.points.pointList)

            def make_thumbnail():
                from openalea.plantgl.all import Scene

                from .thumbnailmaker import make_thumbnail

                return make_thumbnail(Scene([self.mtgeditor.points]), (256, 256))

            def reset_open_object():
                self.openDBObject = None
                self.database_editor.current_opened_item = None

            self.actionDatabase.setEnabled(True)
            self.actionExport_To_Database.setEnabled(True)
            self.actionUpdate_Current_Item.setEnabled(True)
            self.database_editor = dbeditor.DatabaseEditor(
                size_callback, make_thumbnail, parent=self
            )
            self.actionDatabase.triggered.connect(self.database_editor.show)
            self.actionExport_To_Database.triggered.connect(
                self.database_editor.insert_item
            )
            self.actionUpdate_Current_Item.triggered.connect(
                self.database_editor.update_current_item
            )
            self.database_editor.openObjectRequested.connect(open_request)
            self.database_editor.saveObjectRequested.connect(save_request)
            self.database_editor.setCurrentObjectRequested.connect(set_object_request)
            self.database_editor.objectDeleted.connect(delete_request)

            self.segment_editor.set_database(
                dbeditor.DatabaseEditor(size_callback, make_thumbnail, parent=self)
            )

            self.mtgeditor.open_file.connect(reset_open_object)
            QMessageBox.information(
                self,
                "Connection success",
                "The connection to the MongoDB server has succeeded",
            )
            self.database_editor.show()
        else:
            QMessageBox.warning(
                self,
                "Connection fail",
                "The connection to the MongoDB server has failed",
            )
            self.db_connection.show()

    def db_connection_validated(self):
        try:
            # Python 3.x
            from urllib.parse import quote_plus
        except ImportError:
            # Python 2.x
            from urllib.parse import quote_plus

        mongodb_address = self.db_connection.addressComboBox.currentText()
        mongodb_username = self.db_connection.usernameLineEdit.text()
        mongodb_password = self.db_connection.passwordLineEdit.text()
        uri = "mongodb://"
        if self.db_connection.IDGroupBox.isChecked():
            uri += (
                quote_plus(mongodb_username)
                + ":"
                + quote_plus(mongodb_password)
                + "@"
                + mongodb_address
            )
        else:
            uri += mongodb_address
        from .database.server_manip import WorkerTestConnection, server_info

        server_info.mongodb_uri = uri

        self.workerThread = QThread()
        self.workerObject = WorkerTestConnection()
        self.workerObject.moveToThread(self.workerThread)
        self.workerThread.started.connect(self.workerObject.run)
        self.workerObject.finished.connect(self.workerThread.quit)
        self.workerObject.result.connect(self.test_connection_callback)
        self.workerThread.start()


def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = "-" * 80
    logFile = "plantscan3d.log"
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
    notice = """PlantScan3D v%s
%s
An unhandled exception occurred. The system may become unstable.
A log has been written to "%s".
Please report the problem at https://github.com/fredboudon/plantscan3d/issues.
%s
Error information:
Date: %s
""" % (psc_version, separator, logFile, separator, timeString)

    tbinfofile = io.StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = "%s: \n%s" % (str(excType), str(excValue))
    sections = [separator, errmsg, separator, tbinfo]
    msg = "\n".join(sections)
    noticelog = "\n".join([psc_version, separator, timeString]) + "\n"
    with open(logFile, "w") as f:
        f.write(noticelog)
        f.write(msg)
    errorbox = QMessageBox()
    errorbox.setText(str(notice) + str(msg))
    errorbox.exec_()


import io
import sys
import time
import traceback

sys._excepthook = sys.excepthook
sys.excepthook = excepthook


def main():
    import os
    import sys

    app = QApplication(["-qwindowtitle", "PlantScan3D"])
    app.setApplicationName("PlantScan3D")
    app.setApplicationDisplayName("PlantScan3D")
    app.setDesktopFileName("PlantScan3D")
    app.setApplicationVersion(psc_version)
    window = MainWindow()
    window.loadModules()
    window.show()
    if len(sys.argv) > 1:
        for fname in sys.argv[1:]:
            if os.path.exists(fname):
                fname = os.path.abspath(fname)
                window.mtgeditor.openFile(fname)
    app.setWindowIcon(QIcon("images/icon.png"))
    return app.exec_()


if __name__ == "__main__":
    main()
