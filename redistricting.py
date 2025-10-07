# Redistricting Analysis with GerryChain
# This script analyzes Pennsylvania’s voting district plans
# using the GerryChain library.
#
# Question 1: Compares three FiveThirtyEight plans (Dem-, GOP-, Compactness-favoring)
#              and computes Republican wins & efficiency gaps.
#
# Question 2: Runs a Markov Chain (ReCom) ensemble starting
#              from the compactness plan and measures distribution
#              of Republican wins and efficiency gaps.
#
# Output:
#   - Console summary of results
#   - Two histogram plots: rep_wins_hist.png, efficiency_gap_hist.png

# Imports
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# GerryChain imports
from gerrychain import Graph, Partition
from gerrychain.proposals import recom
from gerrychain.constraints import contiguous
from gerrychain.accept import always_accept



# config
PATH = "PA_VTDs.json"   # GerryChain JSON graph file
POP_COL = "TOT_POP"           # Total population column name
DEM_COL = "PRES12D"           # Democratic vote column (2012)
GOP_COL = "PRES12R"           # Republican vote column (2012)
PLAN_DEM = "538DEM_PL"        # 538 Democratic-favoring plan column
PLAN_GOP = "538GOP_PL"        # 538 Republican-favoring plan column
PLAN_CMP = "538CPCT__1"       # 538 Compactness-favoring plan column

# Ensemble parameters
ENSEMBLE_SIZE = 100           # Number of districting plans to generate
RECOM_EPSILON = 0.01          # Allowed population deviation (1%)
STEPS_BETWEEN_SAMPLES = 2     # Minimum steps between saved plans



# Compute Republican wins and efficiency gap for a given plan
def compute_republican_wins_and_efficiency_gap(df, plan_col):
    """
    Computes:
      - Number of Republican districts won
      - Efficiency gap (Republican - Democratic)

    Parameters:
        df (DataFrame): must contain columns for DEM_COL, GOP_COL, and plan_col (district ID)
        plan_col (str): column that encodes district IDs

    Returns:
        num_rep_wins (int)
        efficiency_gap (float)
    """
    # Aggregate vote totals by district
    agg = df.groupby(df[plan_col]).agg({DEM_COL: "sum", GOP_COL: "sum"})
    agg = agg.rename(columns={DEM_COL: "D", GOP_COL: "R"})
    agg["T"] = agg["D"] + agg["R"]
    agg = agg[agg["T"] > 0].copy()  # Skip districts with no votes

    # Count number of Republican-won districts
    num_rep_wins = int((agg["R"] > agg["D"]).sum())

    # Compute wasted votes and efficiency gap
    wasted_R, wasted_D = [], []
    for _, row in agg.iterrows():
        D, R, T = row["D"], row["R"], row["T"]
        half = T / 2.0
        if R > D:
            wasted_R.append(R - half)
            wasted_D.append(D)
        else:
            wasted_R.append(R)
            wasted_D.append(D - half)

    total_wasted_R = np.sum(wasted_R)
    total_wasted_D = np.sum(wasted_D)
    total_votes = agg["T"].sum()

    efficiency_gap = (total_wasted_R - total_wasted_D) / total_votes
    return num_rep_wins, efficiency_gap

# Main function
def main():
    # Load and validate the graph file
    if not os.path.exists(PATH):
        print(f"Graph file not found at {PATH}. Please set PATH correctly.")
        sys.exit(1)

    print("Loading GerryChain graph...")
    graph = Graph.from_json(PATH)

    print("Converting graph node data to DataFrame...")
    gdf = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient="index")

    # Ensure all required columns exist
    required_cols = {POP_COL, DEM_COL, GOP_COL, PLAN_DEM, PLAN_GOP, PLAN_CMP}
    missing = required_cols - set(gdf.columns)
    if missing:
        print("Missing required columns in graph:", missing)
        print("Available columns:", list(gdf.columns))
        sys.exit(1)

    print("Checking two-party vote totals for sanity...")
    gdf["T12"] = gdf[DEM_COL] + gdf[GOP_COL]
    print("Total two-party PRES12 votes across state:", int(gdf["T12"].sum()))
    print("Nonzero-VTD count:", int((gdf["T12"] > 0).sum()))


    # QUESTION 1: PARTITIONS & ELECTIONS
    # Compare the three FiveThirtyEight districting plans
    # (Democratic-favoring, Republican-favoring, and Compactness-favoring)
    # by computing:
    #   - Number of Republican-won districts
    #   - Efficiency gap for each plan

    print("\nQUESTION 1: Partitions & Elections\n")
    plans = [
        (PLAN_DEM, "FiveThirtyEight - Dem-favoring plan"),
        (PLAN_GOP, "FiveThirtyEight - GOP-favoring plan"),
        (PLAN_CMP, "FiveThirtyEight - Compactness-favoring plan"),
    ]

    for col, name in plans:
        wins, eg = compute_republican_wins_and_efficiency_gap(gdf, col)
        print(f"Plan: {name} (column = {col})")
        print(f"  -> Republican districts won (2012 two-party): {wins}")
        print(f"  -> Efficiency gap (Republican - Democratic) = {eg:.4f}")
        print("")

    # QUESTION 2: MARKOV CHAINS - RECOM ENSEMBLE
    # Use the ReCom (Recombination) algorithm to generate an
    # ensemble of districting plans, starting from the
    # compactness-favoring plan.
    #
    # Each sampled plan is used to compute:
    #   - Number of Republican districts won
    #   - Efficiency gap

    print("\nQUESTION 2: Markov Chains - ReCom ensemble (starting from compactness plan)\n")

    # Define updaters (calculate district populations and vote totals)
    updaters = {
        "population": lambda part: {
            k: sum(part.graph.nodes[n][POP_COL] for n in part.parts[k]) for k in part.parts
        },
        "PRES12D": lambda part: {
            k: sum(part.graph.nodes[n][DEM_COL] for n in part.parts[k]) for k in part.parts
        },
        "PRES12R": lambda part: {
            k: sum(part.graph.nodes[n][GOP_COL] for n in part.parts[k]) for k in part.parts
        },
    }

    # Create an initial Partition using the compactness plan
    print("Constructing initial Partition object from compactness plan...")
    assignment = {node: graph.nodes[node][PLAN_CMP] for node in graph.nodes}
    initial_partition = Partition(graph, assignment, updaters=updaters)

    # Compute ideal population per district
    num_districts = len(set(initial_partition.assignment.values()))
    total_pop = sum(graph.nodes[n][POP_COL] for n in graph.nodes)
    ideal_pop = total_pop / num_districts
    print(f"Number of districts: {num_districts}")
    print(f"Total state population: {total_pop}")
    print(f"Ideal population per district: {ideal_pop:.2f}")

    # Initialize ensemble collection variables
    print("Running the Markov chain and collecting an ensemble of plans...")
    ensemble_rep_wins = []
    ensemble_egs = []

    current = initial_partition
    steps_between = STEPS_BETWEEN_SAMPLES
    samples_collected = 0
    steps_taken = 0
    MAX_STEPS = ENSEMBLE_SIZE * steps_between * 5
    rng = np.random.default_rng(42)  # For reproducibility

    # Run the Markov chain to generate new valid plans
    while samples_collected < ENSEMBLE_SIZE and steps_taken < MAX_STEPS:
        # Propose a new plan using ReCom
        new_part = recom(
            current, pop_col=POP_COL, pop_target=ideal_pop, epsilon=RECOM_EPSILON
        )
        current = new_part
        steps_taken += 1

        # Save sample
        if steps_taken % steps_between == 0:
            node_to_district = current.assignment
            temp = pd.DataFrame.from_dict(node_to_district, orient="index", columns=["district"])
            merged = gdf.join(temp, how="left")

            # Compute election metrics for this sampled plan
            wins, eg = compute_republican_wins_and_efficiency_gap(merged, "district")
            ensemble_rep_wins.append(wins)
            ensemble_egs.append(eg)
            samples_collected += 1
            print(f"Collected sample {samples_collected}/{ENSEMBLE_SIZE}: wins={wins}, eg={eg:.4f}")

    if samples_collected < ENSEMBLE_SIZE:
        print("WARNING: Did not collect the requested number of samples. Collected:", samples_collected)

    # Plot histogram of Republican wins
    max_possible = max(ensemble_rep_wins) if ensemble_rep_wins else 0
    min_possible = min(ensemble_rep_wins) if ensemble_rep_wins else 0
    bins = range(min_possible, max_possible + 2)

    plt.figure()
    plt.hist(ensemble_rep_wins, bins=bins, edgecolor="black")
    plt.title("Histogram of Republican wins in ReCom ensemble")
    plt.xlabel("Number of Republican wins")
    plt.ylabel("Number of plans")
    plt.xticks(list(bins))
    plt.savefig("rep_wins_hist.png")
    print("Saved histogram of Republican wins to rep_wins_hist.png")

    # Plot histogram of efficiency gaps
    plt.figure()
    plt.hist(ensemble_egs, bins=20, edgecolor="black")
    plt.title("Histogram of efficiency gaps in ReCom ensemble (Rep - Dem)")
    plt.xlabel("Efficiency gap")
    plt.ylabel("Number of plans")
    plt.savefig("efficiency_gap_hist.png")
    print("Saved histogram of efficiency gaps to efficiency_gap_hist.png")

    # Print a simple histogram summary in text
    max_seats = max(ensemble_rep_wins) if ensemble_rep_wins else 0
    poor_mans = [ensemble_rep_wins.count(i) for i in range(0, max_seats + 1)]
    print("\nPoor-man histogram (index = number of Republican seats -> count):")
    for seats, count in enumerate(poor_mans):
        print(f"  {seats} seats: {count} plans")

    print("\nDone. Files produced: rep_wins_hist.png, efficiency_gap_hist.png")
    print("Q1 results printed above.")


# Entry point
if __name__ == "__main__":
    main()
