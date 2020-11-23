from gym_minigrid.minigrid import *
from gym_minigrid.register import register
import numpy as np

class MazeEnv(MiniGridEnv):
    """
    Empty grid environment, no obstacles, sparse reward
    """

    def __init__(
        self,
        size=2, # 1 or greater; increase maze size
        limit=1, # 1 to size; increase room size
        obstacle_type=None, # toggles lava
        ball_level=0, # 0 to 5; increase movable objects
        door_level=0, # 0 to 3; 0=no doors, 1=unlocked doors, 2=locked doors, 3=locked doors hidden keys 
        gap_level=1, # 1 to 3; number of gaps added
        agent_start_pos=(1,1),
        agent_start_dir=0,
        seed=0
    ):
        self.agent_start_pos = agent_start_pos
        self.agent_start_dir = agent_start_dir
        self.size = pow(2,size+1)+1
        self.limit = pow(2,limit)+1
        self.obstacle_type = obstacle_type
        self.ball_level = ball_level
        self.door_level = door_level
        self.gap_level = gap_level

        if self.door_level > 1:
            self.lock = True
        else:
            self.lock = False

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
            self._recursive_division(1, 1, self.size-2, self.limit, 0)

        # place moveable objeccts
        if self.ball_level > 0:
            num_balls = int(self.size*self.ball_level)
            for i in range(num_balls):
                x = self._rand_int(0, int((self.size-1)/2))*2+1
                y = self._rand_int(0, int((self.size-1)/2))*2+1
                if (x > 1 or y > 1) and self.grid.get(x, y)==None: # can't populate agent start position
                    self.put_obj(Ball(), x, y)

        # Place a goal square in the bottom-right corner
        self.put_obj(Goal(), width-2, height-2)

        # Place the agent
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        self.mission = "Reach green goal square"

    def _recursive_division(self, x, y, size, min, lvl):
        div = int((size-1)/2)

        num_gap = (self.gap_level - lvl)
        if num_gap < 1:
            num_gap = 1
        #print(num_gap)
        # horizontal wall
        gap1 = 0
        for j in range(num_gap):
            # generate gap positions
            gap1 = self._rand_int(0, div+1)*2
            while self.grid.get(x+gap1, y+div)!=None:
                gap1 = self._rand_int(0, div+1)*2
                #print(gap1)

            if size>7 and self.door_level>0:
                self.grid.set(x+gap1, y+div, Door(color=COLOR_NAMES[lvl%6], is_locked=self.lock))

        # build walls
        for i in range(size):
            if self.grid.get(x+i, y+div)==None and i!=gap1:
                self.grid.set(x+i, y+div, Wall())

        gap1 = 0
        gap2 = 2
        # vertical wall
        for j in range(num_gap):            
            # generate gap positions 
            if div > 2:   
                gap1 = self._rand_int(0, div)
                while gap1%2==1 or self.grid.get(x+div, y+gap1)!=None:
                    gap1 = self._rand_int(0, div)
                    #print(gap1)

                gap2 = self._rand_int(div+1, size)
                while gap2%2==1 or self.grid.get(x+div, y+gap2)!=None:
                    gap2 = self._rand_int(div+1, size)
                    #print(gap2)

            if size>7 and self.door_level>0:
                self.grid.set(x+div, y+gap1, Door(color=COLOR_NAMES[lvl%6], is_locked=self.lock))
                self.grid.set(x+div, y+gap2, Door(color=COLOR_NAMES[lvl%6], is_locked=self.lock))

        # build walls
        for i in range(size):
            if self.grid.get(x+div, y+i)==None and i!=gap1 and i!=gap2:
                self.grid.set(x+div, y+i,  Wall())
                
        
        # place keys
        if self.lock==True and size>3 and lvl!=0:
            color = COLOR_NAMES[(lvl-1)%6]
            kx = self._rand_int(0, div)*2
            ky = self._rand_int(0, div)*2
            while (kx==0 and ky==0) or self.grid.get(kx+x, ky+y)!=None:
                kx = self._rand_int(0, div)*2
                ky = self._rand_int(0, div)*2
                #print(self.grid.get(kx+x, ky+y)!=None)  

            if self.door_level == 2:
                self.put_obj(Key(color=color), kx+x, ky+y)
            else:
                self.put_obj(Box(color='red', contains=Key(color=color)), kx+x, ky+y)
                
                for i in range(3):
                    kx = self._rand_int(0, div)*2
                    ky = self._rand_int(0, div)*2
                    while (kx==0 and ky==0) or self.grid.get(kx+x, ky+y)!=None:
                        kx = self._rand_int(0, div)*2
                        ky = self._rand_int(0, div)*2
                        #print((kx==0 and ky==0) or self.grid.get(kx+x, ky+y)!=None)  
                        #print(self.grid.get(kx+x, ky+y))
                    self.put_obj(Box(color='red'), kx+x, ky+y)

        nlvl = lvl+1
        if size/2 > min:
            newSize = int((size-1)/2)
            self._recursive_division(x, y, newSize, min, nlvl)
            self._recursive_division(x+div+1, y, newSize, min, nlvl)
            self._recursive_division(x, y+div+1, newSize, min, nlvl)
            self._recursive_division(x+div+1, y+div+1, newSize, min, nlvl)
        elif self.limit != 1:
            newSize = int((size-1)/2)
            self._construct_room(x, y, newSize, lvl)
            self._construct_room(x+div+1, y, newSize, lvl)
            self._construct_room(x, y+div+1, newSize, lvl)
            self._construct_room(x+div+1, y+div+1, newSize, lvl)

    def _construct_room(self, x, y, size, lvl):
        div = int((size-1)/2)

        # Generate lava wall
        if self.obstacle_type == Lava:
            gap = self._rand_int(0, size)
            dir = self._rand_bool()
            
            if dir == 0:
                for i in range(size):
                    if i != gap:
                        self.grid.set(x+i, y+div, self.obstacle_type())
            else:
                for i in range(size):
                    if i != gap:
                        self.grid.set(x+div, y+i, self.obstacle_type())  
        
        # place keys
        if self.lock==True and size>6:
            color = COLOR_NAMES[(lvl)%6]
            kx = self._rand_int(0, div)*2
            ky = self._rand_int(0, div)*2
            while (kx==0 and ky==0) or self.grid.get(kx+x,ky+y)!=None:
                kx = self._rand_int(0, div)*2
                ky = self._rand_int(0, div)*2
                #print(self.grid.get(kx+x,ky+y)!=None)  

            if self.door_level == 2:
                self.put_obj(Key(color=color), kx+x, ky+y)
            else:
                self.put_obj(Box(color='red', contains=Key(color=color)), kx+x, ky+y)
                
                for i in range(2):
                    kx = self._rand_int(0, div)*2
                    ky = self._rand_int(0, div)*2
                    
                    while (kx==0 and ky==0) or self.grid.get(kx+x,ky+y)!=None:
                        kx = self._rand_int(0, div)*2+1
                        ky = self._rand_int(0, div)*2
                        #print(self.grid.get(kx+x,ky+y)!=None)  
                    self.put_obj(Box(color='red'), kx+x, ky+y)



# empty room
class EmptyEnv9x9(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=3, 
                         limit=3, 
                         obstacle_type=None, 
                         **kwargs)

# simple maze
class MazeEnv9x9(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=3, 
                         limit=1, 
                         obstacle_type=None, 
                         **kwargs)

# medium maze with small rooms
class MazeEnv17x17EZ(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=4, 
                         limit=2, 
                         obstacle_type=None, 
                         **kwargs)

# medium maze w/o rooms
class MazeEnv17x17(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=4, 
                         limit=1, 
                         door_level=3, 
                         **kwargs)

# hard maze w/ small rooms
class MazeEnv33x33(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=5, 
                         limit=2, 
                         obstacle_type=None, 
                         **kwargs)

# large maze w/ large rooms
class MazeEnv33x33BigRoom(MazeEnv):
    def __init__(self, **kwargs):
        super().__init__(size=4, 
                         limit=2, 
                         obstacle_type=Lava, 
                         ball_level=5,
                         door_level=3, 
                         gap_level=1,
                         **kwargs)

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

register(
    id='MiniGrid-Maze-33x33-v1',
    entry_point='gym_minigrid.envs:MazeEnv33x33BigRoom'
)