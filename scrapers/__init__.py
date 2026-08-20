from .linkedin import scrape as scrape_linkedin
from .vagasremotas import scrape as scrape_vagasremotas
from .gupy import scrape as scrape_gupy
from .trampos import scrape as scrape_trampos
from .vagascom import scrape as scrape_vagascom
from .infojobs import scrape as scrape_infojobs
from .nerdin import scrape as scrape_nerdin
from .empregoscom import scrape as scrape_empregoscom
from .dribbble import scrape as scrape_dribbble
from .solides import scrape as scrape_solides
from .jobs99 import scrape as scrape_jobs99
from .catho import scrape as scrape_catho

ALL_SCRAPERS = [
    scrape_linkedin,
    scrape_vagasremotas,
    scrape_gupy,
    scrape_trampos,
    scrape_vagascom,
    scrape_infojobs,
    scrape_nerdin,
    scrape_empregoscom,
    scrape_dribbble,
    scrape_solides,
    scrape_jobs99,
    scrape_catho,
]
