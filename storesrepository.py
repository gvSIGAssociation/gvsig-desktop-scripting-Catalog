# encoding: utf-8

import gvsig
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

from addons.Catalog.catalogutils import CatalogNode, CatalogSimpleNode, createJMenuItem, getDataManager, getIconFromParams

from org.gvsig.fmap.dal.exception import ValidateDataParametersException

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from javax.swing import SwingUtilities

from  addons.Catalog.cataloglocator import getCatalogManager

try:
  from addons.ScriptingComposerTools.abeille.abeille import launchAbeille
except:
  launchAbeille = None
    
class StoresRepository(CatalogNode):
  def __init__(self, parent):
    CatalogNode.__init__(self,parent, icon=getResource(__file__,"images","StoresRepository.png"))
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
      names0 = self.subrepo.keySet()
      if names0 != None:
        names = list()
        names.extend(names0)
        names.sort()
        for name in names:
          params = self.subrepo.get(name)
          self._children.append(Table(self, name, params))
    except Throwable:
      pass
    SwingUtilities.invokeLater(self.reload)
  
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    return menu    

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
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_view"),self.addToView))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_table"),self.actionPerformed))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_form"),self.openAsForm))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_search_dialog"),self.openSearchDialog))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_bookmarks"),self.addToBookmarks))
    menu.add(createJMenuItem(i18n.getTranslation("_Copy_URL"),self.copyURL))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_View_parameters"),self.editParameters))
    if launchAbeille!=None:
      menu.add(JSeparator())
      menu.add(createJMenuItem(i18n.getTranslation("_Open_form_editor"),self.openFormEditor))
      menu.add(createJMenuItem(i18n.getTranslation("_Upload_resource"),self.uploadResource))
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
    
  def uploadResource(self, *args):
    if launchAbeille==None:
      return
    msgbox("Upload rsources to database not yet implemented")

    # Abrir el selector de fichero en la carpeta temporal de formularios
    # y el fichero jfrm que corresponda a la tabla seleccionada.
    # Una vez seleccionado subir el recurso a la BBDD.
    
  def copyURL(self, event=None):
    application = ApplicationLocator.getApplicationManager()
    url = self.__params.getDynValue("URL")
    if url.startswith("jdbc:h2:file:"):
      url = url.replace("jdbc:h2:file:","jdbc:h2:tcp://localhost:9123/")
    application.putInClipboard(url)
 
  def openAsForm(self, *args):
    i18n = ToolsLocator.getI18nManager()
    try:
      self.getParams().validate()
    except ValidateDataParametersException, ex:
      msgbox(i18n.getTranslation("_It_is_not_possible_to_open_the_recurse_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
      return
    store = getDataManager().openStore(self.__params.getDataStoreName(), self.__params)
    swingManager = DALSwingLocator.getSwingManager()
    form = swingManager.createJFeaturesForm(store)
    form.showForm(WindowManager.MODE.WINDOW)

  def openSearchDialog(self, *args):
    #menu.add(createJMenuItem(i18n.getTranslation("_Open_search_dialog"),self.openSearchDialog))
    i18n = ToolsLocator.getI18nManager()
    try:
      self.getParams().validate()
    except ValidateDataParametersException, ex:
      msgbox(i18n.getTranslation("_It_is_not_possible_to_open_the_recurse_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
      return
    swingManager = DALSwingLocator.getSwingManager()
    winmgr = ToolsSwingLocator.getWindowManager()
    store = getDataManager().openStore(self.__params.getDataStoreName(), self.__params)
    panel = swingManager.createFeatureStoreSearchPanel(store)
    winmgr.showWindow(
            panel.asJComponent(), 
            i18n.getTranslation("Search: ") + store.getName(), 
            WindowManager.MODE.WINDOW
    )
    
  def addToBookmarks(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    bookmarks = self.getRoot().getBookmarks()
    name = self.__params.getTable()
    try:
      self.__params.validate()
    except ValidateDataParametersException, ex:
      msgbox(i18n.getTranslation("_It_is_not_possible_to_add_the_recuse_to_the_markers_Try_to_edit_the_parameters_first_and_fill_in_the_required_values"+"\n\n"+ex.getLocalizedMessageStack()))
      return
    bookmarks.addParamsToBookmarks(name,self.__params)

  def actionPerformed(self, event):
    i18n = ToolsLocator.getI18nManager()
    try:
      self.getParams().validate()
    except ValidateDataParametersException, ex:
      msgbox(i18n.getTranslation("_It_is_not_possible_to_open_the_recurse_Try_to_edit_the_parameters_first_and_fill_in_the_required_values")+"\n\n"+ex.getLocalizedMessageStack())
      return
    store = getDataManager().openStore(self.__params.getDataStoreName(), self.__params)
    projectManager = ApplicationLocator.getManager().getProjectManager()
    tableDoc = projectManager.createDocument(TableManager.TYPENAME)
    tableDoc.setStore(store)
    tableDoc.setName(str(self))
    projectManager.getCurrentProject().addDocument(tableDoc)
    ApplicationLocator.getManager().getUIManager().addWindow(tableDoc.getMainWindow())
  
  def editParameters(self, event):
    manager = DALSwingLocator.getDataStoreParametersPanelManager()
    panel = manager.createDataStoreParametersPanel(self.__params)
    manager.showPropertiesDialog(self.__params, panel)
  
  def addToView(self, event):
    layer = MapContextLocator.getMapContextManager().createLayer(self.__params.getTable(), self.__params)
    gvsig.currentView().getMainWindow().getMapControl().addLayer(layer)
    
def main(*args):
    dataManager = getDataManager()
    repo = dataManager.getStoresRepository()
    for subrepo in repo.getSubrepositories():
      print subrepo.getID(), subrepo.getLabel()
      ks = subrepo.keySet()
      print ks
