# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 11:16:21 2019

@author: agross
"""

import xml.etree.ElementTree as ET

class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

#@Singleton
class XML_Read():
    def __init__(self,XMLfilename='config.xml'):
        """     
        Loads an XML file.
               
        Parameters
        ----------
        XMLfilename : str
            Relative path to xml file from the project folder
        
        Returns
        -------
        None
        
        """
        self.filename = XMLfilename
        try:
            self.tree = ET.parse(XMLfilename)
            self.root = self.tree.getroot() #'config.xml'
        except IOError as e :
            print(e)
    
    def getValue(self,listTags,root=None):
        """     
        Recursively finds the needed XML Tag.
               
        Parameters
        ----------
        listTags : list(str)
            List of all xml tags each one, one level deeper than the latter one.
        root : root of element tree
            the new root of the subtree. If None, the original tree is used.
        
        Returns
        -------
        str
            Content of the XML tag, given it exists, None otherwise.
        
        """
        try:
            searchroot = self.root if root==None else root
            if len(listTags)==1:
                return searchroot.find(listTags[0]).text
            for child in searchroot:
                if child.tag==listTags[0]:
                    return self.getValue(listTags[1:],root=child)
            return None
        except AttributeError as e:
            return None
        
    def getAttrib(self,listTags,attribname,root=None):
        """     
        Recursively finds the needed XML Tag.
               
        Parameters
        ----------
        listTags : list(str)
            List of all xml tags each one, one level deeper than the latter one.
        root : root of element tree
            the new root of the subtree. If None, the original tree is used.
        
        Returns
        -------
        str
            Content of the XML tag, given it exists, None otherwise.
        
        """
        try:
            searchroot = self.root if root==None else root
            if len(listTags)==1:
                return searchroot.find(listTags[0]).attrib[attribname]
            for child in searchroot:
                if child.tag==listTags[0]:
                    return self.getAttrib(listTags[1:],attribname,root=child)
            return None
        except (AttributeError,KeyError) as e:
            return None
        
    def saveValue(self,listTags,value,root=None):
        """     
        Recursively finds the needed XML Tag.
               
        Parameters
        ----------
        listTags : list(str)
            List of all xml tags each one, one level deeper than the latter one.
        root : root of element tree
            the new root of the subtree. If None, the original tree is used.
        
        Returns
        -------
        str
            Content of the XML tag, given it exists, None otherwise.
        
        """
        try:
            searchroot = self.root if root==None else root
    
            for child in searchroot:
                if child.tag==listTags[0]:
                    if len(listTags)==1:
                        child.text = value
                        self.tree.write(self.filename)
                        return True
                    return self.saveValue(listTags[1:],value,root=child)
            return False
        except AttributeError as e:
            return None
        
    def getChildren(self,listTags,root=None):
        """     
        Recursively finds the needed XML Tag.
               
        Parameters
        ----------
        listTags : list(str)
            List of all xml tags each one, one level deeper than the latter one.
        root : root of element tree
            the new root of the subtree. If None, the original tree is used.
        
        Returns
        -------
        str
            Content of the XML tag, given it exists, None otherwise.
        
        """
        try:
            searchroot = self.root if root==None else root           
            for child in searchroot:
                if child.tag==listTags[0]:
                    if len(listTags[1:]) == 0:
                        return [(child_.tag,child_.text) for child_ in child]
                    return self.getChildren(listTags[1:],root=child)
            return None
        except AttributeError as e:
            return None
