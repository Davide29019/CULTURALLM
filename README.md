# CULTURALLM

## IDEAS

#### GIORNO 0: domanda aperta da un utente x, un LLM risponde istantaneamente, ed eventuali profili rispondono anche essi e fanno il ranking
#### GIORNO 1: profili rispondono e fanno il ranking
#### ... 
#### GIORNO 7: domanda viene chiusa, vengono i points per ogni risposta (valori acquisiti da ogni ranking effettuato) e normalizzati rispetto ranking_times e vengono distributiti i punti normalizzati
#### GIORNO 8: un utente y risponde (anche se domanda in stato close) e (prende punti di partecipazione) prende una percentuale dei punti della c lassifica se la risposta era gia presente in classifica

###### condizione di poter fare il ranking: almeno 5 risposte ricevute per quella domanda, nel totale tra quelle utente e LLM. Messaggio all'utente quando un ranking è disponibile. 

###### condizione di chiusura domanda: dopo 7 giorni se ha ricevuto almeno 10 ranking_times altrimenti in attesa della ricezione di essi

###### dopo la chiusura della domanda fare una classifica per far vedere chi ha rispopsto meglio a quella domanda senza far vedere la risposta
