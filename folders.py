# encoding: utf-8

import gvsig
from gvsig import getResource

import os
import ConfigParser

from java.io import File
from org.gvsig.tools import ToolsLocator
from org.gvsig.andami import PluginsLocator
from javax.swing import JPopupMenu
from javax.swing import JMenuItem

from addons.Catalog.catalogutils import CatalogSimpleNode, CatalogNode, getIconFromFile
from addons.Catalog.catalogutils import createJMenuItem, getDataManager, getProviderFactoryFromFile
from addons.Catalog.catalogutils import getDataFolder

from  addons.Catalog.cataloglocator import getCatalogManager

from org.gvsig.tools.swing.api.windowmanager import WindowManager
from org.gvsig.fmap.dal.swing import DALSwingLocator

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from org.gvsig.fmap.dal import DataStoreProviderFactory

from javax.swing import JSeparator

from org.gvsig.tools.util import ToolsUtilLocator

from gvsig.commonsdialog import msgbox
from org.gvsig.fmap.dal.exception import ValidateDataParametersException

from gvsig.commonsdialog import openFolderDialog

from gvsig.commonsdialog import inputbox
from gvsig.commonsdialog import QUESTION

from gvsig import logger
from gvsig import LOGGER_WARN
import sys

def getFoldersFolder():
  f = os.path.join(getDataFolder(),"folders")
  if not os.path.exists(f):
    os.mkdir(f)
  return f

class Folders(CatalogNode):
  def __init__(self, parent):
    CatalogNode.__init__(self,parent)
    self.add(HomeFolder(self))

    foldersManager = ToolsLocator.getFoldersManager()
    dataFolder = foldersManager.get("DataFolder")
    if dataFolder != None:
      self.add(DataFolderFolder(self,dataFolder.getAbsolutePath()))

    ls = os.listdir(getFoldersFolder())
    for fname in ls:
      pathname = os.path.join(getFoldersFolder(),fname)
      if fname[0] == ".":
        continue
      if fname.endswith(".linkfile"):
        self.add(LinkedFolder(self,pathname))
      
    
  def toString(self):
    i18n = ToolsLocator.getI18nManager()
    return i18n.getTranslation("_Folders")

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Add_folder_to_catalog"),self.addFolder))
    return menu    

  def addFolder(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    target = openFolderDialog(i18n.getTranslation("_Select_a_folder_to_add_to_catalog"))
    if target==None:
      return
    target = target[0]
    i18n = ToolsLocator.getI18nManager()
    name = os.path.basename(target)
    pathname = None
    prompt = i18n.getTranslation("_Folder_name")
    while pathname==None or os.path.exists(pathname):
      name = inputbox(prompt, i18n.getTranslation("_Catalog"), QUESTION, initialValue=name)
      if name in ("", None):
        return
      prompt = i18n.getTranslation("_Folder_name_already_exist_entry_another_name")
      pathname = os.path.join(getFoldersFolder(),name) + ".linkfile"
    config = ConfigParser.ConfigParser()
    config.add_section('FolderLink')
    config.set("FolderLink","target", target)
    with open(pathname, 'wb') as configfile:
      config.write(configfile)
    self.add(LinkedFolder(self,pathname))

class FolderNode(CatalogSimpleNode):
  def __init__(self, parent, path, label = None, icon = None):
    CatalogSimpleNode.__init__(self, parent, icon)
    self.__path = path
    if label == None:
      self.__label = os.path.basename(self.__path)
    else:
      self.__label = label
    self.__files = list()
    try:
      ls = os.listdir(self.__path)
      lsdirs = list()
      lsfiles = list()
      for f in ls:
        x = os.path.join(self.__path,f)
        if f[0]!=".":
          if os.path.isdir(x):
            lsdirs.append(x)
          else:
            lsfiles.append(x)
      lsdirs.sort(key=lambda s: s.lower())
      lsfiles.sort(key=lambda s: s.lower())
      self.__files.extend(lsdirs)
      self.__files.extend(lsfiles)
    except:
      logger("Can't get file list from '%s'" % self.__path,LOGGER_WARN, sys.exc_info()[1])
      
  def toString(self):
    return  unicode(self.__label, 'utf-8') 

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Open_in_filesystem_explorer"),self.openInFilesystemBrowser))
    return menu    

  def openInFilesystemBrowser(self,event=None):
    f = File(self.__path)
    desktop = ToolsUtilLocator.getToolsUtilManager().createDesktopOpen()
    desktop.open(f)
      
  def children(self):
    # Returns the children of the receiver as an Enumeration.
    return enumerate(self.__files)
    
  def getAllowsChildren(self):
    # Returns true if the receiver allows children.
    return True

  def getChildAt(self, childIndex):
    # Returns the child TreeNode at index childIndex.
    fname = os.path.join(self.__path,self.__files[childIndex])
    try:
      if os.path.isdir(fname):
        return FolderNode(self,fname)
      return FileNode(self,fname)
    except:
      return BrokenNode(self,fname)
      
  def getChildCount(self):
    # Returns the number of children TreeNodes the receiver contains.
    x = len(self.__files)
    #print ">>> getChildCount ", x
    return x

  def getIndex(self, node):
    # Returns the index of node in the receivers children.
    index = 0
    for x in self.__files:
      if node == x:
        return index
      index += 1
    return -1
     
  def isLeaf(self):
    # Returns true if the receiver is a leaf.
    return False

class FileNode(CatalogSimpleNode):
  def __init__(self, parent, path, label = None):
    CatalogSimpleNode.__init__(self, parent, icon=getIconFromFile(path))
    self.__path = path
    if label == None:
      self.__label = os.path.basename(self.__path)
    else:
      self.__label = label
    self.__params = None

  def toString(self):
    return  unicode(self.__label, 'utf-8') 

  def getParams(self):
    if self.__params == None:
      factory = getProviderFactoryFromFile(self.__path)
      if factory==None:
        return
      self.__params = factory.createParameters()
      self.__params.setFile(File(self.__path))
    return self.__params
    
  def createPopup(self):
    if self.getIcon()==None:
      return
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    factory = getProviderFactoryFromFile(self.__path)
    if factory!=None : 
      if (factory.hasVectorialSupport()!=DataStoreProviderFactory.NO or
        factory.hasRasterSupport()!=DataStoreProviderFactory.NO ):
        menu.add(createJMenuItem(i18n.getTranslation("_Add_to_view"),self.actionPerformed))
      if factory.hasTabularSupport()==DataStoreProviderFactory.YES:
        menu.add(createJMenuItem(i18n.getTranslation("_Open_as_table"),self.openAsTable))
        menu.add(createJMenuItem(i18n.getTranslation("_Open_as_form"),self.openAsForm))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_bookmarks"),self.addToBookmarks))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.mnuEditParameters))
    actions = getCatalogManager().getActions("FOLDERS_FILE", self.__params)
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

  def addToBookmarks(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    bookmarks = self.getRoot().getBookmarks()
    name = os.path.basename(self.__path)
    try:
      self.getParams().validate()
    except ValidateDataParametersException, ex:
      msgbox(i18n.getTranslation("_It_is_not_possible_to_add_the_recurse_to_the_markers_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
      return
    bookmarks.addParamsToBookmarks(name,self.getParams())
    
  def mnuEditParameters(self, event=None):
    manager = DALSwingLocator.getDataStoreParametersPanelManager()
    panel = manager.createDataStoreParametersPanel(self.getParams())
    manager.showPropertiesDialog(self.getParams(), panel)

  def openAsTable(self, event=None):
    factory = getProviderFactoryFromFile(self.__path)
    if factory==None or factory.hasTabularSupport()!=DataStoreProviderFactory.YES:
      return
    store = getDataManager().openStore(factory.getName(), self.getParams())
    projectManager = ApplicationLocator.getManager().getProjectManager()
    tableDoc = projectManager.createDocument(TableManager.TYPENAME)
    tableDoc.setStore(store)
    tableDoc.setName(str(self))
    projectManager.getCurrentProject().addDocument(tableDoc)
    ApplicationLocator.getManager().getUIManager().addWindow(tableDoc.getMainWindow())
  
  def actionPerformed(self, event=None):
    if self.getIcon()==None:
      return
    factory = getProviderFactoryFromFile(self.__path)
    if ( factory!=None and 
      factory.hasTabularSupport()==DataStoreProviderFactory.YES and 
      factory.hasVectorialSupport()!=DataStoreProviderFactory.YES and
      factory.hasRasterSupport()!=DataStoreProviderFactory.YES ):
      self.openAsTable()
      return
    listfiles = (File(self.__path),)
    actions = PluginsLocator.getActionInfoManager()
    addlayer = actions.getAction("view-layer-add")
    addlayer.execute((listfiles,))

class HomeFolder(FolderNode):
  def __init__(self, parent):
    FolderNode.__init__(self, parent, 
      os.path.expanduser('~'), 
      ToolsLocator.getI18nManager().getTranslation("_User_folder"),
      icon=getResource(__file__,"images","Home.png")
    ) 
      
class DataFolderFolder(FolderNode):
  def __init__(self, parent, path):
    FolderNode.__init__(self, parent, path, 
      ToolsLocator.getI18nManager().getTranslation("_Data_folder"),
      icon=getResource(__file__,"images","DataFolder.png")
    )

class BrokenNode(CatalogSimpleNode):
  def __init__(self, parent, path):
    CatalogSimpleNode.__init__(self, parent, icon=getResource(__file__,"images","FolderClosedRemoved.png"))
    self.__path = path
    self.__label = os.path.basename(self.__path)

  def toString(self):
    return  unicode(self.__label, 'utf-8') 

class LinkedFolder(FolderNode):
  def __init__(self, parent, linkfile):
    FolderNode.__init__(*self.__buildFolderNodeParams(parent,linkfile))
    self.__linkfile = linkfile

  def __buildFolderNodeParams(self, parent, linkfile):
    configfile = ConfigParser.ConfigParser()
    configfile.read(linkfile)
    target = configfile.get("FolderLink","target")
    return (self, parent, target)
    
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Open_in_filesystem_explorer"),self.openInFilesystemBrowser))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_folder_from_catalog"),self.removeLink))
    return menu    

  def removeLink(self, event=None):
    os.remove(self.__linkfile)
    self.getParent().remove(self)
    
def main(*args):
    pass
