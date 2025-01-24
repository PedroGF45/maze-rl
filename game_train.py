import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

# initialize the pygame
pygame.init()

# RGB colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
LIGHT_RED = (150, 50, 50)
BLUE = (0, 0, 200)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
YELLOW = (200, 200, 0)

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

class WinCondition(Enum):
    PLAYER_HIT_BUTTER = 1
    MOLD_HIT_TOASTER = 2
    MOLD_HIT_PLAYER = 3
    MOLD_HIT_BUTTER = 4

# Point
Point = namedtuple('Point', 'x, y')

# Game settings
OFF_SET = 10
GRID_SIZE = 50
FPS = 60

MAX_BARRIERS = 10

class MazeGame:

    def __init__(self, grid_w = 11, grid_h = 11):
        
        # initialize grid
        self._initialize_grid(grid_w, grid_h)

        self.reset(0)
        
    def _initialize_grid(self, grid_w, grid_h):
        # init display
        self.w = GRID_SIZE * (grid_w + 1) + 2*OFF_SET
        self.h = GRID_SIZE * (grid_h + 1) + 2*OFF_SET
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.display = pygame.display.set_mode((self.w, self.h))
        
        self.clock = pygame.time.Clock()

    def reset(self, game_id):
        pygame.display.set_caption("Maze Game - ID: " + str(game_id))
        self._initialize_positions()
        self._initialize_game_state()

    def _initialize_positions(self):
        
        # valid positions for everyone
        self.valid_positions = [Point(x, y) for x in range(0, self.grid_w, 2) for y in range(0, self.grid_h, 2)]

        # toaster position
        self.toaster = random.choice(self.valid_positions)
        #self.toaster = Point(2,0)
        self.toaster_heat = [(self.toaster.x + 2, self.toaster.y), (self.toaster.x - 2, self.toaster.y), (self.toaster.x, self.toaster.y + 2), (self.toaster.x, self.toaster.y - 2)]

        # butter position except toaster position
        self.butter  = random.choice([pos for pos in self.valid_positions if pos != self.toaster])
        #self.butter = Point(8, 10)

        # valid positions for barriers
        self.valid_barriers = set(Point(x, y) for x in range(self.grid_w) for y in range(self.grid_h) if (x % 2 != 0) != (y % 2 != 0))
        self.barriers = []

        # add random number of barriers
        for _ in range(MAX_BARRIERS):
            barrier = random.choice(list(self.valid_barriers))
            self.barriers.append(barrier)
            self.valid_barriers.remove(barrier)
        #self.barriers.append(Point(1, 0))
        #self.barriers.append(Point(1, 2))
        #self.barriers.append(Point(0, 3))

        self.frame_iteration = 0

    def _initialize_game_state(self):

        self.reward = 0
        self.game_over = False
        self.win_condition = None

        # init player position
        self.player = Point(0, 0)
        self.prev_player = None

        # set player direction
        self.direction = Direction.RIGHT

        # mold position
        self.mold = Point(10,10)
        self.prev_mold = None

        # set player visited positions
        self.visited_positions = set()
        self.visited_positions.add(self.player)

        # known heat positions
        self.known_heat = set()

        # know toaster position
        self.know_toaster = False

        # plaeyr waiting on toaster
        self.player_wait = False

        # possible positions of the toaster
        self.possible_toaster = self.valid_positions.copy()

        # set player known barriers
        self.known_barriers = set()
        self._reveal_barriers() # revela as barreiras que estão na posição inicial do player

        # possible possitions of the butter
        self.distances = self._calculate_distances()
        self.possible_butter = self._init_possible_butter()
        self.know_butter = False

        # visited mold positions
        self.mold_visited = set()
        self.mold_visited.add(self.mold)

        # mold path
        self.mold_path = []

    def get_state(self):

        # convert visited positions to list of positions
        # there's self.grid_w * self.grid_h / 4 possible positions
        visited_positions = list(self.visited_positions.copy())
        while len(visited_positions) < (self.grid_w + 1)/2 * (self.grid_h + 1)/2:
            visited_positions.append((-1, -1))
        # remove tuples
        visited_positions = [pos for sublist in visited_positions for pos in sublist]

        # convert possible toaster to list of positions
        # there's self.grid_w * self.grid_h / 4 possible positions
        possible_toaster = list(self.possible_toaster.copy())
        while len(possible_toaster) < (self.grid_w + 1)/2 * (self.grid_h + 1)/2:
            possible_toaster.append((-1, -1))
        # remove tuples
        possible_toaster = [pos for sublist in possible_toaster for pos in sublist]

        #convert 4 known heat to list of positions
        # there's 4 possible heat positions
        heat_positions = list(self.known_heat.copy())
        while len(heat_positions) < 4:
            heat_positions.append((-1, -1))
        # remove tuples
        heat_positions = [pos for sublist in heat_positions for pos in sublist]

        # convert known barriers to list of positions
        # there's MAX_BARRIERS possible positions
        known_barriers = list(self.known_barriers.copy())
        while len(known_barriers) < MAX_BARRIERS:
            known_barriers.append((-1, -1))
        # remove tuples
        known_barriers = [pos for sublist in known_barriers for pos in sublist]

        # convert possible butter to list of positions
        # there's maximum self.grid + 1 /2 possible positions
        possible_butter = list(self.possible_butter.copy())
        while len(possible_butter) < (self.grid_w + 1)/2:
            possible_butter.append((-1, -1))
        # remove tuples
        possible_butter = [pos for sublist in possible_butter for pos in sublist]

        # convert mold visited to list of positions
        # there's self.grid_w * self.grid_h / 4 possible positions
        mold_visited = list(self.mold_visited.copy())
        while len(mold_visited) < (self.grid_w + 1)/2 * (self.grid_h + 1)/2:
            mold_visited.append((-1, -1))
        # remove tuples
        mold_visited = [pos for sublist in mold_visited for pos in sublist]

        # convert mold path to list of positions
        # maximum self.grid.w + 1 / 2 + self.grid.h + 1 / 2 possible positions
        mold_path = list(self.mold_path.copy())
        while len(mold_path) < (self.grid_w + 1)/2 + (self.grid_h + 1)/2:
            mold_path.append((-1, -1))
        # remove tuples
        mold_path = [pos for sublist in mold_path for pos in sublist]

        arr = np.array([
            # player info
            self.player.x,
            self.player.y,                  
            self.direction.value,               # player direction
            *visited_positions,                  # visited positions

            # toaster info
            *possible_toaster,      # possible toaster positions
            *heat_positions,        # known heat positions
            self.know_toaster,      # know toaster position

            # barriers info
            *known_barriers,    # known barriers

            # butter info
            *possible_butter,   # possible butter positions
            self.know_butter,       # know butter position
            
            # mold info
            self.mold.x,              # mold position
            self.mold.y,
            *mold_visited,      # visited mold positions
            *mold_path,         # mold path

            # reward info
            self.reward             # reward
            ], dtype=int)
        
        #print(arr)

        self._update_ui()
        return arr


    def play_step(self, action):

        # increase frame iteration
        self.frame_iteration += 1

        # update state
        self._update_state()

        # update ui and clock
        self._update_ui()

        # 1. collect user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # 2. move
        self._move(action)

        self._update_state()

        # 3. check if game over
        self._is_game_over()
        if self.game_over:
            return self.reward, self.game_over, self.win_condition
        
        if self.frame_iteration > 25:
            self.game_over = True
            self.win_condition = 5
            self.reward = -100
            return self.reward, self.game_over, self.win_condition

        # 4. update ui and clock
        self._update_ui()

        # 5. return game over and score
        return self.reward, self.game_over, self.win_condition
    
    def is_action_impossible(self):

        # check if there are barriers in all directions and can is valid move
        up = Point(self.player.x, self.player.y - 1)
        position_up = Point(self.player.x, self.player.y - 2)
        right = Point(self.player.x + 1, self.player.y)
        position_right = Point(self.player.x + 2, self.player.y)
        down = Point(self.player.x, self.player.y + 1)
        position_down = Point(self.player.x, self.player.y + 2)
        left = Point(self.player.x - 1, self.player.y)
        position_left = Point(self.player.x - 2, self.player.y)

        if (up in self.known_barriers or position_up not in self.valid_positions) and (right in self.known_barriers or position_right not in self.valid_positions) and (down in self.known_barriers or position_down not in self.valid_positions) and (left in self.known_barriers or position_left not in self.valid_positions):
            return True

    
    def is_action_valid(self, action):
        #print("KNOWN BARRIERS: ", self.known_barriers)
        if np.array_equal(action, [1, 0, 0, 0]): # up
            
            #print("from ", self.player, " to ", Point(self.player.x, self.player.y - 2))
            if (Point(self.player.x, self.player.y - 1) not in self.known_barriers) and (Point(self.player.x, self.player.y - 2) in self.valid_positions):
                return True
        elif np.array_equal(action, [0, 1, 0, 0]): # right
            #print("from ", self.player, " to ", Point(self.player.x + 2, self.player.y))
            if (Point(self.player.x + 1, self.player.y) not in self.known_barriers) and (Point(self.player.x + 2, self.player.y) in self.valid_positions):
                return True
        elif np.array_equal(action, [0, 0, 1, 0]): # down
            #print("from ", self.player, " to ", Point(self.player.x, self.player.y + 2))
            if (Point(self.player.x, self.player.y + 1) not in self.known_barriers) and (Point(self.player.x, self.player.y + 2) in self.valid_positions):
                return True
        elif np.array_equal(action, [0, 0, 0, 1]): # left
            #print("from ", self.player, " to ", Point(self.player.x - 2, self.player.y))
            if (Point(self.player.x - 1, self.player.y) not in self.known_barriers) and (Point(self.player.x - 2, self.player.y) in self.valid_positions):
                return True
        return False
    
    def _calculate_distances(self):
        distances = np.zeros((self.grid_w, self.grid_h))
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                if x % 2 == 0 and y % 2 == 0:
                    distances[x, y] = int(self._get_distance(Point(x, y), self.butter)/2)
                else:
                    distances[x, y] = -1
        return distances
    
    def _reveal_barriers(self):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for direction in directions:
            if Point(self.player.x + direction[0], self.player.y + direction[1]) in self.barriers and Point(self.player.x + direction[0], self.player.y + direction[1]) not in self.known_barriers:
                self.known_barriers.add(Point(self.player.x + direction[0], self.player.y + direction[1]))
    
    def _move(self, action):

        if np.array_equal(action, [1, 0, 0, 0]):
            self.direction = Direction.UP # go up
        elif np.array_equal(action, [0, 1, 0, 0]):
            self.direction = Direction.RIGHT # go right
        elif np.array_equal(action, [0, 0, 1, 0]):
            self.direction = Direction.DOWN # go down
        elif np.array_equal(action, [0, 0, 0, 1]): # 
            self.direction = Direction.LEFT # go left

        if (self.player_wait == False):
            if self.direction == Direction.UP:
                self.prev_player = self.player
                self.player = Point(self.player.x, self.player.y - 2)
            elif self.direction == Direction.RIGHT:
                self.prev_player = self.player
                self.player = Point(self.player.x + 2, self.player.y)
            elif self.direction == Direction.LEFT:
                self.prev_player = self.player
                self.player = Point(self.player.x - 2, self.player.y)
            elif self.direction == Direction.DOWN:
                self.prev_player = self.player
                self.player = Point(self.player.x, self.player.y + 2)

            # add player to visited positions
            if self.player not in self.visited_positions:
                self.visited_positions.add(self.player)
                # increase reward for discovering new position
                self.reward += 2
            else:
                self.reward -= 1
            

        # reveal barriers on player position
        self._reveal_barriers()

        self._update_ui()

        self._update_reward_player()

        # check game over
        self._is_game_over()

        # if game hasnt finished move mold
        if not self.game_over:

            # move mold
            self._move_mold()

            self._update_reward_mold()

            # check if player is in toaster
            if (self.player == self.toaster and self.player_wait == True):
                self.player_wait = False
            elif (self.player == self.toaster and self.player_wait == False):
                self.player_wait = True

    def _move_mold(self):

        # mold has priority of moving of N S E W
        # check wich direction is the shortest to the player
        dist_up = self._get_distance(Point(self.mold.x, self.mold.y - 2), self.player)
        dist_down = self._get_distance(Point(self.mold.x, self.mold.y + 2), self.player)
        dist_left = self._get_distance(Point(self.mold.x - 2, self.mold.y), self.player)
        dist_right = self._get_distance(Point(self.mold.x + 2, self.mold.y), self.player)

        # choose the shortest distance
        if dist_up <= dist_down and dist_up <= dist_left and dist_up <= dist_right:
            if (self.mold.y > 0):
                self.prev_mold = self.mold
                self.mold = Point(self.mold.x, self.mold.y - 2)
        elif dist_down <= dist_up and dist_down <= dist_left and dist_down <= dist_right:
            if (self.mold.y < self.grid_h - 1):
                self.prev_mold = self.mold
                self.mold = Point(self.mold.x, self.mold.y + 2)
        elif dist_left <= dist_up and dist_left <= dist_down and dist_left <= dist_right:
            if (self.mold.x > 0):
                self.prev_mold = self.mold
                self.mold = Point(self.mold.x - 2, self.mold.y)
        elif dist_right <= dist_up and dist_right <= dist_down and dist_right <= dist_left:
            if (self.mold.x < self.grid_w - 1):
                self.prev_mold = self.mold
                self.mold = Point(self.mold.x + 2, self.mold.y)

        # add mold to visited positions
        if self.mold not in self.mold_visited:
            self.mold_visited.add(self.mold)
            # increase reward for discovering new position
            self.reward += 2
        else:
            self.reward -= 1

        self.mold_path = self._get_mold_path(self.mold, self.player)

    def _get_mold_path(self, start, end):
        
        mold_x, mold_y = start
        player_x, player_y = end

        path = []

        # mold needs to go to the same row as the player before moving inside/outside
        while mold_y != player_y:
            if mold_y < player_y:
                mold_y += 2
            else:
                mold_y -= 2
            path.append(Point(mold_x, mold_y))

        # now that mold is in the same row as the player it needs to go to the same column
        while mold_x != player_x:
            if mold_x < player_x:
                mold_x += 2
            else:
                mold_x -= 2
            path.append(Point(mold_x, mold_y))

        return path
    
    def _update_state(self):
        self._remove_possible_toaster()
        self._remove_possible_butter()

    def _update_reward_player(self):
        
        if self.prev_player != None:
            # if player gets closer to toaster reward is positive
            if self._get_distance(self.player, self.toaster) < self._get_distance(self.prev_player, self.toaster):
                self.reward += 1
            # if player gets farther from toaster reward is negative
            elif self._get_distance(self.player, self.toaster) > self._get_distance(self.prev_player, self.toaster):
                self.reward -= 1

            # if player gets farther from mold reward is positive
            if self._get_distance(self.player, self.mold) > self._get_distance(self.prev_player, self.mold):
                self.reward += 2
            # if player gets closer to mold reward is negative
            elif self._get_distance(self.player, self.mold) < self._get_distance(self.prev_player, self.mold):
                self.reward -= 2

            # if player gets closer to butter reward is positive
            if self._get_distance(self.player, self.butter) < self._get_distance(self.prev_player, self.butter):
                self.reward += 3
            # if player gets farther from butter reward is negative
            elif self._get_distance(self.player, self.butter) > self._get_distance(self.prev_player, self.butter):
                self.reward -= 3

    def _update_reward_mold(self):

        if self.prev_mold != None:
            # if mold gets closer to toaster reward is positive
            if self._get_distance(self.mold, self.toaster) < self._get_distance(self.prev_mold, self.toaster):
                self.reward += 2
            # if mold gets farther from toaster reward is negative
            elif self._get_distance(self.mold, self.toaster) > self._get_distance(self.prev_mold, self.toaster):
                self.reward -= 2

            # if mold gets closer to player reward is negative
            if self._get_distance(self.mold, self.player) < self._get_distance(self.prev_mold, self.player):
                self.reward -= 2
            # if mold gets farther from player reward is positive
            elif self._get_distance(self.mold, self.player) > self._get_distance(self.prev_mold, self.player):
                self.reward += 2

            # if mold gets closer to butter reward is negative
            if self._get_distance(self.mold, self.butter) < self._get_distance(self.prev_mold, self.butter):
                self.reward -= 2
            # if mold gets farther from butter reward is positive
            elif self._get_distance(self.mold, self.butter) > self._get_distance(self.prev_mold, self.butter):
                self.reward += 2
            
    def _remove_possible_toaster(self):

        # if player is in toaster heat we can remove some positions
        if self.player in self.toaster_heat:
            self.known_heat.add(self.player)
            
            # increase reward for discovering heat
            self.reward += 2

        # remove current player position from possible toaster positions
        if self.player in self.possible_toaster and self.player != self.toaster:
            self.possible_toaster.remove(self.player)

        # remove mold position from possible toaster positions
        if self.mold in self.possible_toaster and self.mold != self.toaster:
            self.possible_toaster.remove(self.mold)

        if self.player == self.toaster:
            self.know_toaster = True
            self.possible_toaster = [self.toaster]

            # increase reward for discovering toaster
            self.reward += 15

        # if there's more than one possible toaster position we can remove some positions
        if len(self.possible_toaster) > 1:
            copy_possible_toaster = self.possible_toaster.copy()
            
            # remove positions that are not 2 distance from the heat
            for (x, y) in copy_possible_toaster:
                for heat in self.known_heat:
                    if (self._get_distance(Point(heat[0], heat[1]), Point(x, y)) != 2 and (x, y) in self.possible_toaster):
                        self.possible_toaster.remove(Point(x, y))

        # if there's only one possible toaster position we can know the toaster position
        if (len(self.possible_toaster) == 1) and self.know_toaster == False:
            self.know_toaster = True
            # increase reward for discovering toaster
            self.reward += 15

    def _init_possible_butter(self):
        possible_butter = []

        for (x, y) in self.valid_positions:
            if (x + y) == 2*self.distances[0][0]:
                possible_butter.append(Point(x, y))

        return possible_butter
    
    def _remove_possible_butter(self):
        possible_butter = self.possible_butter.copy()
        for (x, y) in possible_butter:
            if (self._get_distance(Point(x, y), self.player) != 2 * self.distances[self.player.x, self.player.y]) or (x,y) in self.mold_visited:
                self.possible_butter.remove(Point(x, y))

        if len(self.possible_butter) == 1 and self.know_butter == False:
            self.know_butter = True
            # increase reward for discovering butter
            self.reward += 10
                
    def _get_distance(self, p1, p2):
        return abs(p1.x - p2.x) + abs(p1.y - p2.y)

    def _is_game_over(self):

        # if player hits butter player wins
        if self.player == self.butter:
            self.display.fill(BLACK)
            text = pygame.font.Font(None, 36).render("You Win: player reached butter!", True, WHITE)
            self.display.blit(text, (self.w/4, self.h/4))
            pygame.display.flip()
            self.reward += 100
            self.game_over = True
            self.win_condition = WinCondition.PLAYER_HIT_BUTTER.value
        # if mold hits toaster player wins
        elif self.mold == self.toaster:
            self.display.fill(BLACK)
            text = pygame.font.Font(None, 36).render("You Win: mold reached toaster!", True, WHITE)
            self.display.blit(text, (self.w/4, self.h/4))
            pygame.display.flip()
            self.reward += 150
            self.game_over = True
            self.win_condition = WinCondition.MOLD_HIT_TOASTER.value
        # if player hits mold player loses
        elif self.player == self.mold:
            self.display.fill(BLACK)
            text = pygame.font.Font(None, 36).render("You Lose: player reached mold!", True, WHITE)
            self.display.blit(text, (self.w/4, self.h/4))
            pygame.display.flip()
            self.reward -= 100
            self.game_over = True
            self.win_condition = WinCondition.MOLD_HIT_PLAYER.value
        # if mold hits butter player loses
        elif self.mold == self.butter:
            self.display.fill(BLACK)
            text = pygame.font.Font(None, 36).render("You Lose: mold reached butter!", True, WHITE)
            self.display.blit(text, (self.w/4, self.h/4))
            pygame.display.flip()
            self.reward -= 100
            self.game_over = True
            self.win_condition = WinCondition.MOLD_HIT_BUTTER.value
        return False
            
        
    def _update_ui(self):

        self.display.fill(BLACK)

        # draw lines
        for x in range(0, int((self.grid_w + 1) / 2) + 1, 1):
            pygame.draw.line(self.display, WHITE, (x * GRID_SIZE * 2 + OFF_SET, 0 + OFF_SET), (x * GRID_SIZE * 2 + OFF_SET, self.h - OFF_SET), 2)
        for y in range(0, int((self.grid_h + 1) / 2) + 1, 1): 
            pygame.draw.line(self.display, WHITE, (0 + OFF_SET, y * GRID_SIZE * 2 + OFF_SET), (self.w - OFF_SET, y * GRID_SIZE * 2 + OFF_SET), 2)

        # draw toaster heat if is discovered
        for pos in self.known_heat:
            pygame.draw.rect(self.display, LIGHT_RED, (pos.x * GRID_SIZE + 2*OFF_SET, pos.y * GRID_SIZE + 2*OFF_SET, GRID_SIZE * 2 - 2*OFF_SET, GRID_SIZE * 2 - 2*OFF_SET))

         # draw possible butter positions
        for pos in self.possible_butter:
            pygame.draw.rect(self.display, YELLOW, (pos.x * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), pos.y * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), GRID_SIZE, GRID_SIZE))

        # draw player
        pygame.draw.rect(self.display, GREEN, (self.player.x * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), self.player.y * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), GRID_SIZE, GRID_SIZE))

        # draw mold
        pygame.draw.rect(self.display, BLUE, (self.mold.x * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), self.mold.y * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), GRID_SIZE, GRID_SIZE))

        # draw toaster
        if self.know_toaster:
            text_letter = pygame.font.Font(None, 36).render("T", True, WHITE)
            self.display.blit(text_letter, (self.toaster.x * GRID_SIZE + 2*GRID_SIZE - 2*OFF_SET, self.toaster.y * GRID_SIZE + OFF_SET * 2))

        # draw known barriers
        for barrier in self.known_barriers:
            # check if is an horizontal barrier or a vertical barrier
            if barrier.x % 2 == 0:
                pygame.draw.line(self.display, RED, (barrier.x * GRID_SIZE + OFF_SET, barrier.y * GRID_SIZE + OFF_SET + GRID_SIZE), (barrier.x * GRID_SIZE + OFF_SET + GRID_SIZE * 2, barrier.y * GRID_SIZE + OFF_SET + GRID_SIZE), 10)
            else:
                pygame.draw.line(self.display, RED, (barrier.x * GRID_SIZE + OFF_SET + GRID_SIZE, barrier.y * GRID_SIZE + OFF_SET), (barrier.x * GRID_SIZE + OFF_SET + GRID_SIZE, barrier.y * GRID_SIZE + OFF_SET + GRID_SIZE * 2), 10)

        # draw heuristic (distances to butter)
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                if self.distances[x, y] != -1 and Point(x, y) in self.visited_positions:
                    text_number = pygame.font.Font(None, 36).render(str(int(self.distances[x, y])), True, YELLOW)
                    self.display.blit(text_number, (x * GRID_SIZE + OFF_SET * 2, y * GRID_SIZE + OFF_SET * 2))

        pygame.display.flip()

        #wait for a while
        #pygame.time.wait(1000)

        self.clock.tick(FPS)
