import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os
import numpy as np

class Linear_QNet(nn.Module):

    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, hidden_size)
        self.linear3 = nn.Linear(hidden_size, output_size)

    # forward pass
    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = F.relu(self.linear2(x))
        x = self.linear3(x)
        return x
    
    # save model
    def save(self, file_name='model.pth'):
        model_folder_path = './model'

        # if folder does not exist, create it
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)

        # save model to file
        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)

class QTrainer:

    def __init__(self, model, lr, gamma):
        self.model = model
        self.lr = lr
        self.gamma = gamma
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criteria = nn.MSELoss()

    def train_step(self, state, action, reward, next_state, is_done):
        # convert to tensors
        state = np.array(state, dtype=np.float32)
        state = torch.tensor(state, dtype=torch.float)
        next_state = np.array(next_state, dtype=np.float32)
        next_state = torch.tensor(next_state, dtype=torch.float)
        action = torch.tensor(action, dtype=torch.long)
        reward = torch.tensor(reward, dtype=torch.float)

        if len(state.shape) == 1:
            # add a batch dimension
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            is_done = (is_done, )

        # predicted Q values
        pred = self.model(state)

        target = pred.clone()
        for idx in range(len(is_done)):
            Q_new = reward[idx]
            if not is_done[idx]:
                Q_new = reward[idx] + self.gamma * torch.max(self.model(next_state[idx]))

            target[idx][torch.argmax(action).item()] = Q_new

        # calculate loss
        self.optimizer.zero_grad()
        loss = self.criteria(target, pred)
        loss.backward()

        # update model
        self.optimizer.step()
