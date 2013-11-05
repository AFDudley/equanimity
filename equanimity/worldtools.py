def get_world(world):
    """ Returns the world by id if provided """
    from world import World
    if isinstance(world, World):
        return world
    else:
        return World.get(world)
