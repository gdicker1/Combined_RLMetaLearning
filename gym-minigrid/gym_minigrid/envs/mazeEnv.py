from gym_minigrid.minigrid import *
from gym_minigrid.register import register

class MazeEnv(MiniGridEnv):
    """
    Empty grid environment, no obstacles, sparse reward
    """

    def __init__(
        self,
        size=3, # 2 or greater 
        limit=1, # 1 to size
        agent_start_pos=(1,1),
        agent_start_dir=0,
        seed=1000
    ):
        self.agent_start_pos = agent_start_pos
        self.agent_start_dir = agent_start_dir
        self.size = pow(2,size)+1
        self.limit = pow(2,limit)+1

        super().__init__(
            grid_size = self.size,
            max_steps = 4*self.size*self.size,
            seed = seed,
            # Set this to True for maximum speed
            see_through_walls=True
        )

    def _gen_grid(self, width, height):
        # Create an empty grid
        self.grid = Grid(width, height)

        # Generate the surrounding walls
        self.grid.wall_rect(0, 0, width, height)

        # Generate maze
        if self.limit < self.size:
            self._recursive_division(1, 1, self.size-2, self.limit)

        # Place a goal square in the bottom-right corner
        self.put_obj(Goal(), width-2, height-2)

        # Place the agent
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        self.mission = "Reach green goal square"

    def _recursive_division(self, x, y, size, min):
        div = int((size-1)/2)

        obj_type=Wall
        # horizontal wall
        # generate gap positions
        gap1 = self._rand_int(0, size)
        while gap1%2 == 1:
            gap1 = self._rand_int(0, size)
        # build walls
        for i in range(size):
            if i != gap1:
                self.grid.set(x+i, y+div, obj_type())

        # vertical wall 
        if div < 3:
            gap2 = 0
            gap3 = 2
        else:   
            # generate gap positions
            gap2 = self._rand_int(0, div)
            while gap2%2 == 1:
                gap2 = self._rand_int(0, div)

            gap3 = self._rand_int(div+1, size)
            while gap3%2 == 1:
                gap3 = self._rand_int(div+1, size)
        # build walls
        for i in range(size):
            if i != gap2 and i != gap3:
                self.grid.set(x+div, y+i, obj_type())

        if size/2 > min:
            newSize = int((size-1)/2)
            self._recursive_division(x, y, newSize, min)
            self._recursive_division(x+div+1, y, newSize, min)
            self._recursive_division(x, y+div+1, newSize, min)
            self._recursive_division(x+div+1, y+div+1, newSize, min)


# empty room
class EmptyEnv9x9(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=3, limit=3, **kwargs)

# simple maze
class MazeEnv9x9(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=3, limit=1, **kwargs)

# medium maze with small rooms
class MazeEnv17x17EZ(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=4, limit=2, **kwargs)

# medium maze w/o rooms
class MazeEnv17x17(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=4, limit=1, **kwargs)

# hard amze w/ small rooms
class MazeEnv33x33(MazeEnv):
    def __init__(self, **kwargs):

        super().__init__(size=5, limit=2, **kwargs)

register(
    id='MiniGrid-Maze-9x9-v0',
    entry_point='gym_minigrid.envs:EmptyEnv9x9'
)

register(
    id='MiniGrid-Maze-9x9-v1',
    entry_point='gym_minigrid.envs:MazeEnv9x9'
)

register(
    id='MiniGrid-Maze-17x17-v0',
    entry_point='gym_minigrid.envs:MazeEnv17x17EZ'
)

register(
    id='MiniGrid-Maze-17x17-v1',
    entry_point='gym_minigrid.envs:MazeEnv17x17'
)

register(
    id='MiniGrid-Maze-33x33-v0',
    entry_point='gym_minigrid.envs:MazeEnv33x33'
)