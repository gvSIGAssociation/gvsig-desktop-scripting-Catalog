# encoding: utf-8

import gvsig

from gvsig.uselib import use_plugin
use_plugin("org.gvsig.geodb.app.mainplugin")

import os
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
from org.gvsig.tools.swing.api.windowmanager import WindowManager, WindowManager_v2

from org.gvsig.expressionevaluator import ExpressionUtils
from org.gvsig.expressionevaluator.swing import ExpressionEvaluatorSwingLocator

from addons.Catalog import catalogutils
from addons.Catalog.catalogutils import CatalogNode, CatalogSimpleNode, createJMenuItem, getDataManager, getIconFromParams

from addons.Catalog.catalogutils import openAsTable, openAsLayer, openAsForm, openSearchDialog, openAsParameters, addToBookmarks, getResourceOfTable, putResourceOfTable

from org.gvsig.fmap.dal.exception import ValidateDataParametersException

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from javax.swing import SwingUtilities
from org.gvsig.andami import PluginsLocator

from  addons.Catalog.cataloglocator import getCatalogManager
from  addons.Catalog.repository.createrepo import CreateRepository

from org.gvsig.tools.observer import Observer
from org.gvsig.geodb.databaseworkspace import RepositoryAddTablePanel
from org.gvsig.fmap.dal.DatabaseWorkspaceManager import TABLE_REPOSITORY_NAME, TABLE_RESOURCES_NAME, TABLE_CONFIGURATION_NAME

try:
  from addons.ScriptingComposerTools.abeille.abeille import launchAbeille
except:
  launchAbeille = None

DEFAULT_REPOSITORY_GROUP_NAME="Tables"

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
    for n in xrange(1,5):
      try:
        for subrepo in repo.getSubrepositories():
          self._children.append(SubstoresRepository(self, subrepo.getLabel(), subrepo))
        break
      except:
        pass
    SwingUtilities.invokeLater(self.reload)
    
  def toString(self):
    i18n = ToolsLocator.getI18nManager()
    return i18n.getTranslation("_Repositories")

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("Conectar a repositorio"),self.conectarARepositorio))
    menu.add(createJMenuItem(i18n.getTranslation("Crear repositorio"),self.crearRepositorio))
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    return menu    

  def update(self, event=None):
    SwingUtilities.invokeLater(self.__load)
    
  def conectarARepositorio(self, event=None):
    actionManager = PluginsLocator.getActionInfoManager()
    action = actionManager.getAction("database-workspace-connect").execute()
     
  def crearRepositorio(self, event=None):
      x = CreateRepository()
      x.showWindow("Crear repositorio")
    
class SubstoresRepository(CatalogNode):
  def __init__(self, parent, label, repo):
    CatalogNode.__init__(self, parent, icon=getResource(__file__,"images","StoresRepository.png"))
    #print "### SubstoresRepository.__init__", repr(label)
    self.__label = label
    self.__repo = repo

  def _getChildren(self):
    #print "### SubstoresRepository._getChildren"
    if self._children == None:
      self.__load()
    return self._children
    
  def __load(self):
    #print "### SubstoresRepository.__load"
    self._children = list()
    for i in xrange(1,5):
      try :
        #config = catalogutils.getConfig()
        #sectionName = "StoreRepository_" + self.__repo.getID()
        #hidde_pattern = None
        #if config.has_section(sectionName):
        #  if config.has_option(sectionName, "hidde_pattern"):
        #    hidde_pattern = config.get(sectionName, "hidde_pattern")
        #    if hidde_pattern.strip() == "":
        #      hidde_pattern = None

        #print "### SubstoresRepository: hidde_pattern:%s " % (hidde_pattern)
        groups = set()
        names = self.__repo.keySet()
        for name in names:
          group = self.__repo.getProperty(name+".catalog.group")
          #print "### SubstoresRepository: name:%s  group:%s" % (name,group)
          if group in (None,""):
            groups.add(DEFAULT_REPOSITORY_GROUP_NAME)
            continue
          groups.add(group)
        names = list()
        names.extend(groups)
        names.sort()
        #print "### SubstoresRepository: groups:%s" % (names)
        for name in names:
          x = Group(self, name, self.__repo)
          self._children.append(x)
        break
      except Throwable as e:
        e.printStackTrace()
        pass
    SwingUtilities.invokeLater(self.reload)
  
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    dataManager = getDataManager()
    repoID = self.__repo.getID()
    isdbrepo = dataManager.getDatabaseWorkspace(repoID)!=None
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    menu.add(createJMenuItem(i18n.getTranslation(u"Añadir tablas al repositorio"),self.addTablesToRepository, enabled=isdbrepo))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation(u"Desconectar del reposotorio"),self.disconnectWorkspace, enabled=isdbrepo))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation(u"Ver la tabla de recursos"),lambda e: self.__showTable(TABLE_RESOURCES_NAME), enabled=isdbrepo))
    menu.add(createJMenuItem(i18n.getTranslation(u"Ver la tabla de configuración"),lambda e: self.__showTable(TABLE_CONFIGURATION_NAME), enabled=isdbrepo))
    menu.add(createJMenuItem(i18n.getTranslation(u"Ver la tabla de contenidos"),lambda e: self.__showTable(TABLE_REPOSITORY_NAME), enabled=isdbrepo))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Hidde_entries"),self.getPatternToHiddeEntries))
    return menu    

  def disconnectWorkspace(self, *args):
    dataManager = getDataManager()
    repoID = self.__repo.getID()
    workspace = dataManager.getDatabaseWorkspace(repoID)
    if workspace!=None:
      workspace.disconnect()

  def __showTable(self, tablename):
    dataManager = getDataManager()
    workspace = dataManager.getDatabaseWorkspace(self.__repo.getID())
    serverExplorer = workspace.getServerExplorer()
    params = serverExplorer.get(tablename)
    #openAsTable(params)
    #openAsForm(params)
    openSearchDialog(params)
    
  def addTablesToRepository(self, *args):
    dataManager = getDataManager()
    workspace = dataManager.getDatabaseWorkspace(self.__repo.getID())
    winManager = ToolsSwingLocator.getWindowManager()
    panel = RepositoryAddTablePanel()
    dialog = winManager.createDialog(
                panel,
                u"Añadir tablas al repositorio (%s)" %  self.__repo.getID(),
                None,
                winManager.BUTTONS_OK_CANCEL
    )
    dialog.addActionListener(lambda e: self.__doAddTablesToRepository(workspace, dialog, panel))
    dialog.show(winManager.MODE.WINDOW)

  def __doAddTablesToRepository(self, workspace, dialog, panel):
    if  dialog.getAction() == WindowManager_v2.BUTTON_OK:
      for x in panel.getDataStoreParameters():
        if x == None:
          continue
        if not workspace.writeStoresRepositoryEntry(x.getLabel(), x.getValue()):
          msgbox(u"No se ha podido añadir al repositorio la tabla '%s'" % x.getLabel())
    workspace.connect() # Para forzar a recargar las tablas del repositorio.
    SwingUtilities.invokeLater(self.reload)
 
  def getPatternToHiddeEntries(self, *args):
    i18n = ToolsLocator.getI18nManager()
    config = catalogutils.getConfig()
    sectionName = "StoreRepository_" + self.__repo.getID()
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

  def update(self, event=None):
    SwingUtilities.invokeLater(self.__load)
    
  def toString(self):
    #print "### SubstoresRepository.toString ", repr(self.__label)
    return  self.__label

def getGroupIcon(label):
  if label in ("",None):
    label = DEFAULT_REPOSITORY_GROUP_NAME.lower()
  label = label.lower()
  r = getResource(__file__,"images",label +".png")
  if not os.path.isfile(r):
    r = getResource(__file__,"images","tables.png")
  return r
  
class Group(CatalogNode):
  def __init__(self, parent, label, repo):
    CatalogNode.__init__(self, parent, icon=getGroupIcon(label))
    self.__label = label
    self.__repo = repo
    #print "### Group.__init__", repr(self.__label)

  def _getChildren(self):
    #print "### Group._getChildren"
    if self._children == None:
      self.__load()
    return self._children
    
  def __load(self):
    #print "### Group.__load", repr(self.__label)
    self._children = list()
    for i in xrange(1,5):
      try :
        config = catalogutils.getConfig()
        sectionName = "StoreRepository_" + self.__repo.getID()
        hidde_pattern = None
        if config.has_section(sectionName):
          if config.has_option(sectionName, "hidde_pattern"):
            hidde_pattern = config.get(sectionName, "hidde_pattern")
            if hidde_pattern.strip() == "":
              hidde_pattern = None
     
        #print "### Group.__load, hidde_pattern =",repr(hidde_pattern)
        names0 = self.__repo.keySet()
        if names0 != None:
          names = list()
          names.extend(names0)
          names.sort()
          for name in names:
            #print "### Group.__load, name =",repr(name)
            if hidde_pattern!=None and fnmatch(name, hidde_pattern):
              #print "### Group.__load, pattern skip name =",repr(name)
              continue
            group = self.__repo.getProperty(name+".catalog.group")
            if group in (None,""):
              group = DEFAULT_REPOSITORY_GROUP_NAME
            if group != self.__label:
              #print "### Group.__load, group skip name =",repr(name)
              continue;
            label = self.__repo.getProperty(name+".label")
            if label in ("",None):
              label = name
            params = self.__repo.get(name)
            x = Table(self, label, params, self.__repo)
            self._children.append(x)
        break
      except Throwable as e:
        e.printStackTrace()
        pass
    SwingUtilities.invokeLater(self.reload)

  def update(self, event=None):
    SwingUtilities.invokeLater(self.__load)

  def toString(self):
    #print "### Group.toString", repr(self.__label)
    return  self.__label


class Table(CatalogSimpleNode):
  def __init__(self, parent, label, params, repo):
    CatalogSimpleNode.__init__(self, parent, icon=getIconFromParams(params))
    self.__label = label
    self.__params = params
    self.__repo = repo
    
  def getParams(self):
    return self.__params
            
  def toString(self):
    return  self.__label
    
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    dataManager = getDataManager()
    repoID = self.__repo.getID()
    isdbrepo = dataManager.getDatabaseWorkspace(repoID)!=None
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
    menu.add(createJMenuItem(i18n.getTranslation("_Open_editing_actions"),lambda e: self.__openScript("editsc",u"Editing actions: %s" %  self.getParams().getTable()), enabled=isdbrepo))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_form_actions"),lambda e: self.__openScript("jfrms",u"Form actions: %s" %  self.getParams().getTable()), enabled=isdbrepo))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_form_editor"),lambda e: self.__openFormEditor(), enabled=False))
    actions = getCatalogManager().getActions("STORES_REPOSITORY_TABLE", self.__params)
    if len(actions)>0 :
      menu.add(JSeparator())
      for action in actions:
        menu.add(JMenuItem(action))
    return menu    

  def __openScript(self, resourceName, title):
    resource = getResourceOfTable(self.getParams(), resourceName)
    if resource == None:
      script = ExpressionUtils.createScript(None, "%s_%s" % (self.getParams().getTable(),resourceName))
    else:
      script = ExpressionUtils.createScript(resource, "%s_%s" % (self.getParams().getTable(),resourceName))
    editor = ExpressionEvaluatorSwingLocator.getManager().createJScriptEditor(script)
    winManager = ToolsSwingLocator.getWindowManager()
    dialog = winManager.createDialog(
                editor,
                title,
                None,
                winManager.BUTTONS_APPLY_OK_CANCEL
    )
    editor.setScript(script)
    dialog.addActionListener(lambda e: self.__doUpdateScript(dialog, editor, resourceName))
    dialog.show(winManager.MODE.WINDOW)

  def __doUpdateScript(self, dialog, editor, resourceName):
    if  dialog.getAction()== WindowManager_v2.BUTTON_CANCEL:
      return
    putResourceOfTable(self.getParams(), resourceName, editor.getScript().getCode())
    
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
    openAsTable(self.getParams(), self.__label)
  
  def editParameters(self, event):
    openAsParameters(self.getParams())
  
  def addToView(self, event):
    openAsLayer(self.getParams(), self.__label)
    
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