# encoding: utf-8

import gvsig

from javax.swing import Action

class CatalogManager(object):
  def __init__(self):
    self.__actions = dict()

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
    
def main(*args):
    pass
