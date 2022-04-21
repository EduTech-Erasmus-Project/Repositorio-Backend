from django.test import TestCase

# Create your tests here.
# import logging
# from django.urls import reverse
# import pandas as pd
# from tensorflow.python.keras.models import load_model, model_from_json
# from keras import backend as ke
# from sumarization_app.Logica import modeloRNN
# import pickle

class modeloRNN():
    def cargarNN(nombreArchivo):
        print("Cargando modelo...")
        # modelo = load_model(nombreArchivo+'.h5')
        # print("Red Neuronal cargada desde archivo") 
        # return modelo
    def cargarModelo():
        modeloOptimizado=modeloRNN.cargarNN('ProyectoCreditoBanco\Recursos\modeloRedNeuronalOptimizada')
        print(modeloOptimizado)
        # #Se agrega la Red Neuronal al final del Pipeline
        # pipe.steps.append(['modelNN',modeloOptimizado])
        # cantidadPasos=len(pipe.steps)
        # print("Cantidad de pasos: ",cantidadPasos)
        # print(pipe.steps)
        # print('Red Neuronal integrada al Pipeline')
        # return pipe

model = modeloRNN
model.cargarModelo()
