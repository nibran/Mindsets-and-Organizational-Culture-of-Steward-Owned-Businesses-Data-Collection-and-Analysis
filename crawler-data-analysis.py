import csv
import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from schema import Schema

# loading variables from .env file
load_dotenv()
# Increase the field size limit to avoid field size limit error (due to the web data being very big)
csv.field_size_limit(1000000000)

# Initialize the OpenAI client
GPT_API_KEY = os.getenv('GPT_API_KEY')
client = OpenAI(api_key=GPT_API_KEY)

# Output file names
filename_mindsets = 'company_mindsets.csv'
filename_org_cultures = 'company_org_cultures.csv'


# Read company web data from the file
def read_company_data(file_path):
    with open(file_path, 'r', encoding='utf-8', newline='') as company_data:
        # Additionally we replace the null characters with an empty string
        reader = csv.reader((line.replace('\0', '') for line in company_data), delimiter=';')
        return [row for row in reader]


# Write the extracted mindsets to a file
def write_mindsets_to_file(company_name, mindset_list):
    mindset_file_exists = os.path.isfile(filename_mindsets)
    # Writing the mindsets to file
    with open(filename_mindsets, mode='a', newline='', encoding='utf8', errors='ignore') as mindset_file:
        writer = csv.writer(mindset_file, delimiter=';')
        # If the file does not exist, write the header
        if not mindset_file_exists:
            writer.writerow(['company', 'mindset', 'core_attribute', 'quote'])
        # Write the mindsets
        for mindset in mindset_list:
            if isinstance(mindset, dict) and all(
                    key in mindset for key in ['mindset', 'core_attribute', 'quote']):
                writer.writerow(
                    [company_name, mindset['mindset'], mindset['core_attribute'], mindset['quote']])
            else:
                print(f"Skipping invalid mindset format: {mindset}")


# Write the extracted organizational cultures to a file
def write_org_cultures_to_file(company_name, org_culture_list):
    org_culture_file_exists = os.path.isfile(filename_org_cultures)
    # Writing the organizational cultures to file
    with open(filename_org_cultures, mode='a', newline='', encoding='utf8', errors='ignore') as org_file:
        writer = csv.writer(org_file, delimiter=';')
        # If the file does not exist, write the header
        if not org_culture_file_exists:
            writer.writerow(['company', 'organizational_culture'])
        # Write the organizational cultures
        writer.writerow([company_name, ','.join(org_culture_list)])


# Load the mindset and core attributes from a JSON file which provides them in the required format
with open('mindsets.json', 'r') as file:
    mindsets = json.load(file)

# Save organizational cultures identified for consistent naming throughout the analysis.
prev_org_cultures = []

# Context for the GPT-4o model (Always the same for each company)
context = f'''
    Analyze company web data to extract mindsets and organizational cultures that align with the defined mindsets: {mindsets}. Only include insights that directly refer to these mindsets—avoid introducing unrelated concepts.

    Instructions:
    1. Direct Quotes: Include only direct quotes from the web data—no paraphrasing. The content must explicitly reference one of the provided mindsets.
    2. Naming: Use the exact mindsets provided. Introduce new terms only if absolutely necessary and if they add significant value.
    3. Relevance: Focus solely on mindsets relevant to steward ownership. Exclude unrelated data like legal disclaimers or cookie policies.
    4. Organizational Culture: Always return an array of concise organizational culture keywords identified within the text, ensuring naming consistency with previously found organizational culture keywords, you can add new ones to this list if you find any: {prev_org_cultures}.
    5. Consistency: Ensure findings match the provided mindsets and organizational cultures, maintaining consistency across results.
    6. In case you don't find any mindset or organizational culture, please return "No mindset found" or "No organizational culture found" respectively inside the array.
    '''


# Analyze company web data to extract mindsets and organizational cultures that align with the defined mindsets.
def analyze_company(company):
    # Prompt for the GPT-4o model
    prompt = f'''
        Analyze the company web data to extract mindsets and organizational cultures:
        Company: {company[0]}
        Web Data: {company[1][:110000]}
        '''

    # Initialize completion and error variables, used for error handling and retrying the API call
    completion = None
    error = ''

    # Retry the API call if an error occurs (maximum 2 retries)
    for x in range(0, 2):
        try:
            # If completion is None, it means it's the first time the API is called for this company
            if completion is None:
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=Schema
                )
            else:
                # If an error happened, ask GPT again. It tells it what error happened, so it can correct itself.
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": completion.choices[0].message.content},
                        {"role": "user", "content": f"I got this error, please make sure to give me the right "
                                                    f"json type: {error}"}
                    ],
                    response_format=Schema
                )

            # Handle response as json object
            message = completion.choices[0].message.content
            mindset_list = json.loads(message)['mindsets']
            org_culture = json.loads(message)['organizational_culture']

            # print the mindset names
            print(f'Mindsets found for {company[0]}: {[mindset["mindset"] for mindset in mindset_list]}')
            print(f'Organizational Culture for {company[0]}: {org_culture}')

            # Extract organizational cultures for consistent naming
            prev_org_cultures.extend(org_culture)

            # write results to files
            write_mindsets_to_file(company[0], mindset_list)
            write_org_cultures_to_file(company[0], org_culture)
            break

        except Exception as e:
            error = str(e)
            print(f'Error: {e}')
            continue


def main():
    # Read crawler data
    company_data = read_company_data('Company2Fulltext.csv')

    # Analyze each company (without header)
    for ind, company in enumerate(company_data[1:]):
        print(f'{ind + 1}. Analyzing company: {company[0]}')
        analyze_company(company)
        # Sleep for 10 seconds to avoid rate limiting
        time.sleep(10)


main()
