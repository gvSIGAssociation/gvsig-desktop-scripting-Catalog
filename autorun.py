# encoding: utf-8

import gvsig

from addons.Catalog import actions
from addons.Catalog import cataloglocator

def main(*args):
  script.registerDataFolder("Catalog")
  cataloglocator.selfRegister()
  actions.selfRegister()
  

