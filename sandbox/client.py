import os
import sys
import socket


def sender(txt, s):
    msg = str.encode(str(txt))
    s.send(bytes(msg))


def listener(s):
    risposta = s.recv(1024)
    print(risposta.decode("utf-8"))


if __name__ == "__main__":
    modalita = sys.argv[1]
    indirizzo = sys.argv[2]
    port = 5678
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((str(indirizzo), port))
    if str(modalita) == "connect":
        sender(modalita, s)
        username = input("Immettere username ->")
        sender(username, s)
        password = input("Immettere password ->")
        sender(password, s)
        print("Connessione ultimata. Usa list, upload ,download e remove per interagire con il server.")
        while True:
            comando = input("Comando? ")
            sender(comando, s)
            if comando == "list":
                listener(s)
            elif comando == "upload":
                filename = input("Nome del file? ")
                sender(filename, s)
                file = open(filename, "r")
                s.send(bytes(file.__sizeof__()))
                contenuto = file.read()
                sender(contenuto, s)
                listener(s)
            elif comando == "download":
                filename = input("Nome del file? ")
                sender(filename, s)
                size = s.recv(1024)
                size = int.from_bytes(size, byteorder='big')
                oggetto = s.recv(1024)
                scaricato = open(filename, "w")
                scaricato.write(oggetto.decode("utf-8"))
                scaricato.close()
                print("Scaricato con successo.")
            elif comando == "remove":
                filename = input("Nome del file? ")
                if filename == "server.py" or "db.sqlite":
                    print("Abbiamo a che fare con un volpone, eh?")
                    s.close()
                    quit()
                sender(filename, s)
                print("Rimosso con successo")
            elif comando == "quit":
                s.close()
                break
    elif str(modalita) == "register":
        sender(modalita, s)
        username = input("Immettere username ->")
        sender(username, s)
        password = input("Immettere password ->")
        sender(password, s)