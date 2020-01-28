# encoding: utf-8

import gvsig

import ConfigParser

import sys

from gvsig import getResource
from gvsig.libs.formpanel import ActionListenerAdapter

from java.io import File
from java.awt.event import ActionListener
from java.awt.event import MouseAdapter
from java.awt.event import MouseEvent
from javax.imageio import ImageIO
from javax.swing import JTree
from javax.swing import JScrollPane
from javax.swing import ImageIcon
from javax.swing import JMenuItem
from javax.swing import JPopupMenu
from javax.swing import JSeparator
from javax.swing.tree import TreeNode
from javax.swing.tree import DefaultTreeCellRenderer
from javax.swing.tree import DefaultTreeModel
from javax.swing.tree import TreePath
from javax.swing import JOptionPane 

import os

from gvsig.commonsdialog import inputbox, msgbox, confirmDialog, QUESTION, WARNING, YES, YES_NO

from org.gvsig.fmap.dal.exception import ValidateDataParametersException
from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.fmap.dal import DALLocator
from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.andami import PluginsLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.tools.swing.api.windowmanager import WindowManager
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.fmap.dal import DataStoreProviderFactory

from gvsig import logger
from gvsig import LOGGER_WARN


from org.gvsig.scripting import ScriptingLocator

explorer = None
mapContextManager = None
iconTheme = None
dataManager = None

def getDataFolder():
  return ScriptingLocator.getManager().getDataFolder("Catalog").getAbsolutePath()

def getConfig():
  fname = os.path.join(getDataFolder(), "catalog.ini")
  config = ConfigParser.ConfigParser()
  if os.path.exists(fname):
    config.read(fname)
  return config

def saveConfig(config):
  fname = os.path.join(getDataFolder(), "catalog.ini")
  f = open(fname,"w")
  config.write(f)
  f.close()

def getDataManager():
  global dataManager
  if dataManager == None:
    dataManager = DALLocator.getDataManager()
  return dataManager

def getIconFromFile(pathname):
  global explorer
  global mapContextManager
  global iconTheme

  if explorer == None:
    explorer = getDataManager().openServerExplorer("FilesystemExplorer", "initialpath", os.path.dirname(pathname))
    
  providerName = explorer.getProviderName(File(pathname))
  if providerName != None:
    #print "Layer %s, %s" % (providerName, pathname)
    if mapContextManager == None:
      mapContextManager = MapContextLocator.getMapContextManager()
    iconName = mapContextManager.getIconLayer(providerName)
    if iconTheme == None:
      iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
    icon = iconTheme.get(iconName)
    return icon
  return None
  
def getIconFromParams(params):
  global mapContextManager
  global iconTheme

  providerName = params.getDataStoreName()
  if providerName != None:
    if mapContextManager == None:
      mapContextManager = MapContextLocator.getMapContextManager()
    iconName = mapContextManager.getIconLayer(providerName)
    if iconTheme == None:
      iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
    icon = iconTheme.get(iconName)
    return icon
  return None

def getProviderFactoryFromFile(pathname):
  global explorer

  if explorer == None:
    explorer = getDataManager().openServerExplorer("FilesystemExplorer", "initialpath", os.path.dirname(pathname))
  providerName = explorer.getProviderName(File(pathname))
  if providerName == None:
    return None
  factory = getDataManager().getStoreProviderFactory(providerName)
  return factory

def getProviderFactoryFromParams(params):
  providerName = params.getDataStoreName()
  factory = getDataManager().getStoreProviderFactory(providerName)
  return factory
  
def createJMenuItem(label, function, iconName=None):
  icon = None
  if iconName!=None:
    iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
    if iconTheme.exists(iconName):
        icon = iconTheme.get(iconName);
  if icon != None:
    item = JMenuItem(label, icon)
  else:
    item = JMenuItem(label)
  item.addActionListener(ActionListenerAdapter(function))
  return item

class CatalogSimpleNode(TreeNode, ActionListener):
  def __init__(self, parent, icon=None):
    self.__parent = parent
    self.setIcon(icon)
        
  def toString(self):
    return  "Unknown"

  def getTree(self):
    return self.__parent.getTree()
    
  def getRoot(self):
    return self.__parent.getRoot()
    
  def createPopup(self):
    return None

  def showPopup(self, invoker, x, y):
    menu = self.createPopup()
    if menu!=None:
      menu.show(invoker, x, y)

  def getIcon(self):
    return self.__icon

  def setIcon(self, icon):
    if icon != None:
      if isinstance(icon, ImageIcon):
        self.__icon = icon
      else:
        self.__icon = self.load_icon(str(icon))
    else:
      self.__icon = None

  def load_icon(self, pathname):
    f = File(str(pathname))
    return ImageIcon(ImageIO.read(f))
  
  def children(self):
    # Returns the children of the receiver as an Enumeration.
    return None
    
  def getAllowsChildren(self):
    # Returns true if the receiver allows children.
    return False

  def getChildAt(self, childIndex):
    # Returns the child TreeNode at index childIndex.
    return None
    
  def getChildCount(self):
    return -1

  def getIndex(self, node):
    # Returns the index of node in the receivers children.
    return -1
     
  def getParent(self):
    # Returns the parent TreeNode of the receiver.
    return self.__parent
    
  def isLeaf(self):
    # Returns true if the receiver is a leaf.
    return True

  def actionPerformed(self, event):
    pass

  def getTreePath(self):
    x = self.getParent().getTreePath()
    x.append(self)
    return x

class CatalogNode(CatalogSimpleNode):
  def __init__(self, parent, icon=None):
    CatalogSimpleNode.__init__(self,parent, icon=icon)
    self._children = None
    
  def toString(self):
    return "node"

  def _getChildren(self):
    #print "### CatalogNode._getChildren"
    if self._children == None:
      self._children = list()
    return self._children
  
  def getAllowsChildren(self):
    # Returns true if the receiver allows children.
    #print "### CatalogNode.getAllowsChildren"
    return True

  def getChildAt(self, childIndex):
    # Returns the child TreeNode at index childIndex.
    #print "### CatalogNode.getChildAt", childIndex
    return self._getChildren()[childIndex]
    
  def getChildCount(self):
    # Returns the number of children TreeNodes the receiver contains.
    #print "### CatalogNode.getChildCount"
    return len(self._getChildren())

  def getIndex(self, node):
    # Returns the index of node in the receivers children.
    #print "### CatalogNode.getIndex", node
    index = 0
    for x in self._getChildren():
      if node == x:
        return index
      index += 1
    return -1
     
  def isLeaf(self):
    # Returns true if the receiver is a leaf.
    #print "### CatalogNode.isLeaf"
    return False

  def expand(self, node=None):
    #print "### CatalogNode.expand", node
    if node == None:
      node = self
    treepath = TreePath(self.getTreePath())
    self.getTree().expandPath(treepath)  
      
  def reload(self):
    #print ">>> reload enter", self.__class__.__name__
    root = self.getTree().getModel().getRoot()
    expandeds = self.getTree().getExpandedDescendants(TreePath(root))
    #print ">>> reload ", self.__class__.__name__, self.getTree().getModel().__class__.__name__
    self.getTree().getModel().reload()
    if expandeds != None:
      for treePath in expandeds:
        try:
          self.getTree().expandPath(treePath)
        except:
          pass
    #print ">>> reload exit", self.__class__.__name__

  def add(self, element):
    #print "### CatalogNode.add", element
    self._getChildren().append(element)
    self.reload()
    
  def remove(self, element):
    #print "### CatalogNode.remove", element
    self._getChildren().remove(element)
    self.reload()

  def __delslice__(self, i, j):
    #print "### CatalogNode.__delslice__", i, j
    del self._getChildren()[i:j]


def openAsTable(params):
    i18n = ToolsLocator.getI18nManager()
    try:
      params.validate()
    except ValidateDataParametersException, ex:
      msgbox(i18n.getTranslation("_It_is_not_possible_to_open_the_recurse_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
      return
    factory = getProviderFactoryFromParams(params)
    if ( factory!=None and 
      factory.hasTabularSupport()!=DataStoreProviderFactory.YES ):
      msgbox(i18n.getTranslation("_The_resource_has_no_tabular_support"))
      return

    dataManager = getDataManager();
    store = dataManager.openStore(params.getDataStoreName(), params)
    if not store.supportReferences():

      dialogs = ToolsSwingLocator.getThreadSafeDialogsManager()
      dialogs.messageDialog(
              "\""+ store.getName() + "\"\n"+
              i18n.getTranslation("_The_table_has_no_primary_key_or_OID") +"\n" +
                     i18n.getTranslation("_Many_features_selection_deletion_modification_will_not_be_available_as_they_require_it_for_proper_operation"),
              None, 
              i18n.getTranslation("_Warning"),
              JOptionPane.WARNING_MESSAGE, 
              "TableDoNotSupportReferences"
     )
    projectManager = ApplicationLocator.getManager().getProjectManager()
    project = projectManager.getCurrentProject()

    tableDoc = project.getDocument(store.getName(),TableManager.TYPENAME)
      
    if tableDoc == None:
      tableDoc = projectManager.createDocument(TableManager.TYPENAME)
      tableDoc.setStore(store)
      tableDoc.setName(store.getName())
      project.addDocument(tableDoc)
      
    ApplicationLocator.getManager().getUIManager().addWindow(tableDoc.getMainWindow())

def openAsForm(params):
  i18n = ToolsLocator.getI18nManager()
  try:
    params.validate()
  except ValidateDataParametersException, ex:
    msgbox(i18n.getTranslation("_It_is_not_possible_to_open_the_recurse_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
    return
  store = getDataManager().openStore(params.getDataStoreName(), params)
  swingManager = DALSwingLocator.getSwingManager()
  form = swingManager.createJFeaturesForm(store)
  form.showForm(WindowManager.MODE.WINDOW)

def openAsParameters(params):
  manager = DALSwingLocator.getDataStoreParametersPanelManager()
  panel = manager.createDataStoreParametersPanel(params)
  manager.showPropertiesDialog(params, panel)
  
def openAsLayer(params):
  i18n = ToolsLocator.getI18nManager()
  view = gvsig.currentView()
  if view == None:
    msgbox(i18n.getTranslation("_Need_an_active_view"))
    return
  try:
    params.validate()
  except ValidateDataParametersException, ex:
    msgbox(i18n.getTranslation("_It_is_not_possible_to_open_the_recurse_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
    return
  try:
    factory = getProviderFactoryFromParams(params)
    if ( factory!=None and 
      factory.hasTabularSupport()==DataStoreProviderFactory.YES and 
      factory.hasVectorialSupport()!=DataStoreProviderFactory.YES and
      factory.hasRasterSupport()!=DataStoreProviderFactory.YES ):
      # No es una layer... lo abrimos como tabla.
      openAsTable(params)
      return
    mapContextManager = MapContextLocator.getMapContextManager()
    dataManager = DALLocator.getDataManager()
    store = dataManager.openStore(params.getDataStoreName(), params)
    if store.getDefaultFeatureType().getDefaultGeometryAttribute()==None:
      msgbox(i18n.getTranslation("_The_table_has_no_geographic_information"))
      return
    layer = mapContextManager.createLayer(store.getName(), store)
    view.getMapContext().getLayers().addLayer(layer)
    DisposeUtils.disposeQuietly(store)
  except:
    logger("Can't add layer from params (%r)" % params, LOGGER_WARN, sys.exc_info()[1])
  
def openSearchDialog(params):
  i18n = ToolsLocator.getI18nManager()
  try:
    params.validate()
  except ValidateDataParametersException, ex:
    msgbox(i18n.getTranslation("_It_is_not_possible_to_open_the_recurse_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
    return
  swingManager = DALSwingLocator.getSwingManager()
  winmgr = ToolsSwingLocator.getWindowManager()
  store = getDataManager().openStore(params.getDataStoreName(), params)
  panel = swingManager.createFeatureStoreSearchPanel(store)
  winmgr.showWindow(
          panel.asJComponent(), 
          i18n.getTranslation("_Search")+ ": " + store.getName(), 
          WindowManager.MODE.WINDOW
  )

def addToBookmarks(root, params, name):
  i18n = ToolsLocator.getI18nManager()
  bookmarks = root.getBookmarks()
  try:
    params.validate()
  except ValidateDataParametersException, ex:
    msgbox(i18n.getTranslation("_It_is_not_possible_to_add_the_recuse_to_the_markers_Try_to_edit_the_parameters_first_and_fill_in_the_required_values"+"\n\n"+ex.getLocalizedMessageStack()))
    return
  bookmarks.addParamsToBookmarks(name,params)


def main(*args):
  pass
