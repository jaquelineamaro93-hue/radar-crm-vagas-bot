from .linkedin import scrape as scrape_linkedin
from .gupy import scrape as scrape_gupy
from .infojobs import scrape as scrape_infojobs
from .catho import scrape as scrape_catho
from .vagascom import scrape as scrape_vagascom
from .jobs99 import scrape as scrape_jobs99
from .solides import scrape as scrape_solides

ALL_SCRAPERS = [
    scrape_linkedin,
    scrape_gupy,
    scrape_infojobs,
    scrape_catho,
    scrape_vagascom,
    scrape_jobs99,
    scrape_solides,
]
