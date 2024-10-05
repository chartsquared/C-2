import os
import yaml
from collections import defaultdict
from scipy.stats import skew
import numpy as np


def get_group_from_filename(filename):
    # Split the filename by underscores and look at the second to last element
    try:
        parts = filename.split('_')
        group_identifier = parts[-2]  # Second to last element
        if group_identifier == "50":
            return "50w"
        elif group_identifier == "100":
            return "100w"
    except IndexError:
        pass
    return None


def traverse_and_collect_statistics(root_dir):
    # Data structures to hold word counts for each group
    word_counts = defaultdict(list)

    # Walk through the directory structure
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            print(file)
            if file.endswith(".yaml"):
                # Determine the group (50w or 100w) based on the filename's exact position
                group = get_group_from_filename(file)
                if group is None:
                    continue

                # Full path to the YAML file
                file_path = os.path.join(subdir, file)

                # Load the YAML file and extract the word count
                with open(file_path, 'r') as yaml_file:
                    try:
                        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
                    except yaml.YAMLError as e:
                        print(f"Error loading YAML file {file_path}: {e}")
                        continue

                    if "02_initial_prompt" in data:
                        prompt = data["02_initial_prompt"]
                        word_count = len(prompt.split())
                        word_counts[group].append(word_count)

    return word_counts


def calculate_statistics(word_counts):
    stats = {}
    for group, counts in word_counts.items():
        mean = np.mean(counts)
        std_dev = np.std(counts)
        skewness = skew(counts)
        stats[group] = {
            "mean": mean,
            "std_dev": std_dev,
            "skewness": skewness
        }
    return stats


def main():
    root_dir = '.'  # Set the root directory to the current directory
    word_counts = traverse_and_collect_statistics(root_dir)
    stats = calculate_statistics(word_counts)

    # Print the results
    for group, group_stats in stats.items():
        print(f"Statistics for {group}:")
        print(f"Mean: {group_stats['mean']}")
        print(f"Standard Deviation: {group_stats['std_dev']}")
        print(f"Skewness: {group_stats['skewness']}")
        print()


if __name__ == "__main__":
    main()
