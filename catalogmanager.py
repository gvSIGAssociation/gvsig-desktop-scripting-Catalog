# encoding: utf-8

import gvsig

from javax.swing import Action
from javax.swing import JScrollPane, JComponent
from org.gvsig.tools.observer import Observer

from org.gvsig.tools import ToolsLocator
from org.gvsig.app.project.documents import DocumentManager
from org.gvsig.app import ApplicationLocator
from org.gvsig.app.project.documents.view import ViewManager, ViewDocument

def createJCatalogTree():
    # Esta funcion es para postponer el import de catalog
    # y prevenir imports circulares
    from addons.Catalog import catalog 
    return catalog.JCatalogTree()

def getCatalogManager():
    # Esta funcion es para postponer el import de cataloglocator
    # y prevenir imports circulares
    from addons.Catalog import cataloglocator 
    return cataloglocator.getCatalogManager()

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
    catalogManager = getCatalogManager()
    viewpanel = notification.getValue()
    catalogManager.putCatalogInView(viewpanel)

class CatalogAction(Action):
  def __init__(self,action, storeParameters):
    self.__storeParameters = storeParameters
    self.__action = action

  def putValue(self, key, value):
    self.__action.putValue(key, value)

  def isEnabled(self):
    return self.__action.isEnabled()

  def addPropertyChangeListener(self, listener):
    self.__action.addPropertyChangeListener(listener)

  def removePropertyChangeListener(self, listener):
    self.__action.removePropertyChangeListener(listener)
    
  def getValue(self, key):
    return self.__action.getValue(key)

  def setEnabled(self, enabled):
    self.__action.setEnabled(enabled)

  def actionPerformed(self, event):
    event.setSource(self.__storeParameters)
    self.__action.actionPerformed(event)

class CatalogManager(object):
  def __init__(self):
    self.__actions = dict()
    self.__catalogNodeClasses = list()

  def putCatalogInView(self, view):
    i18n = ToolsLocator.getI18nManager()
    if isinstance(view, JComponent):
      viewpanel = view
    elif isinstance(view, ViewDocument):
      if not view.hasMainWindow():
        return
      viewpanel = view.getWindowOfView()
    else:
      return
    jtree = createJCatalogTree()
    viewpanel.getViewInformationArea().add(
        JScrollPane(jtree), 
        "Catalog", 
        100, 
        i18n.getTranslation("_Catalog"), 
        None, 
        None
  )      
      
  def addCatalogNode(self, nodeClass):
    #print "Catalog manager, add " + repr(nodeClass)
    self.__catalogNodeClasses.append(nodeClass)
    #print "Catalog manager added, nodes " + repr(self.__catalogNodeClasses)

  def getCatalogNodes(self):
    #print "Catalog manager, get nodes " + repr(self.__catalogNodeClasses)
    return self.__catalogNodeClasses
     
  def addAction(self, actionName, nodeName, action):
    self.__actions["%s-%s" %(actionName, nodeName)] = (actionName, nodeName, action)

  def getAction(self, actionName, nodeName):
    action = self.__actions.get("%s-%s" %(actionName, nodeName),None)
    if action == None:
      return None
    return action[2]
    
  def getActions(self, nodeName, storeParameters):
    actionNames = list()
    for action in self.__actions.itervalues():
      if action[1] == nodeName:
        actionNames.append(action[0])
    actions = list()
    actionNames.sort()
    for actionName in actionNames:
      actions.append(CatalogAction(self.__actions["%s-%s" %(actionName, nodeName)][2],storeParameters))
    return actions
  
  def getCatalogTree(self, view=None):
    if view == None:
       view = gvsig.currentView()
    if view == None:
      return None
    window = view.getWindowOfView()
    if window == None:
      return None
    viewInformationArea = window.getViewInformationArea()
    if viewInformationArea == None:
      return None
    jsp = viewInformationArea.get("Catalog")
    if jsp == None:
      return None
    catalogTree = jsp.asJComponent().getViewport().getView()
    return catalogTree

  def installCatalog(self):
    # Añadimos el observer al ViewManager para añadir el catalogo a la Vista
    # cuando se cree el panel de la vista.
    projectManager = ApplicationLocator.getProjectManager()
    viewManager = projectManager.getDocumentManager(ViewManager.TYPENAME)
    addCatalogToViewObserver = AddCatalogToViewObserver()
    viewManager.setProperty("AddCatalogObserver",addCatalogToViewObserver)
    viewManager.addObserver(addCatalogToViewObserver)

  def putCatalogInViews(self):
    projectManager = ApplicationLocator.getProjectManager()
    project = projectManager.getCurrentProject()
    for viewdoc in project.getDocuments(ViewManager.TYPENAME):
      viewpanel = viewdoc.getWindowOfView()
      if viewpanel != None:
        self.putCatalogInView(viewpanel)
  
def main(*args):
  #application = ApplicationLocator.getApplicationManager()
  #application.setProperty("Catalog.Manager",None)
  
  #manager = getCatalogManager()
  #manager.putCatalogInViews()
  pass
