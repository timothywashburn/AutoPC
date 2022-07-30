import torch
from torch import nn
from torch import optim
import torch.nn.functional as F
import pandas as pd
import numpy as np
from utils import custom_round
from torch.utils.data import Dataset
from utils import colored

test_examples = 300
save = True
no_lives = True

device = "cuda"
column_num = 49 if no_lives else 51


class PriceCheckDataset(Dataset):
    def __init__(self, train):
        file_out = pd.read_csv("pitdata.csv")
        if train:
            self.X = torch.tensor(file_out.iloc[1:-test_examples, 3 if no_lives else 1:].values, dtype=torch.float32)
            self.y = torch.tensor(file_out.iloc[1:-test_examples, 0].values)
        else:
            self.X = torch.tensor(file_out.iloc[-test_examples:, 3 if no_lives else 1:].values, dtype=torch.float32)
            self.y = torch.tensor(file_out.iloc[-test_examples:, 0].values)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, index):
        return self.X[index], self.y[index]


class PriceCheckNetwork(nn.Module):

    def __init__(self):
        super().__init__()

        self.fc1 = nn.Linear(column_num, 96)
        self.fc2 = nn.Linear(96, 64)
        self.fc3 = nn.Linear(64, 64)
        self.classifier = nn.Linear(64, 1)

        self.dropout = nn.Dropout(p=0.15)

    def forward(self, x):
        x = x.view(x.shape[0], -1)

        x = self.dropout(F.relu(self.fc1(x)))
        x = self.dropout(F.relu(self.fc2(x)))
        x = self.dropout(F.relu(self.fc3(x)))
        x = self.classifier(x)

        return x


epochs = 150
batch_size = 50
learning_rate = 0.001
test_every = 200

model = PriceCheckNetwork().to(device)
optimizer = optim.Adam(model.parameters(), lr=learning_rate)
criterion = nn.MSELoss()
train_loader = torch.utils.data.DataLoader(PriceCheckDataset(train=True), batch_size=batch_size, shuffle=True)
test_loader = torch.utils.data.DataLoader(PriceCheckDataset(train=False), batch_size=batch_size, shuffle=True)

step = 0
first = True
average_loss = np.zeros([50])
if __name__ == "__main__":
    for epoch in range(epochs):
        for items, labels in train_loader:
            step += 1

            items, labels = items.to(device), labels.type(torch.FloatTensor).to(device)
            predictions = model.forward(items)
            loss = criterion(predictions, labels.view(-1, 1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            average_loss[step % 50] = loss.data.cpu().numpy()
            if step % test_every == 0 and step > 50:
                with torch.no_grad():
                    model.eval()
                    test_pbs_loss = None
                    test_loss = []
                    itemCount = 0
                    real_item = None
                    for items, labels in test_loader:
                        itemCount += len(items)
                        items, labels = items.to(device), labels.type(torch.FloatTensor).to(device)
                        predictions = model.forward(items)
                        loss = criterion(predictions, labels.view(-1, 1))
                        test_pbs_loss = torch.abs(predictions - labels.view(-1, 1)).sum().item()
                        test_loss.append(loss.data.cpu().numpy())

                    model.train()

                    print(f"\nTest PBs Loss: {custom_round(test_pbs_loss / itemCount, 1)}")
                    print(f"Test Loss: {colored(255, 150, 150, custom_round(np.array(test_loss).mean(), 1))}")
                    print(f"Train Loss: {colored(150, 255, 150, custom_round(average_loss.mean(), 1))}")
                    print(f"Epoch: {epoch + 1}")

    if save:
        torch.save(model.state_dict(), "trained-network.pth")
        print("Saved network to file")
