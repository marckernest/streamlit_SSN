import requests
from bs4 import BeautifulSoup

def get_ssa_office_link(zipcode):
    url = "https://secure.ssa.gov/ICON/ic001.action"
    data = {"zipCodeSearched": zipcode, "locate": "Locate"}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.post(url, data=data, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="icon-results-table")

    DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

    if table:
        info = []
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            label = th.get_text(strip=True)
            if label in DAYS:
                continue
            if "Hours" in label:
                hours_table = td.find("table", class_="icon-hoursOfOperation-table")
                if hours_table:
                    hours = []
                    for hrow in hours_table.find_all("tr"):
                        day = hrow.find("th").get_text(strip=True)
                        time = hrow.find("td").get_text(strip=True)
                        hours.append(f"{day}: {time}")
                    info.append(f"{label}\n" + "\n".join(hours))
                continue
            else:
                value = td.get_text(" ", strip=True)
                info.append(f"{label} {value}")
        formatted = f"Here is the nearest Social Security office for ZIP code {zipcode}:\n\n"
        formatted += "\n\n".join(info)
        return formatted.strip()

    error_notice = soup.find(id="invalidZipCodeNotice-Desktop") or soup.find(id="invalidZipCodeNotice-Mobile")
    if error_notice:
        return (
            f"Sorry, the SSA website could not match ZIP code {zipcode}. "
            "It may be new or not in their records. Please double-check the ZIP code, "
            "try a nearby ZIP, or call the SSA at 1-800-772-1213 for assistance."
        )

    return (
        f"No SSA office info could be found for ZIP code {zipcode}. "
        "Please try again later or visit the official SSA Office Locator: https://secure.ssa.gov/ICON/ic001.action"
    )