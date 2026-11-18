import os
from persistence.database import SQLiteRepository
from domain.services import GestaoContratosService
from presentation.gui import App

def main():
    repo = SQLiteRepository("why_database.db")
    repo.seed_initial_data()
    service = GestaoContratosService(repo)
    app = App(service)
    app.mainloop()

if __name__ == "__main__":
    main()
