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

# Point
Point = namedtuple('Point', 'x, y')

# Game settings
OFF_SET = 10
GRID_SIZE = 50
FPS = 60

class MazeGame:

    def __init__(self, grid_w = 11, grid_h = 11):
        
        # initialize grid
        self._initialize_grid(grid_w, grid_h)

        # initialize positions
        self._initialize_positions(grid_w, grid_h)

        # initialize what player knows of the game
        self._initialize_game_state()

        
    def _initialize_grid(self, grid_w, grid_h):
        # init display
        self.w = GRID_SIZE * (grid_w + 1) + 2*OFF_SET
        self.h = GRID_SIZE * (grid_h + 1) + 2*OFF_SET
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Maze Game")
        self.clock = pygame.time.Clock()

    def _initialize_positions(self, grid_w, grid_h):
        # init player position
        self.player = Point(0, 0)
        self.score = 0
        
        # valid positions for everyone
        self.valid_positions = [Point(x, y) for x in range(0, grid_w, 2) for y in range(0, grid_h, 2)]
        self.valid_positions.remove(self.player)

        # bolor position
        self.mold = Point(10,10)
        self.valid_positions.remove(self.mold)

        # toaster position
        #self.toaster = random.choice(self.valid_positions)
        self.toaster = Point(2,0)
        self.toaster_heat = [(self.toaster.x + 2, self.toaster.y), (self.toaster.x - 2, self.toaster.y), (self.toaster.x, self.toaster.y + 2), (self.toaster.x, self.toaster.y - 2)]

        # butter positions
        self.butter = random.choice(self.valid_positions)

        # valid positions for barriers
        self.valid_barriers = set(Point(x, y) for x in range(grid_w) for y in range(grid_h) if (x % 2 != 0) != (y % 2 != 0))
        self.barriers = []

        # add barriers to test
        self.barriers.append(Point(0, 1))
        self.barriers.append(Point(3, 0))

    def _initialize_game_state(self):

        # set player direction
        self.direction = Direction.RIGHT

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

        # possible possitions of the butter
        self.distances = self._calculate_distances()
        self.possible_butter = self._init_possible_butter()

        # visited mold positions
        self.mold_visited = set()
        self.mold_visited.add(self.mold)

        # mold path
        self.mold_path = []


    def play_step(self):

        # reveal barriers on player position
        self._reveal_barriers()

        # update state
        self._update_state()

        # update ui and clock
        self._update_ui()

        # 1. collect user input
        has_decided = False
        while has_decided == False:

            pygame.event.clear()
            event = pygame.event.wait()

            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    if (Point(self.player.x, self.player.y - 1) not in self.known_barriers):
                        self.direction = Direction.UP
                        has_decided = True
                if event.key == pygame.K_DOWN:
                    if (Point(self.player.x, self.player.y + 1) not in self.known_barriers):
                        self.direction = Direction.DOWN
                        has_decided = True
                if event.key == pygame.K_LEFT:
                    if (Point(self.player.x - 1, self.player.y) not in self.known_barriers):
                        self.direction = Direction.LEFT
                        has_decided = True
                if event.key == pygame.K_RIGHT:
                    if (Point(self.player.x + 1, self.player.y) not in self.known_barriers):
                        self.direction = Direction.RIGHT
                        has_decided = True

                # exit game
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    quit()
            
            if (has_decided):
                break

        # 2. move
        self._move()

        self._update_state()

        # 3. check if game over
        game_over = False
        if self._is_game_over():
            game_over = True
            return game_over, self.score

        # 4. update ui and clock
        self._update_ui()

        # 5. return game over and score
        return game_over, self.score
    
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
            if Point(self.player.x + direction[0], self.player.y + direction[1]) in self.barriers:
                self.known_barriers.add(Point(self.player.x + direction[0], self.player.y + direction[1]))
    
    def _move(self):

        if (self.player_wait == False):
            if self.direction == Direction.RIGHT:
                self.player = Point(self.player.x + 2, self.player.y)
            if self.direction == Direction.LEFT:
                self.player = Point(self.player.x - 2, self.player.y)
            if self.direction == Direction.UP:
                self.player = Point(self.player.x, self.player.y - 2)
            if self.direction == Direction.DOWN:
                self.player = Point(self.player.x, self.player.y + 2)

            # add player to visited positions
            self.visited_positions.add(self.player)

        # move mold
        self._move_mold()

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
                self.mold = Point(self.mold.x, self.mold.y - 2)
        elif dist_down <= dist_up and dist_down <= dist_left and dist_down <= dist_right:
            if (self.mold.y < self.grid_h - 1):
                self.mold = Point(self.mold.x, self.mold.y + 2)
        elif dist_left <= dist_up and dist_left <= dist_down and dist_left <= dist_right:
            if (self.mold.x > 0):
                self.mold = Point(self.mold.x - 2, self.mold.y)
        elif dist_right <= dist_up and dist_right <= dist_down and dist_right <= dist_left:
            if (self.mold.x < self.grid_w - 1):
                self.mold = Point(self.mold.x + 2, self.mold.y)

        # add mold to visited positions
        self.mold_visited.add(self.mold)

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


    def _remove_possible_toaster(self):

        # if player is in toaster heat we can remove some positions
        if self.player in self.toaster_heat:
            self.known_heat.add(self.player)

        # remove current player position from possible toaster positions
        if self.player in self.possible_toaster and self.player != self.toaster:
            self.possible_toaster.remove(self.player)

        # remove mold position from possible toaster positions
        if self.mold in self.possible_toaster and self.mold != self.toaster:
            self.possible_toaster.remove(self.mold)

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

    def _init_possible_butter(self):
        possible_butter = []

        for (x, y) in self.valid_positions:
            if (x + y) == 2*self.distances[0][0]:
                possible_butter.append(Point(x, y))

        return possible_butter
    
    def _remove_possible_butter(self):
        for (x, y) in self.possible_butter:
            if (self._get_distance(Point(x, y), self.player) != 2 * self.distances[self.player.x, self.player.y]):
                self.possible_butter.remove(Point(x, y))
                
    def _get_distance(self, p1, p2):
        #print("Distance from ", p1, " to ", p2, " is ", abs(p1.x - p2.x) + abs(p1.y - p2.y))
        return abs(p1.x - p2.x) + abs(p1.y - p2.y)

    def _is_game_over(self):

        # if player hits butter player wins
        # if mold hits toaster player wins
        # if player hits mold player loses
        # if mold hits butter player loses

        if self.player == self.butter or self.mold == self.toaster or self.player == self.mold or self.mold == self.butter:
            return True
        
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
            pygame.draw.rect(self.display, RED, (self.toaster.x * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), self.toaster.y * GRID_SIZE + OFF_SET + int(GRID_SIZE/2), GRID_SIZE, GRID_SIZE))

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

        self.clock.tick(FPS)
        

if __name__ == "__main__":
    game = MazeGame()
    
    # Game loop
    while True:
        game_over, score = game.play_step()

        if game_over:
            break

    pygame.quit()
