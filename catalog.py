# encoding: utf-8

import gvsig
from gvsig import currentView
from gvsig import getResource
from gvsig.libs.formpanel import MouseListenerAdapter

from java.io import File
from java.awt.event import MouseEvent
from javax.imageio import ImageIO
from javax.swing import JTree
from javax.swing import JScrollPane
from javax.swing.tree import DefaultTreeCellRenderer
from javax.swing.tree import DefaultTreeModel
from javax.swing.tree import TreePath
from org.gvsig.fmap.dal import DALLocator
from org.gvsig.tools import ToolsLocator

import addons.Catalog.catalogutils
reload(addons.Catalog.catalogutils)
import addons.Catalog.folders
reload(addons.Catalog.folders)
import addons.Catalog.bookmarks
reload(addons.Catalog.bookmarks)
import addons.Catalog.databases
reload(addons.Catalog.databases)

from addons.Catalog.catalogutils import CatalogNode
from addons.Catalog.folders import Folders
from addons.Catalog.bookmarks import Bookmarks, BookmarkFolder
from addons.Catalog.databases import Databases

class Catalog(CatalogNode):
  def __init__(self, tree):
    CatalogNode.__init__(self,None, icon=getResource(__file__,"images","Catalog.png"))    
    self.__tree = tree
    self.add(Bookmarks(self))
    self.add(Folders(self))
    self.add(Databases(self))

  def getBookmarks(self):
    return self.getChildAt(0)
    
  def getFolders(self):
    return self.getChildAt(1)
    
  def getDatabases(self):
    return self.getChildAt(2)
    
  def toString(self):
    i18n = ToolsLocator.getI18nManager()
    return i18n.getTranslation("_Data_sources")

  def getTreePath(self):
    return [ self ]
    
  def getTree(self):
    return self.__tree
    
class CatalogCellRenderer(DefaultTreeCellRenderer):
  def __init__(self, icon_folder, icon_doc):
    self._icon_folder = icon_folder
    self._icon_doc = icon_doc

  def getTreeCellRendererComponent(self, tree, value, selected, expanded, isLeaf, row, focused):
    c = DefaultTreeCellRenderer.getTreeCellRendererComponent(self, tree, value, selected, expanded, isLeaf, row, focused)
    icon = value.getIcon()
    if icon == None:
      if value.isLeaf():
        icon = self._icon_doc
      else:
        icon = self._icon_folder
    self.setIcon(icon)
    return c

class JCatalogTree(JTree):
  def __init__(self):
    self.__catalog = Catalog(self)
    self.getModel().setRoot(self.__catalog)
    self.setCellRenderer(
      CatalogCellRenderer(
        self.__catalog.load_icon(getResource(__file__,"images","Folder.png")),
        self.__catalog.load_icon(getResource(__file__,"images","Document.png")),
      )
    )    
    self.addMouseListener(MouseListenerAdapter(self.mouseClicked))

  def addCurrentLayerToBookmarks(self):
   currentNode = None
   treePath = self.getSelectionPath()
   if treePath != None:
     currentNode = treePath.getLastPathComponent()
   if not isinstance(currentNode,BookmarkFolder):
     currentNode = self.__catalog.getChildAt(0)
   currentNode.mnuAddCurrentLayerToBookmarks()
   
  def mouseClicked(self, event):
    if event.isPopupTrigger():
      tree = event.getSource()
      treePath = tree.getClosestPathForLocation(event.getX(), event.getY())
      if treePath!=None :
        tree.setSelectionPath(treePath)
        node = treePath.getLastPathComponent()
        node.showPopup(event.getComponent(), event.getX(), event.getY())
      
    elif event.getClickCount() == 2 and event.getID() == MouseEvent.MOUSE_CLICKED  and event.getButton() == MouseEvent.BUTTON1:
      tree = event.getSource()
      if not tree.isSelectionEmpty() :
        treePath = tree.getSelectionPath()
        node = treePath.getLastPathComponent()
        node.actionPerformed(event)
    
    
def main(*args):
  i18n = ToolsLocator.getI18nManager()
  currentView().getWindowOfView().getViewInformationArea().add(
    JScrollPane(JCatalogTree()), 
    "Catalog", 
    100, 
    i18n.getTranslation("_Catalog"), 
    None, 
    None
  )
  