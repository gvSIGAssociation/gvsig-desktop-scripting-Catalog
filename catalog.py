# encoding: utf-8

from gvsig import currentView
from gvsig import currentLayer
from gvsig.commonsdialog import msgbox, inputbox, confirmDialog
from gvsig.commonsdialog import QUESTION, YES_NO_CANCEL, NO
from gvsig import getResource

import os.path

from os.path import join, dirname
from StringIO import StringIO

from java.net import URLDecoder
from java.net import URLEncoder

from java.io import File
from java.io import ByteArrayInputStream
from java.io import ByteArrayOutputStream

from javax.swing.tree import DefaultTreeModel
from javax.swing.tree import DefaultMutableTreeNode
from javax.swing.tree import DefaultTreeCellRenderer
from javax.swing import JMenuItem
from javax.swing import JPopupMenu
from javax.swing import JSeparator
from java.awt.event import MouseEvent

from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.dispose import DisposeUtils
from org.gvsig.tools.swing.api import ToolsSwingLocator

from org.gvsig.app import ApplicationLocator
from org.gvsig.andami import PluginsLocator
from org.gvsig.app.project.documents.view import ViewManager
from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.fmap.dal import DALLocator

from org.gvsig.scripting.app.extension import ScriptingExtension

#import gvsig.libs.formpanel
#reload(gvsig.libs.formpanel)

from gvsig.libs.formpanel import FormPanel, load_icon

import xmltodic

def serializeParameters(parameters):
  persistenceManager = ToolsLocator.getPersistenceManager()
  bos = ByteArrayOutputStream(1000)
  persistenceManager.putObject(bos, parameters)
  data = URLEncoder.encode(bos.toString(), "UTF-8")
  return data

def deserializeParameters(data):
  persistenceManager = ToolsLocator.getPersistenceManager()
  data = URLDecoder.decode(data, "UTF-8")
  bis = ByteArrayInputStream(data)
  parameters = persistenceManager.getObject(bis)
  return parameters


class Item(object):
  def __init__(self,name, value=None, icon=None):
    self._name = name
    self._value = value
    self._iconName = icon
    if self._iconName != None:
        iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
        self._icon = iconTheme.get(self._iconName)
    else:
      self._icon = None

  def __repr__(self):
    return self._name

  def getLabel(self):
    return self._name

  def getIcon(self):
    return self._icon

  def getIconName(self):
    return self._iconName

  def getValue(self):
    return self._value

  def setLabel(self,label):
    self._name = label

  def isGroup(self):
    return self._value == None


class CatalogCellRenderer(DefaultTreeCellRenderer):
  def __init__(self, icon_folder, icon_layer):
    self._icon_folder = icon_folder
    self._icon_layer = icon_layer

  def getTreeCellRendererComponent(self, tree, value, selected, expanded, isLeaf, row, focused):
    c = DefaultTreeCellRenderer.getTreeCellRendererComponent(self, tree, value, selected, expanded, isLeaf, row, focused)
    icon = value.getUserObject().getIcon()
    if icon == None:
      if value.getUserObject().isGroup():
        icon = self._icon_folder
      else:
        icon = self._icon_layer
    self.setIcon(icon)
    return c

class CatalogPanel(FormPanel):

  def __init__(self):
    FormPanel.__init__(self)
    self.mnuCreateNewFolder = JMenuItem("Create group")
    self.mnuAddCurrentLayerToThisFolder = JMenuItem("Add current layer to this group")
    self.mnuAddLayerToTheCurrentView = JMenuItem("Add layer to the current view")
    self.mnuRename = JMenuItem("Rename")
    self.mnuRemove = JMenuItem("Remove")
    self.mnuProperties = JMenuItem("Properties")

    self.load(join(dirname(__file__),"catalogpanel.xml"))
    self.catalog = Catalog()
    self.setPreferredSize(300,400)
    self.treeDataSources.setCellRenderer(
      CatalogCellRenderer(
        self.load_icon(join(dirname(__file__),"images","folder-icon.png")),
        self.load_icon(join(dirname(__file__),"images","layer-icon.png")),
      )
    )
    self.treeDataSources.setModel(DefaultTreeModel(self.catalog.getRoot()))

  def getCurrentNode(self):
    path = self.treeDataSources.getSelectionPath()
    if path == None:
      self.treeDataSources.setSelectionRow(0)
      path = self.treeDataSources.getSelectionPath()
    if path == None:
      return None
    element = path.getLastPathComponent()
    return element

  def addItem(self, node, item):
    newnode = DefaultMutableTreeNode(item)
    node.add(newnode)
    self.refresh(node)
    self.catalog.save()

  def refresh(self, node):
    model = self.treeDataSources.getModel()
    model.reload(node)
    self.treeDataSources.expandPath(self.treeDataSources.getSelectionPath())

  def treeDataSources_mouseClick(self,e):
    if e.isPopupTrigger():
      node = self.getCurrentNode()
      if node == None:
        return
      menu = JPopupMenu()
      if node.getUserObject().isGroup():
        menu.add(self.mnuCreateNewFolder)
        menu.add(self.mnuAddCurrentLayerToThisFolder)
        menu.add(JSeparator())
        menu.add(self.mnuRename)
        menu.add(JSeparator())
        menu.add(self.mnuRemove)
      else:
        menu.add(self.mnuCreateNewFolder)
        menu.add(self.mnuAddLayerToTheCurrentView)
        menu.add(JSeparator())
        menu.add(self.mnuRename)
        menu.add(JSeparator())
        menu.add(self.mnuRemove)
        menu.add(JSeparator())
        menu.add(self.mnuProperties)
      menu.show(e.getComponent(), e.getX(), e.getY())
    elif e.getClickCount() == 2 and e.getID() == MouseEvent.MOUSE_CLICKED and e.getButton() == MouseEvent.BUTTON1:
      self.mnuAddLayerToTheCurrentView_click(None)

  def mnuCreateNewFolder_click(self,*args):
    node = self.getCurrentNode()
    if node == None:
      return
    folderName = inputbox("Group name","Catalog tree")
    if folderName in (None,""):
      return
    self.addItem(node, Item(folderName))

  def mnuAddCurrentLayerToThisFolder_click(self,*args):
    self.addCurrentLayerToCatalog()

  def addCurrentLayerToCatalog(self):
    node = self.getCurrentNode()
    if node == None:
      return
    layer = currentLayer()
    if layer == None:
      msgbox("Need an active layer")
      return
    try:
      params = serializeParameters(layer.getDataStore().getParameters())
      self.addItem(node, Item(layer.getName(),params, layer.getTocImageIcon()))
    except Exception,ex:
      print ex.__class__.__name__,": ", str(ex)

  def mnuAddLayerToTheCurrentView_click(self,*args):
    node = self.getCurrentNode()
    if node == None:
      return
    view = currentView()
    if view == None:
      msgbox("Need a active view")
      return
    try:
      mapContextManager = MapContextLocator.getMapContextManager()
      dataManager = DALLocator.getDataManager()
      parameters = deserializeParameters(node.getUserObject().getValue())
      dataStore = dataManager.openStore(parameters.getDataStoreName(), parameters)
      layer = mapContextManager.createLayer(dataStore.getName(), dataStore)
      view.getMapContext().getLayers().addLayer(layer)
      DisposeUtils.disposeQuietly(dataStore)
    except Exception,ex:
      print ex.__class__.__name__,": ", str(ex)

  def mnuRename_click(self,*args):
    node = self.getCurrentNode()
    if node == None:
      return
    item = node.getUserObject()
    s = inputbox("New name:", "Catalog - rename", QUESTION, item.getLabel())
    if s in ("",None):
      return
    item.setLabel(s)
    self.refresh(node)
    self.catalog.save()

  def mnuRemove_click(self,*args):
    node = self.getCurrentNode()
    if node == None:
      return
    item = node.getUserObject()
    if confirmDialog("Remove '%s' from the catalog ?" % item.getLabel(), "Catalog - remove", YES_NO_CANCEL, QUESTION) == NO:
      return
    parent = node.   getParent()
    node.removeFromParent()
    self.refresh(parent)
    self.catalog.save()


  def show(self):
    self.showTool("Catalog tree")


class Catalog(object):
  def __init__(self):
    self.root = DefaultMutableTreeNode(Item("Data sourcces"))
    self.load()

  def getRoot(self):
    return self.root

  def save(self, fname=None):
    if fname == None:
      fname = join(dirname(__file__),"catalog.xml")
    buffer = StringIO()
    self.writeNode(buffer, self.root)
    xml = buffer.getvalue().encode("utf-8")
    f = open(fname,"w")
    f.write(xml)
    f.close()

  def writeNode(self, buffer, node, indent=0):
    item = node.getUserObject()
    if item.isGroup():
      buffer.write('%s<group name="%s">\n' % ("  "*indent,item.getLabel()))
      for n in range(node.getChildCount()):
        child = node.getChildAt(n)
        self.writeNode(buffer,child,indent+1)
      buffer.write('%s</group>\n' % ("  "*indent))
    else:
      if item.getIconName() == None:
        buffer.write('%s<datasource name="%s">%s</datasource>\n' % ("  "*indent,item.getLabel(),item.getValue()))
      else:
        buffer.write('%s<datasource name="%s" icon="%s">%s</datasource>\n' % ("  "*indent,item.getLabel(),item.getIconName(),item.getValue()))

  def load(self, fname=None):
    if fname == None:
      fname = join(dirname(__file__),"catalog.xml")
    if os.path.exists(fname):
      fin = open(fname,"r")
      d = xmltodic.parse(fin)
      root = d["group"]
      self.root = self.loadGroup(root)

  def loadGroup(self, node, parentTreeNode=None):
    #print "\ndumpGroup: name=%r" % (node["@name"]), node

    treeNode = DefaultMutableTreeNode(Item(node["@name"]))
    if parentTreeNode!=None:
      parentTreeNode.add(treeNode)
    groups=node.get("group",None)
    if groups!=None:
      if isinstance(groups,list):
        for child in groups:
          self.loadGroup(child, treeNode)
      else:
        self.loadGroup(groups,treeNode)

    datasources=node.get("datasource",None)
    if datasources!=None:
      if isinstance(datasources,list):
        for child in datasources:
          self.loadDataSource(child, treeNode)
      else:
        self.loadDataSource(datasources, treeNode)
    return treeNode

  def loadDataSource(self, node, parentTreeNode):
    #print "\ndumpDataSource", node, node.__class__.__name__

    treeNode = DefaultMutableTreeNode(Item(node["@name"],node["#text"], node.get("@icon",None)))
    if parentTreeNode!=None:
      parentTreeNode.add(treeNode)


class DatasourceCatalogExtension(ScriptingExtension):
  def __init__(self):
    self._catalogPanel = None

  def canQueryByAction(self):
    return True

  def isEnabled(self,action):
    if action.lower() == "addlayertocatalog":
      view = currentView()
      if view == None:
        return False
      layers = view.getMapContext().getLayers().getActives()
      if layers == None:
        return False
      if len(layers)<1:
        return False
    return True

  def isVisible(self,action):
    return True

  def getCatalogPanel(self):
    if self._catalogPanel == None:
      self._catalogPanel = CatalogPanel()
    return self._catalogPanel

  def execute(self,actionCommand, *args):
    actionCommand = actionCommand.lower()
    if actionCommand == "show":
      self.getCatalogPanel().show()
    elif actionCommand == "addlayertocatalog":
      self.getCatalogPanel().addCurrentLayerToCatalog()

def selfRegister():
  application = ApplicationLocator.getManager()

  icon_show = File(join(dirname(__file__),"images","catalog-icon.png")).toURI().toURL()
  icon_addLayerToCatalog = File(join(dirname(__file__),"images","catalog-add-icon.png")).toURI().toURL()

  iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
  iconTheme.registerDefault("scripting.catalog", "action", "tools-catalog-show", None, icon_show)
  iconTheme.registerDefault("scripting.catalog", "action", "tools-catalog-addLayerToCatalog", None, icon_addLayerToCatalog)

  extension = DatasourceCatalogExtension()
  actionManager = PluginsLocator.getActionInfoManager()
  action_show = actionManager.createAction(
    extension,
    "tools-catalog-show", # Action name
    "Show catalog", # Text
    "show", # Action command
    "tools-catalog-show", # Icon name
    None, # Accelerator
    1009000000, # Position
    "Show catalog" # Tooltip
  )
  action_addCurrentLayer = actionManager.createAction(
    extension,
    "tools-catalog-addLayerToCatalog", # Action name
    "Add to catalog", # Text
    "addLayerToCatalog", # Action command
    "tools-catalog-addLayerToCatalog", # Icon name
    None, # Accelerator
    1009000000, # Position
    "Add active layer to Catalog" # Tooltip
  )
  action_show = actionManager.registerAction(action_show)
  action_addCurrentLayer = actionManager.registerAction(action_addCurrentLayer)

  application.addMenu(action_show, "tools/Catalog/Show catalog")
  application.addMenu(action_addCurrentLayer, "tools/Catalog/Add layer to catalog")

  projectManager = ApplicationLocator.getProjectManager()
  viewManager = projectManager.getDocumentManager(ViewManager.TYPENAME)
  viewManager.addTOCContextAction("tools-catalog-addLayerToCatalog")

def main(*args):
  catalog = CatalogPanel()
  currentView().getWindowOfView().getViewInformationArea().add(
    catalog.asJComponent(), 
    "Catalog", 
    100, 
    "Catalog", 
    None, 
    None
  )
  #catalog.show()
