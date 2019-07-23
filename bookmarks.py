# encoding: utf-8

import gvsig

from gvsig import getResource
from gvsig.commonsdialog import inputbox, msgbox, confirmDialog, QUESTION, WARNING, YES, YES_NO

from java.io import File
from java.io import FileOutputStream
from java.io import FileInputStream
from javax.swing import JPopupMenu
from javax.swing import JSeparator

import os
import shutil
import sys

from org.gvsig.andami import PluginsLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.fmap.dal import DALLocator
from org.gvsig.tools.dispose import DisposeUtils
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.swing.api.windowmanager import WindowManager
from javax.swing import JMenuItem

from  addons.Catalog.cataloglocator import getCatalogManager

from addons.Catalog.catalogutils import CatalogSimpleNode, CatalogNode, createJMenuItem
from addons.Catalog.catalogutils import getIconFromParams, getDataFolder, getProviderFactoryFromParams
from addons.Catalog.catalogutils import getDataManager


from org.gvsig.fmap.dal import DataStoreProviderFactory

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from gvsig import logger
from gvsig import LOGGER_WARN

from org.gvsig.tools.swing.api.windowmanager import WindowManager_v2

from gvsig.libs.formpanel import load_icon

def saveParameters(parameters, pathname):
  persistenceManager = ToolsLocator.getPersistenceManager()
  fos = None
  try:
    fos = FileOutputStream(File(pathname))
    persistenceManager.putObject(fos, parameters)
  except:
    os.remove(pathname)
  finally:
    if fos!=None:
      fos.close()

def loadParameters(pathname):
  persistenceManager = ToolsLocator.getPersistenceManager()
  fis = None
  try:
    fis = FileInputStream(File(pathname))
    parameters = persistenceManager.getObject(fis)
    return parameters
  finally:
    if fis!=None:
      fis.close()

def getBookmarksFolder():
  f = os.path.join(getDataFolder(),"bookmarks")
  if not os.path.exists(f):
    os.mkdir(f)
  return f

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
      return BookmarkFolder(self,fname)
    return Bookmark(self,fname)
    
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
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Create_group"),self.mnuCreateGroup))
    layer = gvsig.currentLayer()
    if layer != None:
      menu.add(createJMenuItem(i18n.getTranslation("_Add_layer_{0}_to_this_group",(layer.getName(),)),self.mnuAddCurrentLayerToBookmarks))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.mnuReload))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_group"),self.mnuRemoveGroup))
    return menu    

  def mnuAddCurrentLayerToBookmarks(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    layer = gvsig.currentLayer()
    if layer == None:
      gvsig.commonsdialog.msgbox(i18n.getTranslation("_Need_an_active_layer"))
      return
    params = layer.getDataStore().getParameters().getCopy()
    self.addParamsToBookmarks(layer.getName(), params)
    
  def addParamsToBookmarks(self, name, params):
    i18n = ToolsLocator.getI18nManager()
    pathname = os.path.join(self.getPath(),name) + ".data"
    prompt = i18n.getTranslation("_Bookmark_name_already_exist_entry_another_name")
    while pathname==None or os.path.exists(pathname):
      name = inputbox(prompt, i18n.getTranslation("_Catalog"), QUESTION, initialValue=name)
      if name in ("", None):
        return
      pathname = os.path.join(self.getPath(),name) + ".data"
    #print ">>> AddCurrentLayerToBookmarks ", self, pathname
    saveParameters(params, pathname)
    self.reload()
    self.expand()


  def mnuCreateGroup(self, event):
    i18n = ToolsLocator.getI18nManager()
    name = ""
    pathname = None
    prompt = i18n.getTranslation("_Group_name")
    while pathname==None or os.path.exists(pathname):
      name = inputbox(prompt, i18n.getTranslation("_Catalog"), QUESTION, initialValue=name)
      if name in ("", None):
        return
      prompt = i18n.getTranslation("_Group_name_already_exist_entry_another_name")
      pathname = os.path.join(self.getPath(),name)
    #print ">>> CreateGroup ", self, pathname
    os.mkdir(pathname)
    self.reload()
    self.expand()


  def mnuRemoveGroup(self, event):
    i18n = ToolsLocator.getI18nManager()
    #print ">>> RemoveGroup ", self
    prompt = i18n.getTranslation("_Are_you_sure_to_remove_{0}", (os.path.basename(self.getPath()),))
    if confirmDialog(prompt, i18n.getTranslation("_Catalog"),YES_NO,QUESTION)==YES:
      shutil.rmtree(self.getPath())
      self.getParent().reload()
      self.getParent().expand()

  def mnuReload(self, event):
    #print ">>> Reload ", self
    self.reload()
    self.expand()

    
class Bookmark(CatalogSimpleNode):
  def __init__(self, parent, path, label=None, params=None):
    CatalogSimpleNode.__init__(self, parent)
    self.__path = path
    if params == None:
      try:
        self.__params = loadParameters(self.__path)
      except:
        self.__params = None
    else:
      self.__params = params
    if self.__params == None:
      self.setIcon(load_icon(getResource(__file__,"images","Warning.png")))
    else:
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
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    if self.__params != None:
      factory = getProviderFactoryFromParams(self.__params)
      if factory!=None : 
        if (factory.hasVectorialSupport()!=DataStoreProviderFactory.NO or
          factory.hasRasterSupport()!=DataStoreProviderFactory.NO ):
          menu.add(createJMenuItem(i18n.getTranslation("_Add_to_view"),self.actionPerformed))
        if factory.hasTabularSupport()==DataStoreProviderFactory.YES:
          menu.add(createJMenuItem(i18n.getTranslation("_Open_as_table"),self.openAsTable))
          menu.add(createJMenuItem(i18n.getTranslation("_Open_as_form"),self.openAsForm))
      menu.add(JSeparator())
      menu.add(createJMenuItem(i18n.getTranslation("_Chage_name"),self.mnuChangeName))
      menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.mnuEditParameters))
      menu.add(JSeparator())    
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_bookmark"),self.mnuRemoveFromBookmarks))
    actions = getCatalogManager().getActions("BOOKMARKS_BOOKMARK", self.__params)
    if len(actions)>0 :
      menu.add(JSeparator())
      for action in actions:
        menu.add(JMenuItem(action))
    return menu    
 
  def openAsForm(self, *args):
    store = getDataManager().openStore(self.__params.getDataStoreName(), self.__params)
    swingManager = DALSwingLocator.getSwingManager()
    form = swingManager.createJFeaturesForm(store)
    form.showForm(WindowManager.MODE.WINDOW)
  
  def openAsTable(self, event=None):
    factory = getProviderFactoryFromParams(self.__params)
    if factory==None or factory.hasTabularSupport()!=DataStoreProviderFactory.YES:
      return
    store = getDataManager().openStore(factory.getName(), self.__params)
    projectManager = ApplicationLocator.getManager().getProjectManager()
    tableDoc = projectManager.createDocument(TableManager.TYPENAME)
    tableDoc.setStore(store)
    tableDoc.setName(str(self))
    projectManager.getCurrentProject().addDocument(tableDoc)
    ApplicationLocator.getManager().getUIManager().addWindow(tableDoc.getMainWindow())
  
  def mnuChangeName(self, event):
    i18n = ToolsLocator.getI18nManager()
    name = ""
    pathname = None
    prompt = i18n.getTranslation("_Bookmark_name")
    while pathname==None or os.path.exists(pathname):
      name = inputbox(prompt, i18n.getTranslation("_Catalog"), QUESTION, initialValue=name)
      if name in ("", None):
        return
      prompt = i18n.getTranslation("_Bookmark_name_already_exist_entry_another_name")
      pathname = os.path.join(os.path.dirname(self.getPath()),name) + ".data"
    try:
      #print ">>> ChangeName ", repr(self.getPath()), repr(pathname)
      os.rename(self.getPath(), pathname)
    except:
      msgbox(i18n.getTranslation("_Cant_rename_bookmark"),i18n.getTranslation("_Catalog"), WARNING)
    self.getParent().reload()
    
  def mnuEditParameters(self, event):
    manager = DALSwingLocator.getDataStoreParametersPanelManager()
    if manager.showPropertiesDialog(self.__params)==WindowManager_v2.BUTTON_OK:
      saveParameters(self.__params, self.__path)
  
  def mnuRemoveFromBookmarks(self, event):
    i18n = ToolsLocator.getI18nManager()
    #print "RemoveFromBookmarks ", self
    prompt = i18n.getTranslation("_Are_you_sure_to_remove_{0}", (os.path.basename(self.getPath()),))
    if confirmDialog(prompt, i18n.getTranslation("_Catalog"),YES_NO,QUESTION)==YES:
      os.remove(self.getPath())
      self.getParent().reload()
        
  def actionPerformed(self, event):
    if self.__params == None:
      return
    i18n = ToolsLocator.getI18nManager()
    view = gvsig.currentView()
    if view == None:
      msgbox(i18n.getTranslation("_Need_an_active_view"))
      return
    try:
      parameters = self.__params
      factory = getProviderFactoryFromParams(parameters)
      if ( factory!=None and 
        factory.hasTabularSupport()==DataStoreProviderFactory.YES and 
        factory.hasVectorialSupport()!=DataStoreProviderFactory.YES and
        factory.hasRasterSupport()!=DataStoreProviderFactory.YES ):
        self.openAsTable()
        return
      mapContextManager = MapContextLocator.getMapContextManager()
      dataManager = DALLocator.getDataManager()
      dataStore = dataManager.openStore(parameters.getDataStoreName(), parameters)
      layer = mapContextManager.createLayer(dataStore.getName(), dataStore)
      view.getMapContext().getLayers().addLayer(layer)
      DisposeUtils.disposeQuietly(dataStore)
    except:
      logger("Can't add layer from bookmark (%s)" % self.__path, LOGGER_WARN, sys.exc_info()[1])
    

class Bookmarks(BookmarkFolder):
  def __init__(self, parent):
    BookmarkFolder.__init__(self, 
      parent, 
      getBookmarksFolder(), 
      ToolsLocator.getI18nManager().getTranslation("_Bookmarks"), 
      icon=getResource(__file__,"images","Favourite.png")
    )

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Create_group"),self.mnuCreateGroup))
    layer = gvsig.currentLayer()
    if layer != None:
      menu.add(createJMenuItem(i18n.getTranslation("_Add_layer_{0}_to_bookmarks", (layer.getName(),)),self.mnuAddCurrentLayerToBookmarks))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.mnuReload))
    return menu    

  def toString(self):
    i18n = ToolsLocator.getI18nManager()
    return i18n.getTranslation("_Bookmarks")
    
def main(*args):
    pass
