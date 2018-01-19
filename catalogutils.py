# encoding: utf-8

import gvsig
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

import os

from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.fmap.dal import DALLocator
from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.andami import PluginsLocator


from org.gvsig.scripting import ScriptingLocator

explorer = None
mapContextManager = None
iconTheme = None
dataManager = None

def getDataFolder():
  return ScriptingLocator.getManager().getDataFolder("Catalog").getAbsolutePath()

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
  
def createJMenuItem(label, function):
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



def main(*args):
    pass
