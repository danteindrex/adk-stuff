import os

# Define the datasets folder path
datasets_folder = 'datasets'

# Define the output file paths
train_file = 'train.txt'
validation_file = 'validation.txt'

# Define the split ratio (e.g., 80% for training, 20% for validation)
split_ratio = 0.8

# Get a list of all txt files in the datasets folder
txt_files = [f for f in os.listdir(datasets_folder) if f.endswith('.txt')]

# Initialize the train and validation lists
train_data = []
validation_data = []

# Iterate through the txt files and split the data
for file in txt_files:
    file_path = os.path.join(datasets_folder, file)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read().splitlines()
        train_size = int(len(data) * split_ratio)
        train_data.extend(data[:train_size])
        validation_data.extend(data[train_size:])

# Write the train and validation data to files
with open(train_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(train_data))

with open(validation_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(validation_data))

print(f'Train data saved to {train_file}')
print(f'Validation data saved to {validation_file}')