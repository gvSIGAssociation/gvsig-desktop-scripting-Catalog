# encoding: utf-8

import gvsig
from gvsig import getResource
from gvsig.commonsdialog import inputbox, msgbox, confirmDialog, QUESTION, WARNING, YES, YES_NO

from java.lang import Throwable
from javax.swing import JPopupMenu
from javax.swing import JSeparator

from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.tools import ToolsLocator

from addons.Catalog.catalogutils import CatalogNode, CatalogSimpleNode, createJMenuItem, getDataManager, getIconFromParams

from org.gvsig.fmap.dal.exception import ValidateDataParametersException

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from javax.swing import SwingUtilities


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
      names = self.subrepo.keySet()
      if names != None:
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
    
  def toString(self):
    return  self.__label
    
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_table"),self.actionPerformed))
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_bookmarks"),self.addToBookmarks))
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_view"),self.addToView))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_View_parameters"),self.editParameters))
    return menu    

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
      ks = subrepo.keySet();
      print ks
