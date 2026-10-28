# Data Visualization Assignment 01

This folder contains five Jupyter notebooks focused on visualizing different kinds of data patterns. Each notebook works with one of the CSV files in the `week 01 dataset` folder and demonstrates how to choose, build, and interpret charts for exploratory data analysis.

## Project overview

The assignment covers the following five tasks:

1. `datasaurus.ipynb` — shows why summary statistics alone can be misleading.
2. `gapminder.ipynb` — explores long-term trends and the “spaghetti plot” problem with many lines.
3. `flights.ipynb` — analyzes a monthly airline passenger time series.
4. `mpg.ipynb` — selects the most appropriate chart type for different analytical questions.
5. `Penguins.ipynb` — studies distributions and relationships in penguin measurements.

## File structure

### Notebooks
- [datasaurus.ipynb](datasaurus.ipynb)  
  Demonstrates the Datasaurus dataset: despite very similar summary statistics, different datasets produce completely different shapes when plotted.

- [gapminder.ipynb](gapminder.ipynb)  
  Uses the Gapminder dataset to analyze trends in population, life expectancy, and GDP per capita over time across countries and continents.

- [flights.ipynb](flights.ipynb)  
  Visualizes monthly airline passenger totals from 1949 to 1960, focusing on time-series patterns and chart readability.

- [mpg.ipynb](mpg.ipynb)  
  Uses the MPG dataset to choose the right chart for different questions, such as comparing groups, relationships, or trends.

- [Penguins.ipynb](Penguins.ipynb)  
  Examines penguin species, islands, and physical measurements while handling missing values and exploring distributions and relationships.

### Data files
The CSV files used by the notebooks are stored in the `week 01 dataset` folder:

- [week 01 dataset/datasaurus.csv](week%2001%20dataset/datasaurus.csv)
- [week 01 dataset/flights.csv](week%2001%20dataset/flights.csv)
- [week 01 dataset/gapminder.csv](week%2001%20dataset/gapminder.csv)
- [week 01 dataset/mpg.csv](week%2001%20dataset/mpg.csv)
- [week 01 dataset/penguins.csv](week%2001%20dataset/penguins.csv)

## Tools and libraries

These notebooks are written in Python and use common data analysis libraries such as:

- pandas
- matplotlib
- seaborn
- numpy

## How to run

1. Open the folder in Jupyter Notebook, VS Code, or any Python notebook environment.
2. Make sure the required Python packages are installed.
3. Run the cells in each notebook in order.
4. Ensure the notebooks can access the CSV files in the `week 01 dataset` folder.

## Learning goals

By completing this assignment, you will practice:

- choosing appropriate chart types for different questions
- identifying missing data and handling it responsibly
- interpreting distributions, trends, and relationships
- understanding why a graph can reveal structure that summary statistics hide
- building clear and informative visualizations from real datasets

## Summary

This assignment demonstrates key principles of data visualization: not only how to draw charts, but also how to choose the right chart, interpret its meaning, and avoid misleading conclusions from raw numbers alone.
