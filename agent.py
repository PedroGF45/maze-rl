import torch
import random
import numpy as np
from collections import deque
from game_train import MazeGame, Direction, Point
from model import Linear_QNet, QTrainer
from helper import plot_reward, plot_bar

# constants
MAX_MEMORY = 100000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0                                               # number of games played
        self.epsilon = 0                                                # controls randomness
        self.gamma = 0.9                                                # discount factor
        self.memory = deque(maxlen=MAX_MEMORY)                          # replay memory    
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
        print(f"Using device: {self.device}")                  
        self.model = Linear_QNet(288, 256, 4)                          # neural network model
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)    # optimizer
        self.game = None                                               # game object

    def get_state(self, game):
        
        state = game.get_state()

        return state

    # store experience in memory
    def remember(self, state, action, reward, next_state, is_done):
        self.memory.append((state, action, reward, next_state, is_done))

    # train neural network model
    def train_long_memory(self):
        # get a random sample of experiences if memory has more than BATCH_SIZE
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        # unpack experience
        states, actions, rewards, next_states, is_dones = zip(*mini_sample)

        # train model
        self.trainer.train_step(states, actions, rewards, next_states, is_dones)

    # train neural network model
    def train_short_memory(self, state, action, reward, next_state, is_done):
        self.trainer.train_step(state, action, reward, next_state, is_done)

    # get action from model using epsilon-greedy policy
    def get_action(self, state):
        
        # to explore we need to choose a random action
        self.epsilon = 80 - self.n_games # set epsilon to decrease as games are played

        action = [0, 0, 0, 0] # initialize action

        if random.randint(0, 200) < self.epsilon:
            # Explore: Choose a random valid action
            while True:
                move = random.randint(0, 3)
                action = [0] * 4
                action[move] = 1
                if self.game.is_action_valid(action):  # Check validity before returning
                    break
        else:
            # Exploit: Get action from model
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0) 

            # Find the index of the action with the highest predicted value
            max_action_index = torch.argmax(prediction).item() 

            # If the predicted action is invalid, choose the second-best action
            if not self.game.is_action_valid([0, 0, 0, 0, 1][max_action_index]): 
                # Find the indices of all actions sorted by predicted value
                sorted_indices = torch.argsort(prediction, descending=True) 

                # Find the first valid action in the sorted order
                for i in sorted_indices:
                    action = [0] * 4
                    action[i.item()] = 1
                    if self.game.is_action_valid(action):
                        break
        return action

def train():
    plot_scores = []        # list containing scores
    plot_mean_scores = []   # list containing mean scores
    plot_wins_losses = [0, 0, 0, 0, 0, 0, 0]    # list containing 4 types od results and wins and losses and ties
    total_score = 0         # initialize total score
    record = 0              # initialize record
    agent = Agent()         # initialize agent
    game = MazeGame()       # initialize game
    agent.game = game       # set agent game to game

    print("Butter position: ", game.butter)
    print("Toaster position: ", game.toaster)

    # training loop
    while True:
        trying_count = 0
        # get current state
        current_state = agent.get_state(game)
        # get agent action
        is_action_valid = False
        is_done = False
        while not is_action_valid:

            if game.is_action_impossible() or trying_count > 25:
                is_done = True
                win_condition = 5
                reward = -100
                break

            agent_action = agent.get_action(current_state)
            is_action_valid = game.is_action_valid(agent_action)
            if not is_action_valid:
                game.reward -= -1  # This line might need adjustment based on your game logic
                trying_count += 1


        if not is_done:

            # perform agent action
            reward, is_done, win_condition = game.play_step(agent_action)

            # get new state
            new_state = agent.get_state(game)

        # remember experience for short memory
        agent.train_short_memory(current_state, agent_action, reward, new_state, is_done)
        # remember experience
        agent.remember(current_state, agent_action, reward, new_state, is_done)

        if is_done:

             # train long memeory / experience replay
            game.reset(agent.n_games + 1) # reset game state

            # train long memory
            agent.train_long_memory()

            # check for new record
            if reward > record:
                record = reward
                agent.model.save()

            # check for win condition
            if win_condition == 1:
                plot_wins_losses[0] += 1
                plot_wins_losses[4] += 1
                text = "Player wins by hitting butter"
            elif win_condition == 2:
                plot_wins_losses[1] += 1
                plot_wins_losses[4] += 1
                text = "Player wins by mold hitting toaster"
            elif win_condition == 3:
                plot_wins_losses[2] += 1
                plot_wins_losses[5] += 1
                text = "Player loses by hitting mold"
            elif win_condition == 4:
                plot_wins_losses[3] += 1
                plot_wins_losses[5] += 1
                text = "Player loses by mold hitting butter"
            elif win_condition == 5:
                plot_wins_losses[6] += 1
                text = "Tie"

            # print results
            print(f'Game: {agent.n_games}, Reward: {reward}, Record: {record}, Result: {text}')
            # increment number of games played
            agent.n_games += 1

            # plot results
            plot_scores.append(reward)
            total_score += reward
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot_reward(plot_scores, plot_mean_scores)
            # plot win condition
            plot_bar(plot_wins_losses)

if __name__ == '__main__':
    train()
