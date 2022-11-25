# encoding: utf-8

import gvsig
from gvsig.commonsdialog import msgbox

from gvsig.libs.formpanel import FormPanel
from org.gvsig.tools.swing.api import ToolsSwingUtils
from org.apache.commons.lang3 import StringUtils

from org.gvsig.fmap.dal import DALLocator
from org.gvsig.fmap.dal.swing import DALSwingLocator
from org.gvsig.fmap.dal.DatabaseWorkspaceManager import TABLE_REPOSITORY, CONFIG_NAME_STORESREPOSITORYID, CONFIG_NAME_STORESREPOSITORYLABEL
from org.gvsig.andami import PluginsLocator

class CreateRepository(FormPanel):
    def __init__(self):
        FormPanel.__init__(self,gvsig.getResource(__file__,"createrepo.xml"))
        ToolsSwingUtils.ensureRowsCols(self.asJComponent(),6, 100,10,130)
        dataSwingManager = DALSwingLocator.getDataSwingManager()
        self.connectionPicker = dataSwingManager .createJDBCConnectionPickerController(
                self.cboBaseDeDatos,
                self.btnBaseDeDatos
        )

    def btnCrearRepositorio_click(self, *args):
      repoid = self.txtIdentificador.getText()
      repolabel = self.txtEtiqueta.getText()
      if StringUtils.isBlank(repoid) :
        msgbox("Debera indicar un identificador para el nuevo repositorio")
        return
      serverparams = self.connectionPicker.get()
      if serverparams == None:
        msgbox("Debera indicar la base de datos en la que crear el repositorio")
        return
      dataManager = DALLocator.getDataManager()
      wsmanager = dataManager.createDatabaseWorkspaceManager(serverparams)
      if wsmanager.existsTable(TABLE_REPOSITORY):
          msgbox("Ya existe un repositorio en la base de datos indicada")
          return
      wsmanager.createTable(TABLE_REPOSITORY)
      wsmanager.set(CONFIG_NAME_STORESREPOSITORYID, repoid)
      wsmanager.set(CONFIG_NAME_STORESREPOSITORYLABEL, repolabel)
      msgbox("Repositorio creado")
      self.hide()

    def btnCancelar_click(self, *args):
      self.hide()

      
def main(*args):
  #x = CreateRepository()
  #x.showWindow("Crear repositorio")
  actionManager = PluginsLocator.getActionInfoManager()
  action = actionManager.getAction("database-workspace-connect").execute()
  