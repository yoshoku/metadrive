import atexit
import logging

from panda3d.bullet import BulletWorld
from panda3d.core import Vec3

from metadrive.constants import CollisionGroup


class PhysicsWorld:
    def __init__(self, debug=False, disable_collision=False):
        # a dynamic world, moving objects or objects which react to other objects should be placed here
        self.dynamic_world = BulletWorld()
        CollisionGroup.set_collision_rule(self.dynamic_world, disable_collision=disable_collision)
        self.dynamic_world.setGravity(Vec3(0, 0, -9.81))  # set gravity
        # a static world which used to query position/overlap .etc. Don't implement doPhysics() in this world
        self.static_world = BulletWorld() if not debug else self.dynamic_world
        CollisionGroup.set_collision_rule(self.static_world, disable_collision=disable_collision)

        # The dynamic world holds a Python collision callback (a PythonCallbackObject). If the
        # BulletWorld is left to be destroyed during interpreter shutdown (e.g. the user never
        # calls env.close()), that callback's destructor calls PyGILState_Ensure() to release the
        # Python callable *after* the Python runtime has been finalized, which segfaults (observed
        # on macOS). Releasing the callback in an atexit hook runs while Python is still alive and
        # avoids the crash. destroy() is idempotent and unregisters this hook.
        atexit.register(self.destroy)

    def report_bodies(self):
        dynamic_bodies = \
            self.dynamic_world.getNumRigidBodies() + self.dynamic_world.getNumGhosts() + self.dynamic_world.getNumVehicles()
        static_bodies = \
            self.static_world.getNumRigidBodies() + self.static_world.getNumGhosts() + self.static_world.getNumVehicles()
        return "dynamic bodies:{}, static_bodies: {}".format(dynamic_bodies, static_bodies)

    def destroy(self):
        if self.dynamic_world is None and self.static_world is None:
            # already destroyed
            return
        atexit.unregister(self.destroy)

        if self.dynamic_world is not None:
            self.dynamic_world.clearDebugNode()
            self.dynamic_world.clearContactAddedCallback()
            self.dynamic_world.clearFilterCallback()

        if self.static_world is not None:
            self.static_world.clearDebugNode()
            self.static_world.clearContactAddedCallback()
            self.static_world.clearFilterCallback()

        self.dynamic_world = None
        self.static_world = None

    def __del__(self):
        logging.debug("Physics world is destroyed successfully!")
