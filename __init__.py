from .linkedin import scrape as scrape_linkedin
from .vagasremotas import scrape as scrape_vagasremotas
from .gupy import scrape as scrape_gupy
from .trampos import scrape as scrape_trampos
from .automation import scrape as scrape_automation
from .vagascom import scrape as scrape_vagascom
from .infojobs import scrape as scrape_infojobs
from .nerdin import scrape as scrape_nerdin
from .programathor import scrape as scrape_programathor
from .empregoscom import scrape as scrape_empregoscom
from .indeed import scrape as scrape_indeed
from .dribbble import scrape as scrape_dribbble
from .solides import scrape as scrape_solides

ALL_SCRAPERS = [
    scrape_linkedin,
    scrape_vagasremotas,
    scrape_gupy,
    scrape_trampos,
    scrape_automation,
    scrape_vagascom,
    scrape_infojobs,
    scrape_nerdin,
    scrape_programathor,
    scrape_empregoscom,
    scrape_indeed,
    scrape_dribbble,
    scrape_solides,
]
