import time

import mariadb


class Connection:
    """Gestore della connessione al database MariaDB."""


    connection: mariadb.Connection = None

    @classmethod
    def start_connection(cls) -> None:
        """Inizializza la connessione al database, utilizzando la sleep per aspettare che il database sia pronto a ricevere connessioni."""

        # Usiamo un for invece di un while per evitare spiacevoli casi in cui il database non riesca ad avviarsi
        for attempt in range(30):                                      
            try:
                cls.connection: mariadb.Connection = mariadb.connect(
                    host = "mariadb-culturaLLM",
                    port = 3306,
                    user = "user",
                    password = "pwd",
                    database = "culturaLLM"
                )
                print("Connessione al database stabilita!!")
                return
            except mariadb.OperationalError as e:
                time.sleep(2)
        raise ConnectionError("Impossibile connettersi al db dopo 30 tentativi")

    @classmethod
    def get_connection(cls) -> mariadb.Connection:
        """Ritorna la connessione attiva al database."""


        if cls.connection is None:
            raise ConnectionError("Connessione non inizializzata")
        return cls.connection
    
    