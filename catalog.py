# encoding: utf-8

import gvsig
from gvsig import currentView
from gvsig import getResource
from gvsig.libs.formpanel import MouseListenerAdapter

import sys

from java.io import File
from java.awt.event import MouseEvent
from javax.imageio import ImageIO
from javax.swing import JTree
from javax.swing import JScrollPane
from javax.swing.tree import DefaultTreeCellRenderer
from javax.swing.tree import DefaultTreeModel
from javax.swing.tree import TreePath
from javax.swing import JPopupMenu
from org.gvsig.fmap.dal import DALLocator
from org.gvsig.tools import ToolsLocator

import addons.Catalog.catalogutils

from addons.Catalog.catalogutils import CatalogRoot
from addons.Catalog.cataloglocator import getCatalogManager
from addons.Catalog.catalogutils import createJMenuItem

class Catalog(CatalogRoot):
  def __init__(self, tree):
    CatalogRoot.__init__(self,tree)    
    catalogManager = getCatalogManager()
    for node in catalogManager.getCatalogNodes():
      try:
        #print "Catalog, add node " + repr(node)
        self.add(node(self))
      except:
        ex = sys.exc_info()[1]
        gvsig.logger("Can't add node '"+repr(node)+"'. " + str(ex), gvsig.LOGGER_WARN, ex)
           
  def getBookmarks(self):
    return self.getChildAt(0)
    
  def getFolders(self):
    return self.getChildAt(1)
    
  def getDatabases(self):
    return self.getChildAt(2)

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),lambda e:self.getTree().getModel().reload()))
    return menu    
   
class CatalogCellRenderer(DefaultTreeCellRenderer):
  def __init__(self, icon_folder, icon_doc):
    self._icon_folder = icon_folder
    self._icon_doc = icon_doc

  def getTreeCellRendererComponent(self, tree, value, selected, expanded, isLeaf, row, focused):
    c = DefaultTreeCellRenderer.getTreeCellRendererComponent(self, tree, value, selected, expanded, isLeaf, row, focused)
    getIcon = getattr(value,"getIcon")
    if getIcon == None:
      icon = self._icon_folder
    else:
      icon = getIcon()
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
    from addons.Catalog.bookmarks import BookmarkFolder
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
  catalogManager = getCatalogManager()
  catalogManager.addCatalogToView(currentView())
  #catalog  = Catalog(JTree())
 