REDISTRICTING ANALYSIS: PENNSYLVANIA GERRYCHAIN\
------------------------------------------------

This Python script performs a redistricting analysis for **Pennsylvania** congressional districts using the **GerryChain** library. It serves two main purposes: comparing specific, pre-existing plans and analyzing the political characteristics of an ensemble of randomly generated plans.

PURPOSE AND FEATURES
--------------------
This script addresses key questions in redistricting analysis by:

1.  **Comparing Three Plans (Question 1):** Analyzing three pre-drawn FiveThirtyEight-designed plans (Democrat-favoring, Republican-favoring, and Compactness-favoring) based on 2012 Presidential election data.
2.  **Running an Ensemble (Question 2):** Generating a random ensemble of valid, population-balanced redistricting plans using the **ReCom** (Recombination) Markov Chain algorithm, starting from the compactness-favoring plan.
3.  **Measuring Partisan Metrics:** Computing the **Republican districts won** and the **Efficiency Gap** for both the fixed plans and all plans in the ensemble.
4.  **Visualizing Results:** Outputting a statistical summary to the console and two histograms to visualize the ensemble's distribution of partisan outcomes.

PREREQUISITES
-------------
To run this analysis, you must have **Python 3.x** installed and a few key libraries.

1.  **Install Python Packages:**
    pip install pandas numpy matplotlib gerrychain

2.  **Data File:** You need the GerryChain-formatted graph file for Pennsylvania, **PA_VTDs.json**, located in the same directory as the script. I have this in the repo already.

-----------------------------------------------------

HOW TO RUN THE SCRIPT
---------------------
1.  Ensure all packages installed, PA_VTDs.json file present.
2.  Run the following in your terminal in order-
        $  python3 -m venv .venv
        $  source .venv/bin/activate
        $  pip3 install pandas numpy matplotlib gerrychain geopandas

3.  Execute the script from your terminal:

    python3 redistricting.py

-----------------------------------------------------

OUTPUT
------
The script prints a summary of the analysis to the console and generates two image files:

* **Console Output (Q1):** Prints the **Republican wins** and **Efficiency Gap** for the three fixed 538 plans.
* **Console Output (Q2):** Reports the progress of the **Markov Chain** and a final text-based "poor-man histogram" of the ensemble results.
* **rep_wins_hist.png:** A histogram showing the **distribution of Republican wins** across the 100 ReCom ensemble plans.
* **efficiency_gap_hist.png:** A histogram showing the **distribution of Efficiency Gaps** across the 100 ReCom ensemble plans.

-----------------------------------------------------

KEY CODE COMPONENTS (Referencing Script Comments)
---------------------------------

| Component | Description | Code Reference |
|-----------|-------------|----------------|
| Configuration | Defines file paths, data column names (POP_COL, DEM_COL, PLAN_GOP, etc.), and Markov Chain parameters (ENSEMBLE_SIZE, RECOM_EPSILON). **To analyze a different state or election, edit these constants.** | Lines 16-30 |
| compute_republican_wins_and_efficiency_gap | A function to calculate the core partisan metrics—Republican seats won and the Republican-to-Democrat Efficiency Gap—for any given redistricting plan stored in a DataFrame. | Lines 33-72 |
| Question 1: Fixed Plans | Loads the data, then calls the analysis function on the three known FiveThirtyEight plans to compare their partisan biases. | Lines 81-93 |
| Question 2: Markov Chain | Defines **Updaters** to dynamically calculate population and vote totals for new districts, initializes the **Partition** from the compactness plan, and runs the **ReCom** (Recombination) algorithm to generate the ensemble of plans. | Lines 98-142 |
| Plotting | Uses **matplotlib.pyplot** to generate and save the two histogram visualizations. | Lines 144-155 |

-----------------------------------------------------

TECHNICAL DETAILS
-----------------
* **ReCom Proposal:** The `recom()` function is a **proposal** that generates a new, population-balanced plan by merging and re-splitting two adjacent districts.
* **Ensemble Collection:** The Markov Chain is set to take **2** steps (`STEPS_BETWEEN_SAMPLES`) between saving each of the **100** (`ENSEMBLE_SIZE`) samples to ensure they are sufficiently independent.

-----------------------------------------------------

*END OF README*