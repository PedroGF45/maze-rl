import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from IPython import display
matplotlib.use("QtAgg")
plt.ion()

fig_reward, ax_reward = plt.subplots()
fig_bar, ax_bar = plt.subplots()

def plot_reward(scores, mean_scores):
    """Plots the training progress with scores and mean scores."""
    ax_reward.clear() 
    #ax_reward.title('Training...')
    ax_reward.set_xlabel('Number of games')
    ax_reward.set_ylabel('Score')
    ax_reward.plot(scores)
    ax_reward.plot(mean_scores)
    ax_reward.text(len(scores) - 1, scores[-1], str(scores[-1]))
    ax_reward.text(len(mean_scores) - 1, mean_scores[-1], str(mean_scores[-1]))
    plt.show(block=False)
    fig_reward.savefig('plot_reward.png')

def plot_bar(data):
    """Plots a bar graph for the provided data."""
    ax_bar.clear()

    # Extract categories from data labels (assuming labels are present)
    categories = ["PLAYER HITS BUTTER", "MOLD HITS TOASTER", "PLAYER HITS MOLD", "MOLD HITS BUTTER", "WINS", "LOSSES", "TIES"]

    # Set the width of the bars
    bar_width = 0.2

    # Create positions for each bar (dynamically based on data length)
    num_bars = len(data)
    r = np.arange(num_bars)

    # Create the bar plot using a loop for dynamic data handling
    colors = ['g', 'g', 'r', 'r', 'g', 'r', 'y']  # Define a color list for the bars
    for i in range(num_bars):
        ax_bar.bar(r[i], data[i], color=colors[i], width=bar_width, edgecolor='grey', label=categories[i])
        ax_bar.text(r[i], data[i], str(data[i]), ha='center', va='bottom')

    # Customize the plot
    ax_bar.set_xlabel('Categories' if categories else 'Index')
    ax_bar.set_ylabel('Values')
    ax_bar.set_title('Multiple Bar Plot')
    if categories:
        ax_bar.set_xticks(r + bar_width / 2, categories)  # Center x-axis labels with categories
    else:
        ax_bar.set_xticks(r + bar_width / 2)  # Center x-axis labels with indices
    ax_bar.legend()

    plt.show(block=False)
    fig_bar.savefig('plot_bar.png')

