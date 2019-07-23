# encoding: utf-8

import gvsig

from org.gvsig.app import ApplicationLocator

from addons.Catalog.dynobjectadapter import createDynObjectAdapter
from addons.Catalog.catalogmanager import CatalogManager

def getCatalogManager():
  application = ApplicationLocator.getApplicationManager()
  adapter = application.getProperty("Catalog.Manager")
  if adapter == None:
    manager = CatalogManager()
    adapter = createDynObjectAdapter(manager)
    application.setProperty("Catalog.Manager",adapter)
  else:
    manager = adapter._get()
  return manager

getManager = getCatalogManager
  
    
def selfRegister():
  application = ApplicationLocator.getApplicationManager()
  manager = CatalogManager()
  adapter = createDynObjectAdapter(manager)
  application.setProperty("Catalog.Manager",adapter)
  

def main(*args):
  selfRegister()
