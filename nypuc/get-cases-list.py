import re
from bs4 import BeautifulSoup
from typing import List, Dict

from pydantic import BaseModel

import json


# <tbody>
#   <tr role="row" class="odd">
#     <td>
#       <a
#         href="../MatterManagement/CaseMaster.aspx?MatterSeq=74940&amp;MNO=24-C-0663"
#         target="_blank"
#         >24-C-0663</a
#       >
#     </td>
#     <td>Complaint</td>
#     <td>Appeal of an Informal Hearing Decision</td>
#     <td class="sorting_1">11/22/2024</td>
#     <td>
#       In the Matter of the Rules and Regulations of the Public Service
#       Commission, Contained in 16 NYCRR in Relation to Complaint Procedures -
#       Appeal by Patricia Walsh of the Informal Decision Rendered in Favor of
#       Verizon Communications Inc. (Verzion), (310628).
#     </td>
#     <td>Individual</td>
#   </tr>
#   <tr role="row" class="even">
#     <td>
#       <a
#         href="../MatterManagement/CaseMaster.aspx?MatterSeq=74937&amp;MNO=24-M-0664"
#         target="_blank"
#         >24-M-0664</a
#       >
#     </td>
#     <td>Analysis</td>
#     <td>State</td>
#     <td class="sorting_1">11/21/2024</td>
#     <td>
#       In the Matter of the Commission's Assessment of Utility Cybersecurity
#       Programs, Protections, and Compliance with State Standards Pursuant to PSL
#       Section 66(30).
#     </td>
#     <td>New York State Department of Public Service</td>
#   </tr>
#
class DocketInfo(BaseModel):
    docket_id: str  # 24-C-0663
    matter_type: str  # Complaint
    matter_subtype: str  # Appeal of an Informal Hearing Decision
    title: str  # In the Matter of the Rules and Regulations of the Public Service
    organization: str  # Individual


def extract_docket_info(html_content: str) -> List[DocketInfo]:
    """
    Extract complete docket information from HTML table rows

    Args:
        html_content (str): HTML string containing the table

    Returns:
        List[DocketInfo]: List of DocketInfo objects containing details for each docket
    """
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.find_all("tr", role="row")

    docket_infos: List[DocketInfo] = []

    for row in rows:
        # Get all cells in the row
        cells = row.find_all("td")
        if len(cells) >= 6:  # Ensure we have all required cells
            try:
                docket_info = DocketInfo(
                    docket_id=cells[0].find("a").text.strip(),
                    matter_type=cells[1].text.strip(),
                    matter_subtype=cells[2].text.strip(),
                    title=cells[4].text.strip(),
                    organization=cells[5].text.strip(),
                )
                docket_infos.append(docket_info)
            except (AttributeError, IndexError) as e:
                # Skip malformed rows
                print(f"Error processing row: {e}")
                continue

    return docket_infos


def process_docket_file(input_path: str, output_path: str) -> None:
    """
        Process HTML file to extract complete docket information and save to JSON
    >>>>>>> Snippet

        Args:
            input_path (str): Path to input HTML file
            output_path (str): Path to output JSON file
    """

    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    docket_infos = extract_docket_info(html_content)

    # Convert to list of dictionaries for JSON serialization
    docket_dicts = [docket.model_dump() for docket in docket_infos]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docket_dicts, f, indent=2)


# def extract_docket_details(html_content: str) -> List[Dict[str, str]]:
#     """
#     Extract docket IDs and their associated information using BeautifulSoup
#
#     Args:
#         html_content (str): HTML string containing the table
#
#     Returns:
#         List[Dict[str, str]]: List of dictionaries containing docket details
#     """
#     soup = BeautifulSoup(html_content, "html.parser")
#     # docket_links = soup.find_all('a', href=lambda x: x and 'MatterSeq' in x)
#     docket_links = soup.find_all("a")
#
#     docket_details = []
#     for link in docket_links:
#         docket_id = link.text.strip()
#         if re.match(r"\d{2}-[A-Z]-\d{4}", docket_id):
#             # Get the parent tr element
#             row = link.find_parent("tr")
#             if row:
#                 # Extract additional information from the row
#                 details = {
#                     "docket_id": docket_id,
#                     "href": link["href"],
#                     "type": row.find_all("td")[1].text.strip(),
#                     "date": row.find("td", class_="sorting_1").text.strip(),
#                     "description": row.find_all("td")[4].text.strip(),
#                 }
#                 docket_details.append(details)
#
#     return docket_details


# Example usage:
if __name__ == "__main__":
    process_docket_file("all_cases.html", "output_cases.json")
