"""
Modo contínuo com schedule — roda o scraper periodicamente.
Use: python scheduler.py
Vai executar de 6 em 6 horas por padrão.
"""
import schedule
import time
from main import run

INTERVAL_HOURS = 6

if __name__ == "__main__":
    print(f"Scheduler iniciado — coleta a cada {INTERVAL_HOURS}h")
    run()  # Executa imediatamente ao iniciar
    schedule.every(INTERVAL_HOURS).hours.do(run)

    while True:
        schedule.run_pending()
        time.sleep(60)
