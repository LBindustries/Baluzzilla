import os
import socket
import threading

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "non dovrei essere pubblica"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Utente(db.Model):
    __tablename__ = "utente"
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    passwd = db.Column(db.String, nullable=False)
    file = db.relationship("File", back_populates="proprietario")

    def __init__(self, username, password):
        self.username = username
        self.passwd = password


class File(db.Model):
    __tablename__ = "file"
    fid = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    dimensioni = db.Column(db.BigInteger, nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("utente.uid"))
    proprietario = db.relationship("Utente", back_populates="file")


def sender(txt, s):
    msg = str.encode(str(txt))
    s.send(bytes(msg))


def lista(utente, clientSock):
    files = File.query.join(Utente).filter_by(uid=utente.uid)
    msg = ""
    for file in files:
        msg += file.filename + "\n"
    if msg == "":
        msg = "Nessun file trovato sulla cartella remota."
    messaggio_b = str.encode(msg)
    clientSock.send(bytes(messaggio_b))


def carica(utente, clientSock):
    filename = clientSock.recv(1024)
    filename = filename.decode("utf-8")
    size = clientSock.recv(1024)
    size = int.from_bytes(size, byteorder='big')
    nuovofile = File(filename=filename, dimensioni=size, uid=utente.uid)
    files = File.query.all()
    if nuovofile not in files:
        db.session.add(nuovofile)
        db.session.commit()
        documento = clientSock.recv(1024+size)
        documento = documento.decode("utf-8")
        oggetto = open(filename, "w")
        oggetto.write(documento)
        oggetto.close()
        msg = "Oggetto salvato sulla cartella remota."
    else:
        msg = "Errore durante il salvataggio: il file esiste già sul server."
    messaggio_b = str.encode(msg)
    clientSock.send(bytes(messaggio_b))


def scarica(utente, clientSock):
    filename = clientSock.recv(1024)
    print(filename)
    filename = filename.decode("utf-8")
    scarica = File.query.filter_by(filename=filename).join(Utente).filter_by(uid=utente.uid).first()
    print(scarica)
    if scarica:
        oggetto = open(filename, "r")
        contenuto = oggetto.read()
        peso = oggetto.__sizeof__()
        clientSock.send(bytes(peso))
        contenuto = contenuto.encode()
        clientSock.send(bytes(contenuto))
    else:
        msg = "Errore durante il salvataggio: il file non esiste sul server."
        messaggio_b = str.encode(msg)
        clientSock.send(bytes(messaggio_b))


def serverhandler(clientSock):
    mode = clientSock.recv(1024)
    mode = mode.decode("utf-8")
    if mode == "register":
        username = clientSock.recv(1024)
        username = username.decode("utf-8")
        password = clientSock.recv(1024)
        password = password.decode("utf-8")
        nuovouser = Utente(username, password)
        db.session.add(nuovouser)
        db.session.commit()
    else:
        username = clientSock.recv(1024)
        username = username.decode("utf-8")
        password = clientSock.recv(1024)
        password = password.decode("utf-8")
        found = False
        utente = Utente.query.filter_by(username=username).first()
        if utente and utente.passwd == password:
            found = True
        else:
            clientSock.close()
        while found:
            command = clientSock.recv(1024)
            command = command.decode("utf-8")
            if command == "list":
                lista(utente, clientSock)
            elif command == "upload":
                carica(utente, clientSock)
            elif command == "download":
                scarica(utente, clientSock)
            elif command == "quit":
                print("Baluzzilla client disconnecting...")
                clientSock.close()
                break


if __name__ == "__main__":
    if not os.path.isfile("db.sqlite"):
        db.create_all()
    host = ''
    port = 5678
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    print("Baluzzilla server started.")
    while True:
        conn, addr = s.accept()
        print("Baluzzilla client connected")
        t = threading.Thread(target=serverhandler, args=(conn,))
        t.daemon = True
        t.start()
