from selenium import webdriver
from selenium.webdriver.common.by import By

import requests
import argparse


from urllib.parse import urlparse, parse_qs

from typing import List, Optional
import time
import json

defaultDriver = webdriver.Chrome()

pageData = {}


class RowData:
    def __init__(
        cls,
        serial,
        date_filed,
        nypuc_doctype,
        name,
        url,
        organization,
        itemNo,
        file_name,
        docket_id,
    ):
        cls.serial = serial
        cls.date_filed = date_filed
        cls.nypuc_doctype = nypuc_doctype
        cls.name = name
        cls.url = url
        cls.organization = organization
        cls.itemNo = itemNo
        cls.docket_id = docket_id
        cls.file_name = file_name

    def __str__(cls):
        return f"\n(\n\tSerial: {cls.serial}\n\tDate Filed: {cls.date_filed}\
        \n\tNY PUC Doc Type: {cls.nypuc_doctype}\n\tName: {cls.name}\n\tURL: \
        {cls.url}\nOrganization: {cls.organization}\n\tItem No: {cls.itemNo}\n\
        \tFile Name: {cls.file_name}\n)\n"

    def __repr__(cls):
        return f"\n(\n\tSerial: {cls.serial}\n\tDate Filed: {cls.date_filed}\
        \n\tNY PUC Doc Type: {cls.nypuc_doctype}\n\tName: {cls.name}\n\tURL: \
        {cls.url}\nOrganization: {cls.organization}\n\tItem No: {cls.itemNo}\n\
        \tFile Name: {cls.file_name}\n)\n"


# class FilingObject(BaseModel):
#     case : str
#     filings: List[RowData]
def extractRows(driver, graph, case):
    table = driver.find_element(By.ID, "tblPubDoc")
    body = table.find_element(By.TAG_NAME, "tbody")
    rows = body.find_elements(By.TAG_NAME, "tr")
    filings = {"case": case, "filings": []}
    for row in rows:
        filing_item = None
        try:
            # print(row)
            cells = row.find_elements(By.TAG_NAME, "td")
            linkcell = cells[3]
            link = linkcell.find_element(By.TAG_NAME, "a")
            # print(f"link: {link}")
            name = link.text
            href = link.get_attribute("href")
            # print(f"href: {href}")
            # skip if the filing has already been indexed
            # if graph.pages[href].visited:
            #     continue

            filing_item = RowData(
                serial=cells[0].text,
                date_filed=cells[1].text,
                nypuc_doctype=cells[2].text,
                docket_id=case,
                name=name,
                url=href,
                organization=cells[4].text,
                itemNo=cells[5].text,
                file_name=cells[6].text,
            )
            filings["filings"].append(filing_item.__dict__)
        except Exception as e:
            print(
                "Encountered a fatal error while processing a row: ",
                row,
                "\nencountering error: ",
                e,
            )
    # print(f"Found filings:\n {filings}")
    save_process_filing_object(filings)
    return filings


def save_filing_object(filing_object, filename: Optional[str] = None):
    if filename is None:
        filename = f'filing-{filing_object["case"]}.json'
    with open(filename, "w") as f:
        json.dump(filing_object, f)


def verify_docket_id(docket_id: str):

    obj = {"docket_id": docket_id}
    api_url = "https://api.kessler.xyz/v2/public/conversations/verify"

    response = requests.post(api_url, json=obj)

    if response.status_code != 200:
        raise Exception(
            f"Failed to verify docket ID. Status code: {response.status_code}\nResponse:\n{response.text}"
        )

    return response.json()


def process_filing_object(filing_object):
    # assert (
    #     False
    # ), "Everything was successfull, not processing the file out of an abundance of caution"
    filings = filing_object["filings"]
    api_url = (
        "https://thaum.kessler.xyz/v1/process-scraped-doc/ny-puc/list?priority=false"
    )
    response = requests.post(api_url, json=filings)
    if response.status_code != 201:
        raise Exception(
            f"Failed to process filing object. Status code: {response.status_code}, Response: {response.text}"
        )


def save_process_filing_object(filing_object, filename: Optional[str] = None):
    save_filing_object(filing_object, filename)
    verify_docket_id(filing_object["case"])
    process_filing_object(filing_object)


def processURL(driver, url):
    time.sleep(6)
    # Find all <a> tags on the page
    links = driver.find_elements(By.TAG_NAME, "a")
    # Extract the href attribute from each link
    all_links = [link.get_attribute("href") for link in links]

    return all_links


# caseLoaded = "<div id=\"GridPlaceHolder_upUpdatePanelGrd\" \
# style=\"display: none;\"role=\"status\" aria-hidden=\"true\">"


def waitForLoad(driver):
    max_wait = 60
    print("waiting for page to load")
    for i in range(max_wait):
        overlay = driver.find_element(By.ID, "GridPlaceHolder_upUpdatePanelGrd")
        display = overlay.get_attribute("style")
        if display == "display: none;":
            print("Page Loaded")
            return True
        time.sleep(1)

    print("pageload took waaaay too long")
    return False


class Page:
    def __init__(cls, url, graph):
        cls.url = url
        cls.graph = graph
        cls.visited = False
        cls.links = []
        cls.assets = []

    def addLink(cls, link):
        if link not in cls.links:
            cls.links.append(link)

    def caseID(cls):
        # Parse the URL
        parsed_url = urlparse(cls.url)

        # Extract query parameters as a dictionary
        query_params = parse_qs(parsed_url.query)

        # Get the value of a specific key (e.g., 'key')
        key_value = query_params.get("MatterCaseNo", [None])[0]
        if key_value is None:
            return None
        return key_value

    def Process(cls):
        if cls.visited:
            return
        # Get all the links on the page

        defaultDriver.get(cls.url)
        waitForLoad(defaultDriver)
        # all_links = processURL(defaultDriver, cls.url)
        # for link in all_links:
        #     cls.addLink(link)
        #     cls.graph.addLink(link)

        caseId = cls.caseID()
        # print(f"Have CaseID: {caseId}")
        if caseId is not None:
            try:
                rowData = extractRows(defaultDriver, cls.graph, case=caseId)
                cls.graph.addCase(caseId, rowData)
            except Exception as e:
                # Save errored case ID to list
                try:
                    with open("errored_cases.json", "r") as f:
                        errored_cases = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    errored_cases = []

                if caseId not in errored_cases:
                    errored_cases.append(caseId)

                with open("errored_cases.json", "w") as f:
                    json.dump(errored_cases, f)

                # Save detailed error info
                try:
                    with open("error_details.json", "r") as f:
                        error_details = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    error_details = []

                error_details.append(
                    {"case_id": caseId, "error": str(e), "error_type": type(e).__name__}
                )

                with open("error_details.json", "w") as f:
                    json.dump(error_details, f)
                # Print the error to

        cls.visited = True

    def __str__(cls):
        return f"==========\nPage: {cls.url}\nVisited: {cls.visited}\nLinks: {cls.links}\nAssets: {cls.assets}"


def checkIfCasePage(url):
    if "CaseMaster.aspx" in url:
        return True
    return False


def checkIfDocumentPage(url):
    if "ViewDoc.aspx" in url:
        return True
    return False


class SiteGraph:
    def __init__(cls, driver=defaultDriver):
        cls.driver = driver
        cls.pages = {}
        cls.caseData: dict = {}

    def Crawl(cls):
        for url in list(cls.pages):
            page = cls.pages[url]
            if page.visited:
                continue
            page.Process()

    def addLink(cls, link):
        # Check if the link is already in the list
        print(f"Adding link: {link}")
        newPage = Page(link, cls)
        if link not in cls.pages:
            cls.pages[link] = newPage

    def processLink(cls, link):
        # if the page is none add the the link to the dict then process it
        if cls.pages[link] is None:

            return

    def addCase(cls, case, data):
        cls.caseData[case] = data

    def LoadSiteState(cls):
        pass

    def SaveSiteState(cls, filename="links.json"):
        with open(filename, "w") as f:
            json.dump(cls.caseData, f)

    def Seed(cls, urls: List[str]):
        for url in urls:
            cls.addLink(url)

    def dumpLinks(cls):
        for page in cls.pages:
            print(cls.pages[page])


def get_all_cases_from_json(filename: str, after_number: int = 0) -> List[str]:
    with open(filename, "r") as f:
        json_data = json.load(f)
        return json_data[after_number:]


if __name__ == "__main__":
    # test : "22-M-0149"
    parser = argparse.ArgumentParser(
        description="selenium based \
                                     NYPUC case parser"
    )
    # Add flags/arguments
    parser.add_argument("-o", "--output", type=str, help="json file to save the data")
    parser.add_argument("-i", "--input", type=str, help="Specify the input cases")
    parser.add_argument("-c", "--cases", type=str, help="comma separated list of cases")

    # Parse the arguments
    args = parser.parse_args()

    # Use the flags in your script

    graph = SiteGraph()
    # cases = ["22-M-0645"]
    cases = get_all_cases_from_json("output_cases.json", 0)

    # Already processed 24-E-0165 22-M-0645 18-E-0138
    # To process:
    # if args.cases:
    #     caseCodes = args.cases.split(',')
    #     for cc in caseCodes:
    #         cases.append(
    #             f"https://documents.dps.ny.gov/public/MatterManagement/CaseMaster.aspx?MatterCaseNo={cc}")
    #     graph.Seed(cases)

    for case in cases:
        graph.addLink(
            f"https://documents.dps.ny.gov/public/MatterManagement/CaseMaster.aspx?MatterCaseNo={case}"
        )

    graph.Crawl()

    if args.output:
        graph.SaveSiteState(args.output)
