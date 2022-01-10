# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 15:22:15 2021

@author: Lorenzo Famiglini
"""
import pandas as pd
import os
import json
import re
import pickle
import numpy as np
from wtforms import SubmitField, BooleanField, StringField, PasswordField, validators, IntegerField, FloatField
from flask_wtf import Form


def preprocessing_pipeline(observations):
    """
    Prende in input il file xlsx dei pazienti e preprocessa le features di interesse
    """
    features = ['SESSO',"ETA'",'PESO (Kg)','ALTEZZA (cm)','BMI','RQ','REEp (Kcal/die)',
           'REEm (Kcal/die)','REE (%predetto)']
    patient_id = observations[['ID','DATA VISITA','SESSO', 'PESO (Kg)', 'ALTEZZA (cm)', 'BMI']]


    #observations['SESSO'] = pd.get_dummies(observations.SESSO, drop_first=True)
    observations['SESSO'] = observations.SESSO.apply(mapping_gender)
    #y = observations['AGE READER SCORE ']
    x = observations.loc[:, features]
    THIS_FOLDER = os.path.dirname(os.path.abspath('static/'))+'/mysite'
    file = os.path.join(THIS_FOLDER, 'ml_imputer_train.pickle')
    with open(file, 'rb') as f:
        imputer = pickle.load(f)
    x_imputer = imputer_inference(x.reset_index(drop = True), imputer)

    return x_imputer,patient_id

def mapping_gender(x):
    if x.lower() == 'M':
        gender = 0
    elif x.lower() == 'F':
        gender = 1
    else:
        gender = np.nan
    return gender

def remove_nan(x):
    if x == None:
        obj = np.nan
    else:
        obj = x
    return obj



def imputer_inference(df, imp_mean):
    '''
    Imputatore di valori mancanti
    '''
    imputer_res = imp_mean.transform(df)
    df_imput = pd.DataFrame(imputer_res, columns=df.columns)
    return df_imput

def slope_intercept(x1 = 0, y1=0.7,x2 =50,y2 = 2):
    m = (y2 - y1) / (x2 - x1)
    q = y1 - m * x1
    return m,q

def estimate_biological_age(prediction):
    #m,q = slope_intercept()
    m = 0.024
    q = 0.83
    bio_age = (q - prediction)/(-m) #eta' biologica stimata
    return bio_age


def inference(observations,patient_id):
    THIS_FOLDER = os.path.dirname(os.path.abspath('static/'))+'/mysite'
    filename = os.path.join(THIS_FOLDER, 'finalized_model.sav')
    loaded_model = pickle.load(open(filename, 'rb'))
    predictions = loaded_model.predict(observations)
    estimated_age = np.array([int(estimate_biological_age(x)) for x in predictions])
#   estimated_age_lower = np.array([int(estimate_biological_age(x-0.492)) for x in predictions]) #90% DI CONFIDENZA
#   estimated_age_upper = np.array([int(estimate_biological_age(x+0.492)) for x in predictions]) #90% DI CONFIDENZA
    delta =   estimated_age - np.array(observations["ETA'"])
    estimation = {"ID":patient_id.ID, "DATA_VISITA": patient_id['DATA VISITA'],
                  "Sesso":patient_id.SESSO,"Age": observations["ETA'"].round(0),'Peso': patient_id['PESO (Kg)'],
                  'Altezza':patient_id['ALTEZZA (cm)'], 'Age_Reader_Score': predictions.round(3),
                  'Biological_Age':estimated_age,'Delta':delta.round(3)}
    path_static = os.path.dirname(os.path.abspath('static/'))+'/mysite'
    path_static = path_static+'/result.json'
    with open(path_static, 'w') as fp:
        json.dump(pd.DataFrame.from_dict(estimation,orient = 'columns').to_json(), fp)
    return pd.DataFrame.from_dict(estimation,orient = 'columns')

#'Lower_Biological_Age': estimated_age_lower,'Upper_Biological_Age': estimated_age_upper,


class MyFloatField(FloatField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = float(re.sub(',','.', str(valuelist[0])))
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid float value'))

class RegForm(Form):
  id_pat = MyFloatField('ID')
  data = StringField('DATA VISITA')
  sesso = StringField('SESSO (M o F)')
  eta = MyFloatField("ETA'")
  peso = MyFloatField('PESO (Kg)')
  altezza = MyFloatField('ALTEZZA (cm)')
  bmi = MyFloatField('BMI')
  rq = MyFloatField('RQ')
  reep = MyFloatField('Reep (Kcal/die)')
  reem = MyFloatField('REEm (Kcal/die)')
  ree = MyFloatField('REE (%predetto)')
  submit = SubmitField('Submit')
