from flask import Flask, render_template, request, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
from utils import preprocessing_pipeline, inference,RegForm, remove_nan
import pandas as pd
from flask_bootstrap import Bootstrap
from pathlib import Path
app = Flask(__name__)

app.config['UPLOAD_EXTENSIONS'] = ['.xlsx']

app.config.from_mapping(
    SECRET_KEY=b'\xd6\x04\xbdj\xfe\xed$c\x1e@\xad\x0f\x13,@G')

@app.errorhandler(500)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('500.html'), 500

Bootstrap(app)
@app.route('/', methods = ['GET', 'POST'])
def index():
    #upload del file
    form = RegForm(request.form)
    if request.method == 'POST':
        if request.form.get("submit_a"):
            file = request.files['csvfile']
            filename = secure_filename(file.filename)
    #check dell'estenzione
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    return "ONLY .xlsx FILE ARE PERMITTED!", 400
    #creazione cartella static se non esiste
            if not os.path.exists('static'):
                os.mkdir('static')

            filepath = os.path.join('static', file.filename)
            file.save(filepath)
    #Processo i dati
            THIS_FOLDER = os.path.dirname(os.path.abspath('static/'))
            par = str(Path(THIS_FOLDER))+'/static'
            file_excel = os.path.join(par, file.filename)

            observations = pd.read_excel(file_excel, engine = 'openpyxl')

        #rimuovo il file salvato
            os.remove('static/{}'.format(file.filename))

            preprocessed_obs, patient_id = preprocessing_pipeline(observations)
            posts = inference(preprocessed_obs, patient_id)

            return render_template('upload.html', tableA = posts.to_dict('records'))

        elif request.form.get("submit_b"):

            input_diz = {
                "ID": remove_nan(form.id_pat.data),
                "DATA VISITA": remove_nan(form.data.data),
                "SESSO": remove_nan(form.sesso.data),
                "ETA'": remove_nan(form.eta.data),
                "PESO (Kg)":remove_nan(form.peso.data),
                "ALTEZZA (cm)":remove_nan(form.altezza.data),
                "BMI": remove_nan(form.bmi.data),
                "RQ": remove_nan(form.rq.data),
                "REEp (Kcal/die)": remove_nan(form.reep.data),
                "REEm (Kcal/die)":remove_nan(form.reem.data),
                "REE (%predetto)": remove_nan(form.ree.data)}
            observations = pd.DataFrame.from_dict(input_diz, orient = 'index').T
            preprocessed_obs, patient_id = preprocessing_pipeline(observations)
            posts = inference(preprocessed_obs, patient_id)

            return render_template('upload2.html', tableA = posts.to_dict('records'))

    return render_template('index.html', form=form)

if __name__ == "__main__":
    app.run(debug = False)
    
if __name__ == "__main__":
    serve(app, listen='*:8080')




















