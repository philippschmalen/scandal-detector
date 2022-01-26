# Scandal detector

Detect scandals for any entity, such as public firms or celebrities.
The algorithm only requires sufficient search interest for a keyword and its associated scandals.

## Project brief

![](img/data-flow.png)

---
## Objective

Detect scandals for publicly known firms within the last 5 years.

## Key results

1. Show overall number of scandals
2. Display scandals in timeline
3. Provide links to Google for further investigation

## Data

The project builds on [Google Trends](https://trends.google.com/trends/?geo=GLOBAL) data. It covers search interest for a keyword over the last five years.

The data pipeline includes the following steps:

1. a user inputs a keyword to which we add "scandal"
2. the search interest is fetched from Google Trends with [pytrends](https://github.com/GeneralMills/pytrends).
3. Process the data with pandas
4. train a time-series model with [Facebook Prophet](https://facebook.github.io/prophet/).
5. Identify outliers from the predicted search interest. These are the scandals.
5. Visualize timeline with plotly
6. List links to Google in the period of the scandal



---

## Extensions

- [ ] check that detected scandals do not overlap within a period of `date_uppderbound_days`
- [ ] install pre-commit
- [ ] create `config.yaml`
- [ ] load config with `hydra`


## Color codings

Using color codings from http://towardssustainablefinance.com/.

color_discrete_sequence=["#4d886d", "#f3dab9", "#9bcab8", "#829fa5", "#cfaea5"]
dark font color: #545454
bright background color: #D5E6E0