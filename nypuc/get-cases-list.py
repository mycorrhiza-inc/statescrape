import re
from bs4 import BeautifulSoup
from typing import List, Dict


def extract_docket_ids_regex(html_content: str) -> List[str]:
    """
    Extract docket IDs from HTML content using regex

    Args:
        html_content (str): HTML string containing the table

    Returns:
        List[str]: List of docket IDs
    """
    # Pattern matches: two digits, hyphen, capital letter, hyphen, four digits
    docket_pattern = r"\d{2}-[A-Z]-\d{4}"
    return re.findall(docket_pattern, html_content)


def process_docket_file(input_path: str, output_path: str) -> None:
    """
    Process HTML file to extract docket IDs and save to JSON

    Args:
        input_path (str): Path to input HTML file
        output_path (str): Path to output JSON file
    """
    import json

    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    docket_ids = extract_docket_ids_regex(html_content)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docket_ids, f, indent=2)


def extract_docket_details(html_content: str) -> List[Dict[str, str]]:
    """
    Extract docket IDs and their associated information using BeautifulSoup

    Args:
        html_content (str): HTML string containing the table

    Returns:
        List[Dict[str, str]]: List of dictionaries containing docket details
    """
    soup = BeautifulSoup(html_content, "html.parser")
    # docket_links = soup.find_all('a', href=lambda x: x and 'MatterSeq' in x)
    docket_links = soup.find_all("a")

    docket_details = []
    for link in docket_links:
        docket_id = link.text.strip()
        if re.match(r"\d{2}-[A-Z]-\d{4}", docket_id):
            # Get the parent tr element
            row = link.find_parent("tr")
            if row:
                # Extract additional information from the row
                details = {
                    "docket_id": docket_id,
                    "href": link["href"],
                    "type": row.find_all("td")[1].text.strip(),
                    "date": row.find("td", class_="sorting_1").text.strip(),
                    "description": row.find_all("td")[4].text.strip(),
                }
                docket_details.append(details)

    return docket_details


# Example usage:
if __name__ == "__main__":
    process_docket_file("all_cases.html", "output_cases.json")
