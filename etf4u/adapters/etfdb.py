import urllib.request, logging, json, time, sys
from lxml import html
from utils import HEADERS
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<d>{time:YYYY-MM-DD ddd HH:mm:ss}</d> | <lvl>{level}</lvl> | <lvl>{message}</lvl>",
)
log = logging.getLogger(f"etf4u.{__name__}")

# The etfdb adapter is a fallback adapter used when no specific adapter exists for a fund
# It navigates to the etf fund's page on etfdb.com then queries a public api endpoint
# which returns the list of holdings. The endpoint is limited to 15 results for user
# which are not registered to their premium membership plan

FUNDS = []


def fetch(fund):
    result = {}
    fund_csv_url = f"https://etfdb.com/etf/{fund.upper()}/"
    req = urllib.request.Request(fund_csv_url, headers=HEADERS)
    res = urllib.request.urlopen(req, timeout=60)
    tree = html.parse(res)
    table = tree.xpath("//table[@data-hash='etf-holdings']")[0]

    # the api returns 15 results, but we can iterate different sorting
    # criterias in the request to maximize the number of different holdings
    for query in [
        "&sort=weight&order=asc",
        "&sort=weight&order=desc",
        "&sort=symbol&order=asc",
        "&sort=symbol&order=desc",
    ]:
        log.debug(f"fetching query {query}")
        holdings_url = f"https://etfdb.com/{table.get('data-url')}{query}"
        logger.debug(f"fetching URL {holdings_url}")
        holdings_req = urllib.request.Request(holdings_url, headers=HEADERS)
        holdings_res = urllib.request.urlopen(holdings_req)
        holdings = json.loads(holdings_res.read().decode("utf-8"))
        for row in holdings["rows"]:
            symbol = html.fromstring(row["symbol"]).text_content()
            weight = float(row["weight"].strip("%"))
            if symbol != "N/A":
                result[symbol] = weight
        time.sleep(0.5)

    return result
