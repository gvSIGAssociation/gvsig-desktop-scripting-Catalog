# encoding: utf-8

import gvsig

from org.gvsig.app import ApplicationLocator

from addons.Catalog.dynobjectadapter import createDynObjectAdapter

import addons.Catalog.catalogmanager
#reload(addons.Catalog.catalogmanager)
from addons.Catalog.catalogmanager import CatalogManager

def getCatalogManager():
  application = ApplicationLocator.getApplicationManager()
  adapter = application.getProperty("Catalog.Manager")
  if adapter == None:
    manager = CatalogManager()
    #print "==========> Create and register CatalogManager (2)"
    adapter = createDynObjectAdapter(manager)
    application.setProperty("Catalog.Manager",adapter)
  else:
    manager = adapter._get()
  return manager

getManager = getCatalogManager
  
def unload():
  application = ApplicationLocator.getApplicationManager()
  application.setProperty("Catalog.Manager",None)
  #print "==========> Unload CatalogManager (1)"

def selfRegister():
  application = ApplicationLocator.getApplicationManager()
  adapter = application.getProperty("Catalog.Manager")
  if adapter == None:
    manager = CatalogManager()
    #print "==========> Create and register CatalogManager (1)"
    adapter = createDynObjectAdapter(manager)
    application.setProperty("Catalog.Manager",adapter)
  

def main(*args):
  #selfRegister()
  unload()
  
