# encoding: utf-8

import gvsig

from fnmatch import fnmatch

from gvsig import getResource
from gvsig.commonsdialog import inputbox, msgbox, confirmDialog, QUESTION, WARNING, YES, YES_NO

from java.lang import Throwable
from javax.swing import JPopupMenu
from javax.swing import JSeparator
from javax.swing import JMenuItem

from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.swing.api.windowmanager import WindowManager

from addons.Catalog import catalogutils
from addons.Catalog.catalogutils import CatalogNode, CatalogSimpleNode, createJMenuItem, getDataManager, getIconFromParams

from addons.Catalog.catalogutils import openAsTable, openAsLayer, openAsForm, openSearchDialog, openAsParameters, addToBookmarks

from org.gvsig.fmap.dal.exception import ValidateDataParametersException

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from javax.swing import SwingUtilities

from  addons.Catalog.cataloglocator import getCatalogManager

from org.gvsig.tools.observer import Observer

try:
  from addons.ScriptingComposerTools.abeille.abeille import launchAbeille
except:
  launchAbeille = None

class StoresRepositoryObserver(Observer):
  def __init__(self, node):
    Observer.__init__(self)
    self.__node = node

  def update(self, observable, notification):
    self.__node.update()
    
class StoresRepository(CatalogNode):
  def __init__(self, parent):
    CatalogNode.__init__(self,parent, icon=getResource(__file__,"images","StoresRepository.png"))
    dataManager = getDataManager()
    repo = dataManager.getStoresRepository()
    repo.addObserver(StoresRepositoryObserver(self))
    self.__load()
    
  def __load(self):
    self._children = list()
    dataManager = getDataManager()
    repo = dataManager.getStoresRepository()
    for subrepo in repo.getSubrepositories():
      self._children.append(SubstoresRepository(self, subrepo.getLabel(), subrepo))
    self.reload()
    
  def toString(self):
    i18n = ToolsLocator.getI18nManager()
    return i18n.getTranslation("_Repositories")

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    return menu    

  def update(self, event=None):
    SwingUtilities.invokeLater(self.__load)
    
    
class SubstoresRepository(CatalogNode):
  def __init__(self, parent, label, subrepo):
    CatalogNode.__init__(self, parent, icon=getResource(__file__,"images","StoresRepository.png"))
    self.__label = label
    self.subrepo = subrepo

  def _getChildren(self):
    #print "### SubstoresRepository._getChildren"
    if self._children == None:
      self.__load()
    return self._children
    
  def __load(self):
    #print "### SubstoresRepository.__load"
    self._children = list()
    try :
      config = catalogutils.getConfig()
      sectionName = "StoreRepository_" + self.subrepo.getID()
      hidde_pattern = None
      if config.has_section(sectionName):
        if config.has_option(sectionName, "hidde_pattern"):
          hidde_pattern = config.get(sectionName, "hidde_pattern")
          if hidde_pattern.strip() == "":
            hidde_pattern = None
        
      names0 = self.subrepo.keySet()
      if names0 != None:
        names = list()
        names.extend(names0)
        names.sort()
        for name in names:
          if hidde_pattern!=None and fnmatch(name, hidde_pattern):
            continue
          params = self.subrepo.get(name)
          self._children.append(Table(self, name, params))
    except Throwable:
      pass
    SwingUtilities.invokeLater(self.reload)
  
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    dataManager = getDataManager()
    repoID = self.subrepo.getID()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    menu.add(JSeparator())
    enableDisconnet = dataManager.getDatabaseWorkspace(repoID)!=None
    menu.add(createJMenuItem(i18n.getTranslation("_Disconnect_from_database_workspace"),self.disconnectWorkspace, enabled=enableDisconnet))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Add_resource"),self.addResource))
    menu.add(createJMenuItem(i18n.getTranslation("_Get_resource"),self.getResource))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Hidde_entries"),self.getPatternToHiddeEntries))
    return menu    

  def disconnectWorkspace(self, *args):
    dataManager = getDataManager()
    repoID = self.subrepo.getID()
    workspace = dataManager.getDatabaseWorkspace(repoID)
    if workspace!=None:
      workspace.disconnect()
    
  def getPatternToHiddeEntries(self, *args):
    i18n = ToolsLocator.getI18nManager()
    config = catalogutils.getConfig()
    sectionName = "StoreRepository_" + self.subrepo.getID()
    hidde_pattern = ""
    if config.has_section(sectionName):
      if config.has_option(sectionName, "hidde_pattern"):
        hidde_pattern = config.get(sectionName, "hidde_pattern")
    s = inputbox(
      i18n.getTranslation("_Enter_the_pattern_you_will_use_to_hide_the_entries_you_want_you_can_use_arterisks_and_questions"), 
      i18n.getTranslation("_Pattern_to_hide_entries"), 
      initialValue=hidde_pattern
    )
    if s==None:
      return # User cancel
    if not config.has_section(sectionName):
      config.add_section(sectionName)
    config.set(sectionName,"hidde_pattern",s.strip())
    catalogutils.saveConfig(config)
    self.update()
    
  def addResource(self, *args):
    msgbox("Add rsources to database not yet implemented")

  def getResource(self, *args):
    msgbox("Get rsources to database not yet implemented")
    
  def update(self, event=None):
    SwingUtilities.invokeLater(self.__load)
    
  def toString(self):
    return  self.__label

class Table(CatalogSimpleNode):
  def __init__(self, parent, label, params):
    CatalogSimpleNode.__init__(self, parent, icon=getIconFromParams(params))
    self.__label = label
    self.__params = params
  
  def getParams(self):
    return self.__params
            
  def toString(self):
    return  self.__label
    
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_view"),self.addToView, "view-layer-add"))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_table"),self.actionPerformed, "layer-show-attributes-table"))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_form"),self.openAsForm, "layer-show-form"))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_search_dialog"),self.openSearchDialog, "search-by-attributes-layer"))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_bookmarks"),self.addToBookmarks))
    menu.add(createJMenuItem(i18n.getTranslation("_Copy_URL"),self.copyURL))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_View_parameters"),self.editParameters))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Add_resource"),self.addResource))
    menu.add(createJMenuItem(i18n.getTranslation("_Get_resource"),self.getResource))
    if launchAbeille!=None:
      menu.add(JSeparator())
      menu.add(createJMenuItem(i18n.getTranslation("_Open_form_editor"),self.openFormEditor))
    actions = getCatalogManager().getActions("STORES_REPOSITORY_TABLE", self.__params)
    if len(actions)>0 :
      menu.add(JSeparator())
      for action in actions:
        menu.add(JMenuItem(action))
    return menu    


  def openFormEditor(self, *args):
    if launchAbeille==None:
      return
    msgbox("Show form editor for database resources not yet implemented")
    
    # Si el recurso existe en la BBDD sacarlo a una carpeta temporal
    # si no existe crear en la carpeta temporal un jfrm sin campos
    # asignar a folder la carpeta temporal donde se ha dejado el jfrm
    
    #folder = ...
    #thread.start_new_thread(launchAbeille,(folder,))
    
  def addResource(self, *args):
    msgbox("Add rsources to database not yet implemented")
    
  def getResource(self, *args):
    msgbox("Get rsources to database not yet implemented")
    
  def copyURL(self, event=None):
    application = ApplicationLocator.getApplicationManager()
    url = self.__params.getDynValue("URL")
    if url.startswith("jdbc:h2:file:"):
      url = url.replace("jdbc:h2:file:","jdbc:h2:tcp://localhost:9123/")
    application.putInClipboard(url)
 
  def openAsForm(self, *args):
    openAsForm(self.getParams())

  def openSearchDialog(self, *args):
    #menu.add(createJMenuItem(i18n.getTranslation("_Open_search_dialog"),self.openSearchDialog))
    openSearchDialog(self.getParams())
    
  def addToBookmarks(self, event=None):
    addToBookmarks(self.getRoot(), self.getParams(), self.getParams().getTable())

  def actionPerformed(self, event):
    openAsTable(self.getParams())
  
  def editParameters(self, event):
    openAsParameters(self.getParams())
  
  def addToView(self, event):
    openAsLayer(self.getParams())
    
def main(*args):
  pass
  """
    dataManager = getDataManager()
    repo = dataManager.getStoresRepository()
    for subrepo in repo.getSubrepositories():
      print subrepo.getID(), subrepo.getLabel()
      ks = subrepo.keySet()
      print ks
  """