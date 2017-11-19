# encoding: utf-8

import gvsig

from addons.Catalog.catalog import JCatalogTree
from gvsig import currentView
from gvsig import getResource
from java.io import File
from javax.swing import JScrollPane
from org.gvsig.andami import PluginsLocator
from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents import DocumentManager
from org.gvsig.app.project.documents.view import ViewManager
from org.gvsig.scripting.app.extension import ScriptingExtension
from org.gvsig.tools import ToolsLocator
from org.gvsig.tools.observer import Observer
from org.gvsig.tools.swing.api import ToolsSwingLocator

class AddCatalogToViewObserver(Observer):
  def __init__(self):
    pass

  def update(self, viewpanel, notification):
    if notification.getValue()==None :
      return
    if notification.getType() != DocumentManager.NOTIFY_AFTER_CREATEMAINWINDOW :
      return
    #
    # Cada vez que se crea un panel de vista nuevo, le añadimos el catalogo.
    i18n = ToolsLocator.getI18nManager()
    viewpanel = notification.getValue()
    viewpanel.getViewInformationArea().add(
      JScrollPane(JCatalogTree()), 
      "Catalog", 
      100, 
      i18n.getTranslation("_Catalog"), 
      None, 
      None
    )      

class DatasourceCatalogExtension(ScriptingExtension):
  def __init__(self):
    self._catalogPanel = None

  def canQueryByAction(self):
    return True

  def isEnabled(self,action):
    if action.lower() == "addlayertocatalog":
      view = currentView()
      if view == None:
        return False
      layers = view.getMapContext().getLayers().getActives()
      if layers == None:
        return False
      if len(layers)<1:
        return False
    return True

  def isVisible(self,action):
    return True
    
  def getCatalogTree(self):
    viewInformationArea = currentView().getWindowOfView().getViewInformationArea()
    jsp = viewInformationArea.get("Catalog")
    if jsp == None:
      return None
    catalogTree = jsp.asJComponent().getViewport().getView()
    return catalogTree
    
  def execute(self,actionCommand, *args):
    actionCommand = actionCommand.lower()
    if actionCommand == "addlayertocatalog":
      self.getCatalogTree().addCurrentLayerToBookmarks()

def selfRegister():
  #
  # Registramos las traducciones
  i18n = ToolsLocator.getI18nManager()
  i18n.addResourceFamily("text",File(getResource(__file__,"i18n")))

  #
  # Registramos los iconos en el tema de iconos
  icon_addLayerToCatalog = File(getResource(__file__,"images","catalog-add-icon.png")).toURI().toURL()
  iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
  iconTheme.registerDefault("scripting.catalog", "action", "tools-catalog-addLayerToCatalog", None, icon_addLayerToCatalog)

  #
  # Creamos la accion para el ToC
  extension = DatasourceCatalogExtension()
  actionManager = PluginsLocator.getActionInfoManager()
  action_addCurrentLayer = actionManager.createAction(
    extension, 
    "tools-catalog-addLayerToCatalog", # Action name
    "Add to catalog", # Text
    "addLayerToCatalog", # Action command
    "tools-catalog-addLayerToCatalog", # Icon name
    None, # Accelerator
    1009000000, # Position 
    "Add active layer to Catalog" # Tooltip
  )
  action_addCurrentLayer = actionManager.registerAction(action_addCurrentLayer)

  projectManager = ApplicationLocator.getProjectManager()  
  viewManager = projectManager.getDocumentManager(ViewManager.TYPENAME)
  viewManager.addTOCContextAction("tools-catalog-addLayerToCatalog")

  #
  # Añadimos el observer al ViewManager para añadir el catalogo a la Vista
  # cuando se cree el panel de la vista.
  projectManager = ApplicationLocator.getProjectManager()
  viewManager = projectManager.getDocumentManager(ViewManager.TYPENAME)
  addCatalogToViewObserver = AddCatalogToViewObserver()
  viewManager.setProperty("AddCatalogObserver",addCatalogToViewObserver)
  viewManager.addObserver(addCatalogToViewObserver)

  #
  # Si ya hay una vista abierta le mete el catalogo
  view = currentView()
  if view != None:
    viewPanel = view.getWindowOfView()
    viewInformationArea = viewPanel.getViewInformationArea()
    if viewInformationArea.get("Catalog")==None:
      viewInformationArea.add(
        JScrollPane(JCatalogTree()), 
        "Catalog", 
        100, 
        i18n.getTranslation("_Catalog"), 
        None, 
        None
      )      
  
def test():
    viewInformationArea = currentView().getWindowOfView().getViewInformationArea()
    jsp = viewInformationArea.get("Catalog")
    if jsp == None:
      return
    catalogTree = jsp.asJComponent().getViewport().getView()
    print catalogTree.__class__.__name__
    
def main(*args):
  #selfRegister()
  test()    
  