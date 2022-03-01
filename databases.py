# encoding: utf-8

import gvsig
from gvsig import getResource
from gvsig.commonsdialog import inputbox, msgbox, confirmDialog, QUESTION, WARNING, YES, YES_NO

from java.lang import Throwable
from javax.swing import JPopupMenu
from javax.swing import JSeparator
from javax.swing import JMenuItem

from org.gvsig.fmap.dal.store.jdbc import JDBCServerExplorerParameters
from org.gvsig.fmap.mapcontext import MapContextLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.dispose import DisposeUtils
from org.gvsig.tools.swing.api.windowmanager import WindowManager

from addons.Catalog.catalogutils import CatalogNode, CatalogSimpleNode, createJMenuItem, getDataManager, getIconFromParams
from addons.Catalog.catalogutils import openAsTable, openAsLayer, openAsForm, openSearchDialog, openAsParameters, addToBookmarks

from org.gvsig.fmap.dal.exception import ValidateDataParametersException

from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.table import TableManager

from javax.swing import SwingUtilities

from  addons.Catalog.cataloglocator import getCatalogManager

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
    dbExplorer = None
    try :
      dbExplorer = self.getServerExplorer()
      tablesParams = list()
      tablesParams.extend(dbExplorer.list())
      tablesParams.sort(lambda x,y : cmp(x.getTable().lower(),y.getTable().lower()))
      for tableParams in tablesParams:
        self._children.append(Table(self, tableParams))
    except Throwable:
      pass
    finally:
      DisposeUtils.disposeQuietly(dbExplorer)
    SwingUtilities.invokeLater(self.reload)
  
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.editParameters))
    menu.add(createJMenuItem(i18n.getTranslation("_Copy_URL"),self.copyURL))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Update"),self.update))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_database_connection"),self.removeDatabase))
    return menu    

  def copyURL(self, event=None):
    application = ApplicationLocator.getApplicationManager()
    url = self.__params.getDynValue("URL")
    if url.startswith("jdbc:h2:file:"):
      url = url.replace("jdbc:h2:file:","jdbc:h2:tcp://localhost:9123/")
    if url.startswith("jdbc:h2:split:"):
      url = url.replace("jdbc:h2:split:","jdbc:h2:tcp://localhost:9123/split:")
    application.putInClipboard(url)
    
  def removeDatabase(self, event=None):
    #print "RemoveFromBookmarks ", self
    i18n = ToolsLocator.getI18nManager()
    prompt = i18n.getTranslation("_Are_you_sure_to_remove_the_connection_{0}", (str(self),))
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
  
  def getParams(self):
    return self.__params
        
  def toString(self):
    return self.__params.getTable()
    
  def createPopup(self):
    i18n = ToolsLocator.getI18nManager()
    menu = JPopupMenu()
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_view"),self.actionPerformed, "view-layer-add"))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_table"),self.openAsTable, "layer-show-attributes-table"))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_as_form"),self.openAsForm, "layer-show-form"))
    menu.add(createJMenuItem(i18n.getTranslation("_Open_search_dialog"),self.openSearchDialog, "search-by-attributes-layer"))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Add_to_bookmarks"),self.addToBookmarks))
    menu.add(JSeparator())
    menu.add(createJMenuItem(i18n.getTranslation("_Remove_table"),self.removeTable))
    menu.add(createJMenuItem(i18n.getTranslation("_Edit_parameters"),self.editParameters))
    actions = getCatalogManager().getActions("DATABASE_TABLE", self.__params)
    if len(actions)>0 :
      menu.add(JSeparator())
      for action in actions:
        menu.add(JMenuItem(action))
    return menu    

  def removeTable(self, event=None):
    i18n = ToolsLocator.getI18nManager()
    prompt = i18n.getTranslation("_Are_you_sure_to_remove_table_{0}_from_the_database_{1}", (str(self),str(self.getParent())) )
    prompt += "\n\n" + i18n.getTranslation("_This_operation_will_delete_the_table_and_all_its_data")
    if confirmDialog(prompt, i18n.getTranslation("_Catalog"),YES_NO,QUESTION)==YES:
      dbExplorer = self.getParent().getServerExplorer()
      dbExplorer.remove(self.__params)
      self.getParent().update()
      DisposeUtils.disposeQuietly(dbExplorer)
      
  def openAsForm(self, *args):
    openAsForm(self.getParams())

  def openSearchDialog(self, *args):
    #menu.add(createJMenuItem(i18n.getTranslation("_Open_search_dialog"),self.openSearchDialog))
    openSearchDialog(self.getParams())
    
  def addToBookmarks(self, event=None):
    addToBookmarks(self.getRoot(), self.getParams(), self.getParams().getTable())

  def openAsTable(self, event):
    openAsTable(self.getParams())
  
  def editParameters(self, event):
    openAsParameters(self.getParams())
  
  def actionPerformed(self, event):
    openAsLayer(self.getParams())
    
def main(*args):
    pass
