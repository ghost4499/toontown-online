import sys
if sys.version_info >= (3, 0):
    from panda3d.core import NodePath
    from . import Entity, BasicEntities
else:
    from pandac.PandaModules import NodePath
    import Entity, BasicEntities

from direct.directnotify import DirectNotifyGlobal

class LocatorEntity(Entity.Entity, NodePath):
    notify = DirectNotifyGlobal.directNotify.newCategory('LocatorEntity')

    def __init__(self, level, entId):
        node = hidden.attachNewNode('LocatorEntity-%s' % entId)
        NodePath.__init__(self, node)
        Entity.Entity.__init__(self, level, entId)
        self.doReparent()

    def destroy(self):
        Entity.Entity.destroy(self)
        self.removeNode()

    def getNodePath(self):
        return self

    def doReparent(self):
        if self.searchPath != '':
            parent = self.level.geom.find(self.searchPath)
            if parent.isEmpty():
                LocatorEntity.notify.warning("could not find '%s'" % self.searchPath)
                self.reparentTo(hidden)
            else:
                self.reparentTo(parent)

    if __dev__:

        def attribChanged(self, attrib, value):
            self.doReparent()
