# Visual Perception — Week 2 Assignments

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-notebooks-F37626?logo=jupyter&logoColor=white)
![matplotlib](https://img.shields.io/badge/matplotlib-OO%20API-11557c)
![Course](https://img.shields.io/badge/Data%20Visualization-Week%202-blue)

Five Jupyter notebooks on **how the human brain processes visual information** and what that means for chart design:
preattentive attributes, Gestalt grouping, cognitive load, channel effectiveness, and a capstone redesign.
Every chart is built with the object-oriented matplotlib API (`fig, ax = plt.subplots()`), and every notebook explains
*what the eye does and why*, not just what the code draws.

<p align="center">
  <img src="perception_redesign.png" width="720" alt="Capstone redesign: Rwanda's 1992 life expectancy collapse highlighted against 141 grey country lines">
</p>

## Notebooks

| # | Notebook | Topic | Data |
|---|---|---|---|
| 1 | [`task1.ipynb`](task1.ipynb) | Preattentive attributes and visual search (parallel vs serial) | `stimuli_search.csv` |
| 2 | [`task2.ipynb`](task2.ipynb) | Gestalt principles; connection vs proximity vs similarity | `stimuli_gestalt.csv`, `tips.csv` |
| 3 | [`task3.ipynb`](task3.ipynb) | Cognitive load, data-ink ratio, the 4 ± 1 limit | `car_crashes.csv`, `tips.csv` |
| 4 | [`task4.ipynb`](task4.ipynb) | Channel effectiveness (Cleveland & McGill, small scale) | `channel_trials.csv`, `iris.csv` |
| 5 | [`task5.ipynb`](task5.ipynb) | Capstone: perception audit and redesign | `gapminder.csv` |

## Status

Tasks 1, 2, 4 and the Task 5 reader test involve timing or questioning a real person. Those parts are **not simulated**:
the experiment code and analysis are written, and the cells that need participant data stay empty until you run them.

| Task | Complete | Needs participant data |
|---|---|---|
| 1 | Stimulus renderer, trial selection, experiment runner, slope analysis code, written explanation | Run the experiment → `search_results.csv` (response-time chart and slopes appear on re-run) |
| 2 | Six-panel figure, connection test, tips proximity chart, written answers | Reader's group counts and connection-test answers |
| 3 | **Everything** | None |
| 4 | Five channel encodings, experiment runner, ranking code, iris two-channel chart, written answers | Run the 30 trials → `channel_results.csv` (ranking appears on re-run) |
| 5 | Bad chart, both audit tables, redesign, 300 DPI export, written answers | Reader's one-sentence reading of the redesign |

## Gallery

| | |
|---|---|
| <img src="task2_six_panels.png" alt="Six Gestalt panels"> **Task 2** — six grouping cues | <img src="task3_five_panel_strip.png" alt="Five-step de-cluttering of a 51-bar chart"> **Task 3** — five subtractions |
| <img src="task4_iris_two_channels.png" alt="Same iris finding on position and on area"> **Task 4** — position vs area | <img src="task1_step1_render_check.png" alt="Search stimuli: colour, shape, conjunction"> **Task 1** — colour, shape, conjunction |

## Highlights

- **Task 1:** one renderer draws any of the 90 search trials; the runner blocks by condition and times responses with `time.perf_counter()`.
- **Task 2:** in the connection panel only 31% of items have their partner as nearest neighbour and 0% of pairs share a colour, so the connecting line has to beat both proximity and similarity.
- **Task 3:** the overloaded bar chart has a data-ink ratio of 0.13 (0.15 if the y-axis scale is counted as data ink), counted directly from the figure's marks. Sorting the bars is shown to be the largest single improvement and adds no ink. Regional chunking (4 bars) is used for the 4 ± 1 limit.
- **Task 5:** exactly one pop-out (Rwanda, 1992, 23.6 years, the lowest value in the dataset). Similarity is the named Gestalt principle, and the key variable sits on position.

## Getting started

```bash
git clone <this-repo-url>
cd <repo>/week2/assignments

pip install pandas numpy matplotlib seaborn scipy pillow jupyter ipykernel
python3 download_assignment_data.py     # downloads 5 datasets, generates 3 stimulus files (SEED = 42)
jupyter notebook
```

Put the `taskN.ipynb` files in `week2/assignments/` beside `data/`. The notebooks also find `assignments/data/` and `week2/assignments/data/`.
Open and run each notebook top to bottom. The experiment cells use `input()`, so run them in Jupyter.

### Running an experiment (Tasks 1 and 4)

1. In Step 2 of the notebook, set `PARTICIPANT` / `READER` and `RUN_EXPERIMENT = True`.
2. Run the cell and hand the laptop to a participant (one classmate, flatmate or family member is enough).
3. The results are saved as `search_results.csv` or `channel_results.csv`. Re-run the notebook to fill in the analysis.

## Repository layout

```
week2/assignments/
├── README.md
├── TASKS.md                        # original brief
├── download_assignment_data.py     # data download + stimulus generation (SEED = 42, unchanged)
├── data/                           # created by the script
├── task1.ipynb … task5.ipynb
├── perception_redesign.png         # Task 5 export, 300 DPI
└── task*_*.png                     # figures saved by the notebooks
```

## Design decisions worth knowing

- **Task 1 uses 18 trials, not the brief's wording.** "Two per condition × set size cell" would be 30; I used 3 conditions × 3 set sizes (9, 25, 49) × present/absent = 18. Change `SET_SIZES_USED` for 30.
- **Task 3 chunking uses Census regions**, with DC counted in the South, so the reader holds four chunks. The cost (hidden within-region spread) is stated in the notebook.
- **Seeds:** the stimulus `SEED = 42` is untouched. Task 1 and 4 use separate generators only for trial order.

## Requirements

Python 3.9+, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `pillow`, `jupyter`, `ipykernel`.

## Acknowledgements

Course brief and datasets from the Week 2 materials. Datasets are public (seaborn-data, Gapminder). Channel ranking after
Cleveland & McGill (1984).
