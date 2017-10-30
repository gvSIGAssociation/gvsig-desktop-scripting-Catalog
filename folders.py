# encoding: utf-8

import gvsig
from gvsig import getResource

import os

from java.io import File
from org.gvsig.tools import ToolsLocator
from org.gvsig.andami import PluginsLocator


from catalogutils import CatalogSimpleNode, CatalogNode, getIconFromFile

class Folders(CatalogNode):
  def __init__(self, parent):
    CatalogNode.__init__(self,parent)
    self.add(FolderNode(self,os.getenv("HOME"),"Home",icon=getResource(__file__,"images","Home.png")))

    foldersManager = ToolsLocator.getFoldersManager()
    dataFolder = foldersManager.get("DataFolder")
    if dataFolder != None:
      self.add(FolderNode(self,dataFolder.getAbsolutePath(),"Data",icon=getResource(__file__,"images","DataFolder.png")))
    
  def toString(self):
    return "Folders"
    
class FolderNode(CatalogSimpleNode):
  def __init__(self, parent, path, label = None, icon = None):
    CatalogSimpleNode.__init__(self, parent, icon)
    self.__path = path
    if label == None:
      self.__label = os.path.basename(self.__path)
    else:
      self.__label = label
    self.__files = list()
    ls = os.listdir(self.__path)
    lsdirs = list()
    lsfiles = list()
    for f in ls:
      x = os.path.join(self.__path,f)
      if f[0]!=".":
        if os.path.isdir(x):
          lsdirs.append(x)
        else:
          lsfiles.append(x)
    lsdirs.sort(key=lambda s: s.lower())
    lsfiles.sort(key=lambda s: s.lower())
    self.__files.extend(lsdirs)
    self.__files.extend(lsfiles)
    
  def toString(self):
    return  unicode(self.__label, 'utf-8') 

  def children(self):
    # Returns the children of the receiver as an Enumeration.
    return enumerate(self.__files)
    
  def getAllowsChildren(self):
    # Returns true if the receiver allows children.
    return True

  def getChildAt(self, childIndex):
    # Returns the child TreeNode at index childIndex.
    fname = os.path.join(self.__path,self.__files[childIndex])
    if os.path.isdir(fname):
      f = FolderNode(self,fname)
    else:
      f = FileNode(self,fname)
    #print ">>> getChildAt", childIndex, f
    return f
    
  def getChildCount(self):
    # Returns the number of children TreeNodes the receiver contains.
    x = len(self.__files)
    #print ">>> getChildCount ", x
    return x

  def getIndex(self, node):
    # Returns the index of node in the receivers children.
    index = 0
    for x in self.__files:
      if node == x:
        return index
      index += 1
    return -1
     
  def getParent(self):
    # Returns the parent TreeNode of the receiver.
    return self.__parent
    
  def isLeaf(self):
    # Returns true if the receiver is a leaf.
    return False

class FileNode(CatalogSimpleNode):
  def __init__(self, parent, path, label = None):
    CatalogSimpleNode.__init__(self, parent, icon=getIconFromFile(path))
    self.__path = path
    if label == None:
      self.__label = os.path.basename(self.__path)
    else:
      self.__label = label

  def toString(self):
    return  unicode(self.__label, 'utf-8') 
    
  def actionPerformed(self, event):
    if self.getIcon()==None:
      return
    listfiles = (File(self.__path),)
    actions = PluginsLocator.getActionInfoManager()
    addlayer = actions.getAction("view-layer-add")
    addlayer.execute((listfiles,))

def main(*args):
    pass
