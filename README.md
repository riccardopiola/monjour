# Monjour

**Monjour** (Money + Journal) is a tool designed to simplify financial tracking by consolidating your transaction data from multiple sources into a single, unified database. With Monjour, you can generate monthly and yearly financial reports, complete with visualizations such as graphs and diagrams, to help you better understand and manage your spending habits.

### Getting started

It is recommended to create a virtual environment with

```sh
python -m venv .venv
```

Install Monjour directly from github, a PyPy package might be provided in the future. The `st` optional feature is required to run the demo and access streamlit related functionality.

```sh
pip install git+https://github.com/riccardopiola/monjour.git[st]
```

Run the demo

```sh
python -m monjour --demo
```

