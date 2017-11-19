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

class Databases(CatalogNode):
  def __init__(self, parent):
    CatalogNode.__init__(self,parent, icon=getResource(__file__,"images","Database.png"))
    self._load()
    
  def _load(self):
    del self[:]
    dataManager = getDataManager()
    pool = dataManager.getDataServerExplorerPool()
    for entry in pool:
      params = entry.getExplorerParameters()
      if isinstance(params,JDBCServerExplorerParameters) :
        self.add(Database(self, entry.getName(), params))
    self.reload()
    
  def toString(self):
    i18n = ToolsLocator.getI18nManager()
    return i18n.getTranslation("_Databases")

  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Add_database"),self.mnuAddDatabase))
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.mnuRefresh))
    return menu    

  def mnuAddDatabase(self, event):
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
      self._load()
  
  def mnuRefresh(self, event):
    self._load()
    
    
class Database(CatalogNode):
  def __init__(self, parent, label, params):
    CatalogNode.__init__(self, parent, icon=getIconFromParams(params))
    self.__label = label
    self.__params = params
    self.__load()
    
  def __load(self):
    del self[:]
    try :
      dbExplorer = getDataManager().openServerExplorer(self.__params.getExplorerName(), self.__params)
      tablesParams = list()
      tablesParams.extend(dbExplorer.list())
      tablesParams.sort(lambda x,y : cmp(x.getTable().lower(),y.getTable().lower()))
      for tableParams in tablesParams:
        self.add(Table(self, tableParams))
    except Throwable:
      pass
    self.reload()
  
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.mnuEditParameters))
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.mnuRefresh))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_database"),self.mnuRemoveDatabase))
    return menu    

  def mnuRemoveDatabase(self, event):
    #print "RemoveFromBookmarks ", self
    i18n = ToolsLocator.getI18nManager()
    prompt = i18n.getTranslation("_Are_you_sure_to_remove_{0}", (str(self),))
    if confirmDialog(prompt, i18n.getTranslation("_Catalog"),YES_NO,QUESTION)==YES:
      dataManager = getDataManager()
      pool = dataManager.getDataServerExplorerPool()
      pool.remove(str(self))
      self.getParent()._load()
        
  def mnuRefresh(self, event):
    self.__load()
    
  def mnuEditParameters(self, event):
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
    menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.mnuEditParameters))
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
    
  def openAsTable(self, event=None):
    store = getDataManager().openStore(self.__params.getDataStoreName(), self.__params)
    projectManager = ApplicationLocator.getManager().getProjectManager()
    tableDoc = projectManager.createDocument(TableManager.TYPENAME)
    tableDoc.setStore(store)
    projectManager.getCurrentProject().addDocument(tableDoc)
    ApplicationLocator.getManager().getUIManager().addWindow(tableDoc.getMainWindow())
  
  def mnuEditParameters(self, event):
    manager = DALSwingLocator.getDataStoreParametersPanelManager()
    panel = manager.createDataStoreParametersPanel(self.__params)
    manager.showPropertiesDialog(self.__params, panel)
  
  def actionPerformed(self, event):
    layer = MapContextLocator.getMapContextManager().createLayer(self.__params.getTable(), self.__params)
    gvsig.currentView().getMapContext().getLayers().addLayer(layer)
    
def main(*args):
    pass
