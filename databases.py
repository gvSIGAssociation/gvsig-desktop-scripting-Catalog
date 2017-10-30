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

from catalogutils import CatalogNode, CatalogSimpleNode, createJMenuItem, getDataManager, getIconFromParams

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
    return "Databases"

  def createPopup(self):
    menu = JPopupMenu()
    menu.add(createJMenuItem("Add database",self.mnuAddDatabase))
    menu.add(createJMenuItem("Refresh",self.mnuRefresh))
    return menu    

  def mnuAddDatabase(self, event):
    manager = DALSwingLocator.getSwingManager()
    panel = manager.createJDBCConnectionPanel()
    winmgr = ToolsSwingLocator.getWindowManager()
    dialog = winmgr.createDialog(
      panel.asJComponent(),
      "Catalog",
      "Database connections",
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
    except Throwable,ex:
      pass
    self.reload()
  
  def createPopup(self):
    menu = JPopupMenu()
    menu.add(createJMenuItem("Edit parameters",self.mnuEditParameters))
    menu.add(createJMenuItem("Refresh",self.mnuRefresh))
    menu.add(JSeparator())
    menu.add(createJMenuItem("Remove database",self.mnuRemoveDatabase))
    return menu    

  def mnuRemoveDatabase(self, event):
    #print "RemoveFromBookmarks ", self
    if confirmDialog("Are you sure to remove '%s' ?" % str(self), "Catalog",YES_NO,QUESTION)==YES:
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
    menu = JPopupMenu()
    menu.add(createJMenuItem("Edit parameters",self.mnuEditParameters))
    return menu    

  def mnuEditParameters(self, event):
    manager = DALSwingLocator.getDataStoreParametersPanelManager()
    panel = manager.createDataStoreParametersPanel(self.__params)
    manager.showPropertiesDialog(self.__params, panel)
  
  def actionPerformed(self, event):
    layer = MapContextLocator.getMapContextManager().createLayer(self.__params.getTable(), self.__params)
    gvsig.currentView().getMapContext().getLayers().addLayer(layer)
    
def main(*args):
    pass
