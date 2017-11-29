# encoding: utf-8

import gvsig
from gvsig import getResource
from gvsig.commonsdialog import inputbox, msgbox, confirmDialog, QUESTION, WARNING, YES, YES_NO

from java.lang import Throwable
from javax.swing import JPopupMenu
from javax.swing import JSeparator

from org.gvsig.fmap.dal.store.jdbc import JDBCServerExplorerParameters
from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.tools import ToolsLocator

from addons.Catalog.catalogutils import CatalogNode, CatalogSimpleNode, createJMenuItem, getDataManager, getIconFromParams

from org.gvsig.fmap.dal.exception import ValidateDataParametersException

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from javax.swing import SwingUtilities

class Databases(CatalogNode):
  def __init__(self, parent):
    CatalogNode.__init__(self,parent, icon=getResource(__file__,"images","Database.png"))
    self.__load()
    
  def __load(self):
    self._children = list()
    dataManager = getDataManager()
    pool = dataManager.getDataServerExplorerPool()
    for entry in pool:
      params = entry.getExplorerParameters()
      if isinstance(params,JDBCServerExplorerParameters) :
        self._children.append(Database(self, entry.getName(), params))
    self.reload()
    
  def toString(self):
    i18n = ToolsLocator.getI18nManager()
    return i18n.getTranslation("_Databases")

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Add_database"),self.addDatabase))
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    return menu    

  def addDatabase(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    manager = DALSwingLocator.getSwingManager()
    panel = manager.createJDBCConnectionPanel()
    winmgr = ToolsSwingLocator.getWindowManager()
    dialog = winmgr.createDialog(
      panel.asJComponent(),
      i18n.getTranslation("_Catalog"),
      i18n.getTranslation("_Database_connections"),
      winmgr.BUTTONS_OK_CANCEL
    )
    dialog.show(winmgr.MODE.DIALOG)
    if dialog.getAction()==winmgr.BUTTON_OK:
      panel.getServerExplorerParameters() # Los añade al pool
      self.__load()
  
  def update(self, event=None):
    SwingUtilities.invokeLater(self.__load)
    
    
class Database(CatalogNode):
  def __init__(self, parent, label, params):
    CatalogNode.__init__(self, parent, icon=getIconFromParams(params))
    self.__label = label
    self.__params = params

  def getServerExplorer(self):
    dbExplorer = getDataManager().openServerExplorer(self.__params.getExplorerName(), self.__params)
    return dbExplorer

  def _getChildren(self):
    #print "### Database._getChildren"
    if self._children == None:
      self.__load()
    return self._children
    
  def __load(self):
    #print "### Database.__load"
    self._children = list()
    try :
      dbExplorer = self.getServerExplorer()
      tablesParams = list()
      tablesParams.extend(dbExplorer.list())
      tablesParams.sort(lambda x,y : cmp(x.getTable().lower(),y.getTable().lower()))
      for tableParams in tablesParams:
        self._children.append(Table(self, tableParams))
    except Throwable:
      pass
    SwingUtilities.invokeLater(self.reload)
  
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.editParameters))
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_database"),self.removeDatabase))
    return menu    

  def removeDatabase(self, event=None):
    #print "RemoveFromBookmarks ", self
    i18n = ToolsLocator.getI18nManager()
    prompt = i18n.getTranslation("_Are_you_sure_to_remove_{0}", (str(self),))
    if confirmDialog(prompt, i18n.getTranslation("_Catalog"),YES_NO,QUESTION)==YES:
      dataManager = getDataManager()
      pool = dataManager.getDataServerExplorerPool()
      pool.remove(str(self))
      self.getParent().update()
        
  def update(self, event=None):
    SwingUtilities.invokeLater(self.__load)
    
  def editParameters(self, event=None):
    manager = DALSwingLocator.getDataStoreParametersPanelManager()
    panel = manager.createDataStoreParametersPanel(self.__params)
    manager.showPropertiesDialog(self.__params, panel)
    
  def toString(self):
    return  self.__label

class Table(CatalogSimpleNode):
  def __init__(self, parent, params):
    CatalogSimpleNode.__init__(self, parent)
    self.__params = params
    
  def toString(self):
    return self.__params.getTable()
    
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_view"),self.actionPerformed))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_table"),self.openAsTable))
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_bookmarks"),self.addToBookmarks))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_table"),self.removeTable))
    menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.editParameters))
    return menu    

  def addToBookmarks(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    treePath = self.getTreePath()
    bookmarks = treePath[0].getBookmarks()
    name = self.__params.getTable()
    try:
      self.__params.validate()
    except ValidateDataParametersException, ex:
      msgbox(i18n.getTranslation("_It_is_not_possible_to_add_the_recuse_to_the_markers_Try_to_edit_the_parameters_first_and_fill_in_the_required_values"+"\n\n"+ex.getLocalizedMessageStack()))
      return
    bookmarks.addParamsToBookmarks(name,self.__params)

  def removeTable(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    prompt = i18n.getTranslation("_Are_you_sure_to_remove_table_{0}_from_the_database_{1}", (str(self),str(self.getParent())) )
    if confirmDialog(prompt, i18n.getTranslation("_Catalog"),YES_NO,QUESTION)==YES:
      dbExplorer = self.getParent().getServerExplorer()
      dbExplorer.remove(self.__params)
      self.getParent().update()
      
  def openAsTable(self, event=None):
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
  
  def actionPerformed(self, event):
    layer = MapContextLocator.getMapContextManager().createLayer(self.__params.getTable(), self.__params)
    gvsig.currentView().getMainWindow().getMapControl().addLayer(layer)
    
def main(*args):
    pass
