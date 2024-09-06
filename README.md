# Data Collection and Analysis of Steward Owned Businesses (Mindsets, Organizational Culture)

This project aids in researching mindsets that are related to steward ownership, as well as its organizational culture.
It does so by collecting data from the websites of steward owned companies and analyzing the data with respect to 5
steward ownership related mindsets using AI (GPT 4o mini).

## Installation

Clone the repository and install the required packages using the following command:

```bash
pip install -r requirements.txt
```

Make sure to have Python installed on your system.
You can download it from [here](https://www.python.org/downloads/).

## Data

Create a file named `companies2links.csv` in the root directory of the project. The file should contain a list of
steward owned companies with the following structure:

```csv
company;URL
```

where `company` is the name of the company and `URL` is the URL of the company's website.

## Environment Variables

Add the following environment variables to your system by creating a file named `.env` in the root directory of the
project
and adding the following line to it:

```bash
GPT_API_KEY=YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your OpenAI API key. You can get an API key by signing up on
the [OpenAI website](https://platform.openai.com/).

## Usage

To collect data from the websites run the following command:

```bash
python crawler.py
```

Then once the data is collected, run the following command to analyze the data:

```bash
python crawler-data-analysis.py
```

The results will be saved in the files `company_mindsets.csv` and `company_org_cultures.csv`.