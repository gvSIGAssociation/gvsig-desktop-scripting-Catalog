# encoding: utf-8

import gvsig

from addons.Catalog import actions
from addons.Catalog import cataloglocator

from addons.Catalog.folders import Folders
from addons.Catalog.bookmarks import Bookmarks
from addons.Catalog.databases import Databases
from addons.Catalog.storesrepository import StoresRepository

import addons.Catalog.cataloglocator

def main(*args):
  script.registerDataFolder("Catalog")
  
  catalogManager = cataloglocator.getCatalogManager()
  catalogManager.addCatalogNode(Folders)
  catalogManager.addCatalogNode(Bookmarks)
  catalogManager.addCatalogNode(Databases)
  catalogManager.addCatalogNode(StoresRepository)

  catalogManager.installCatalog()
  
  actions.selfRegister()
  catalogManager.putCatalogInViews()

