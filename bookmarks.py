# encoding: utf-8

import gvsig
from gvsig import getResource
from gvsig.commonsdialog import inputbox, msgbox, confirmDialog, QUESTION, WARNING, YES, YES_NO

from java.io import File
from javax.swing import JPopupMenu
from javax.swing import JSeparator

from java.io import FileOutputStream
from java.io import FileInputStream

import os
import shutil

from org.gvsig.tools import ToolsLocator
from org.gvsig.andami import PluginsLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator

from catalogutils import CatalogSimpleNode, CatalogNode, createJMenuItem, getIconFromParams, getDataFolder

def saveParameters(parameters, pathname):
  persistenceManager = ToolsLocator.getPersistenceManager()
  fos = FileOutputStream(File(pathname))
  persistenceManager.putObject(fos, parameters)
  fos.close()

def loadParameters(pathname):
  persistenceManager = ToolsLocator.getPersistenceManager()
  fis = FileInputStream(File(pathname))
  parameters = persistenceManager.getObject(fis)
  fis.close()
  return parameters


class BookmarkFolder(CatalogNode):
  def __init__(self, parent, path, label = None, icon = None):
    CatalogNode.__init__(self, parent, icon)
    self.__path = path
    self.__files = None
    if label == None:
      self.__label = os.path.basename(self.__path)
    else:
      self.__label = label

  def toString(self):
    return  unicode(self.__label, 'utf-8') 

  def getPath(self):
    return self.__path

  def getFiles(self):
    if self.__files == None:
      #print ">>> getFiles (load)", self
      self.__files = list()
      ls = os.listdir(self.__path)
      lsdirs = list()
      lsfiles = list()
      for f in ls:
        x = os.path.join(self.__path,f)
        if f[0]!=".":
          if os.path.isdir(x):
            lsdirs.append(x)
          elif os.path.splitext(x)[1] == ".data":
            lsfiles.append(x)
      lsdirs.sort(key=lambda s: s.lower())
      lsfiles.sort(key=lambda s: s.lower())
      self.__files.extend(lsdirs)
      self.__files.extend(lsfiles)
    return self.__files

  def reload(self):
    #print ">>> reload (__files set to None) ", self
    self.__files = None
    CatalogNode.reload(self)
    
  def children(self):
    # Returns the children of the receiver as an Enumeration.
    #print ">>> children", self
    return enumerate(self.getFiles())

  def getChildAt(self, childIndex):
    # Returns the child TreeNode at index childIndex.
    #print ">>> getChildAt", self, childIndex, "..."
    fname = os.path.join(self.__path,self.getFiles()[childIndex])
    if os.path.isdir(fname):
      f = BookmarkFolder(self,fname)
    else:
      f = Bookmark(self,fname)
    #print ">>> getChildAt", self, childIndex, f
    return f
    
  def getChildCount(self):
    # Returns the number of children TreeNodes the receiver contains.
    x = len(self.getFiles())
    #print ">>> getChildCount ", self, x
    return x

  def getIndex(self, node):
    # Returns the index of node in the receivers children.
    index = 0
    search = node.getPath()
    #print ">>> getIndex search", repr(search)
    for x in self.getFiles():
      #print ">>> getIndex x", x
      if search == x:
        #print ">>> getIndex ", self, node, index
        return index
      index += 1
    #print ">>> getIndex ", self, node, -1
    return -1
    
  def createPopup(self):
    menu = JPopupMenu()
    menu.add(createJMenuItem("Create group",self.mnuCreateGroup))
    layer = gvsig.currentLayer()
    if layer != None:
      menu.add(createJMenuItem("Add layer '"+layer.getName()+"' to this group",self.mnuAddCurrentLayerToBookmarks))
    menu.add(JSeparator())
    menu.add(createJMenuItem("Reload",self.mnuReload))
    menu.add(JSeparator())
    menu.add(createJMenuItem("Remove group",self.mnuRemoveGroup))
    return menu    

  def mnuAddCurrentLayerToBookmarks(self, event):
    layer = gvsig.currentLayer()
    if layer == None:
      gvsig.commonsdialog.msgbox("Need an active layer")
      return
    params = layer.getDataStore().getParameters().getCopy()
    name = layer.getName()
    pathname = os.path.join(self.getPath(),name) + ".data"
    prompt = "Bookmark name exist, entry another name"
    while pathname==None or os.path.exists(pathname):
      name = inputbox(prompt, "Catalog", QUESTION, initialValue=name)
      if name in ("", None):
        return
      pathname = os.path.join(self.getPath(),name) + ".data"
    #print ">>> AddCurrentLayerToBookmarks ", self, pathname
    saveParameters(params, pathname)
    self.reload()
    self.expand()


  def mnuCreateGroup(self, event):
    name = ""
    pathname = None
    prompt = "Group name"
    while pathname==None or os.path.exists(pathname):
      name = inputbox(prompt, "Catalog", QUESTION, initialValue=name)
      if name in ("", None):
        return
      prompt = "Group name exist, entry another name"
      pathname = os.path.join(self.getPath(),name)
    #print ">>> CreateGroup ", self, pathname
    os.mkdir(pathname)
    self.reload()
    self.expand()


  def mnuRemoveGroup(self, event):
    #print ">>> RemoveGroup ", self
    if confirmDialog("Are you sure to remove '%s' ?" % os.path.basename(self.getPath()), "Catalog",YES_NO,QUESTION)==YES:
      shutil.rmtree(self.getPath())
      self.getParent().reload()
      self.getParent().expand()

  def mnuReload(self, event):
    #print ">>> Reload ", self
    self.reload()
    self.expand()

    
class Bookmark(CatalogSimpleNode):
  def __init__(self, parent, path, label = None):
    CatalogSimpleNode.__init__(self, parent)
    self.__path = path
    self.__params = loadParameters(self.__path)
    self.setIcon(getIconFromParams(self.__params))
    if label == None:
      self.__label = os.path.splitext(os.path.basename(self.__path))[0]
    else:
      self.__label = label

  def getPath(self):
    return self.__path
    
  def toString(self):
    return  unicode(self.__label, 'utf-8') 
  
  def createPopup(self):
    menu = JPopupMenu()
    menu.add(createJMenuItem("Chage name",self.mnuChangeName))
    menu.add(createJMenuItem("Edit parameters",self.mnuEditParameters))
    menu.add(JSeparator())
    menu.add(createJMenuItem("Remove from bookmarks",self.mnuRemoveFromBookmarks))
    return menu    

  def mnuChangeName(self, event):
    name = ""
    pathname = None
    prompt = "Bookmark name"
    while pathname==None or os.path.exists(pathname):
      name = inputbox(prompt, "Catalog", QUESTION, initialValue=name)
      if name in ("", None):
        return
      prompt = "Bookmark name exist, entry another name"
      pathname = os.path.join(os.path.dirname(self.getPath()),name) + ".data"
    try:
      #print ">>> ChangeName ", repr(self.getPath()), repr(pathname)
      os.rename(self.getPath(), pathname)
    except:
      msgbox("Can't rename bookmark","Catalog", WARNING)
    self.getParent().reload()
    
  def mnuEditParameters(self, event):
    manager = DALSwingLocator.getDataStoreParametersPanelManager()
    panel = manager.createDataStoreParametersPanel(self.__params)
    manager.showPropertiesDialog(self.__params, panel)
  
  def mnuRemoveFromBookmarks(self, event):
    #print "RemoveFromBookmarks ", self
    if confirmDialog("Are you sure to remove '%s' ?" % os.path.basename(self.getPath()), "Catalog",YES_NO,QUESTION)==YES:
      os.remove(self.getPath())
      self.getParent().reload()
        
  def actionPerformed(self, event):
    view = gvsig.currentView()
    if view == None:
      msgbox("Need an active view")
      return
    try:
      mapContextManager = MapContextLocator.getMapContextManager()
      dataManager = DALLocator.getDataManager()
      parameters = self.__params
      dataStore = dataManager.openStore(parameters.getDataStoreName(), parameters)
      layer = mapContextManager.createLayer(dataStore.getName(), dataStore)
      view.getMapContext().getLayers().addLayer(layer)
      DisposeUtils.disposeQuietly(dataStore)
    except Exception,ex:
      print ex.__class__.__name__,": ", str(ex)
    

class Bookmarks(BookmarkFolder):
  def __init__(self, parent):
    BookmarkFolder.__init__(self, 
      parent, 
      getDataFolder(), 
      "Bookmarks", 
      icon=getResource(__file__,"images","Favourite.png")
    )

  def createPopup(self):
    menu = JPopupMenu()
    menu.add(createJMenuItem("Create group",self.mnuCreateGroup))
    layer = gvsig.currentLayer()
    if layer != None:
      menu.add(createJMenuItem("Add layer '"+layer.getName()+"' to bookmarks",self.mnuAddCurrentLayerToBookmarks))
    menu.add(JSeparator())
    menu.add(createJMenuItem("Reload",self.mnuReload))
    return menu    

  def toString(self):
    return "Bookmarks"
    
def main(*args):
    pass
