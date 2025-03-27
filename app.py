
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'motdepassepartage'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS mouvements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    montant REAL NOT NULL,
                    description TEXT,
                    categorie TEXT,
                    personne TEXT,
                    nature TEXT,
                    date TEXT NOT NULL
                )""")
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == 'monmotdepasse':
            session['logged_in'] = True
            return redirect('/dashboard')
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')
    
    if request.method == 'POST':
        type_m = request.form['type']
        montant = float(request.form['montant'])
        description = request.form['description']
        categorie = request.form['categorie']
        personne = request.form['personne']
        nature = request.form['nature']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO mouvements (type, montant, description, categorie, personne, nature, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (type_m, montant, description, categorie, personne, nature, date))
        conn.commit()
        conn.close()
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM mouvements ORDER BY date DESC")
    mouvements = c.fetchall()
    conn.close()

    solde = sum(m[2] if m[1] == 'revenu' else -m[2] for m in mouvements)

    return render_template('dashboard.html', mouvements=mouvements, solde=solde)


@app.route('/rapport', methods=['GET'])
def rapport():
    if not session.get('logged_in'):
        return redirect('/')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM mouvements")
    mouvements = c.fetchall()
    conn.close()

    mois_selectionnes = request.args.getlist('mois')
    mois_disponibles = sorted(set(m[7][:7] for m in mouvements))

    if mois_selectionnes:
        mouvements = [m for m in mouvements if m[7][:7] in mois_selectionnes]

    solde = sum(m[2] if m[1] == 'revenu' else -m[2] for m in mouvements)
    totaux_personne = {}
    totaux_categorie = {}

    for m in mouvements:
        personne = m[5]
        categorie = m[4]
        montant = m[2] if m[1] == 'revenu' else -m[2]
        totaux_personne[personne] = totaux_personne.get(personne, 0) + montant
        totaux_categorie[categorie] = totaux_categorie.get(categorie, 0) + montant

    labels = list(totaux_categorie.keys())
    data = [abs(v) for v in totaux_categorie.values()]

    return render_template('rapport.html', solde=solde,
                           totaux_personne=totaux_personne,
                           totaux_categorie=totaux_categorie,
                           labels=labels, data=data,
                           mois_disponibles=mois_disponibles,
                           mois_selectionnes=mois_selectionnes)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
