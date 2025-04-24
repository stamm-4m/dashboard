import os
from pathlib import Path
from tensorflow.keras.models import load_model
import numpy as np  
import joblib  
#import rpy2.robjects as robjects
#from rpy2.robjects import pandas2ri
import requests
import json



class ModelPredictor:
    def __init__(self):
        self.model_file_path = ""
        self.model_data = {}
        self.url_rf = "http://127.0.0.1:8000/rf/0002_penicillin_RF"
        self.url_cubist = "http://127.0.0.1:8000/cubist/0003_penicillin_CUBIST"
       
    def load_model_ini(self, model_data):
        if(model_data != {} or model_data != 'None'):
            print("model_data",model_data)
            self.model_data = model_data
            # inicio el file path 
            self.model_file_path = self.model_data["model_file"]

            """
            Inicializa el ModelPredictor cargando el modelo .keras desde la ruta especificada. 
            :parametro model_path: Ruta al archivo de modelo .keras
            """
            if self.is_keras_model():
                print(f"{self.model_file_path} es un archivo compatible con Keras.")
                self.model = load_model("../ML_Repository/"+ self.model_data["model_file"])
            elif self.is_pickle_model():
                print(f"{self.model_file_path} es un archivo .pkl.")
                self.model = joblib.load(os.path.join("../ML_Repository/"+ self.model_data["model_file"]))
            elif self.is_rds_model():
                print(f"{self.model_file_path} es un archivo RDS.")
                # REalizar la carga y ejecucion de la api rest R
                # para el modelo seleccionado
                # Verificar ambos endpoints
                self.check_endpoint(self.url_rf)
                self.check_endpoint(self.url_cubist)
            else:
                print("Formato de archivo no compatible.")
                return "unsupported"
            
            print("Modelo cargado desde ../ML_Repository/"+ self.model_data['model_file'])

    def predict(self, input_data):
        """
        Realiza predicciones en los datos de entrada proporcionados.
        
        :param input_data: numpy array con los datos de entrada
        :return: numpy array con las predicciones del modelo
        """
        # Asegurarse de que los datos de entrada sean un array de numpy
        if not isinstance(input_data, np.ndarray):
            raise ValueError("Los datos de entrada deben ser un numpy array.")
        
        # Realizar predicciones utilizando el modelo cargado
        predictions = self.model.predict(input_data)
        
        return predictions
    def get_file_extension(self):
        # Extrae la extensión del archivo (por ejemplo, ".h5" o ".pkl")
        return Path(self.model_file_path).suffix

    def is_keras_model(self):
        # Verifica si el archivo es compatible con Keras
        extension = self.get_file_extension()
        return extension in ['.h5', '.keras']

    def is_pickle_model(self):
        # Verifica si el archivo es un archivo Pickle (por ejemplo, ".pkl")
        extension = self.get_file_extension()
        return extension == '.pkl'
    
    def is_rds_model(self):
        # Verifica si el archivo es un archivo RDS (por ejemplo, ".rds")
        extension = self.get_file_extension()
        return extension == '.rds'

    # Función para verificar los endpoint
    def check_endpoint(self,url):
        try:
            response = requests.post(url)
            # Verificar que el estado de la respuesta sea 200 (OK)
            if response.status_code == 200:
                print(f"El endpoint {url} está funcionando.")
            else:
                print(f"El endpoint {url} no respondió correctamente. Código de estado: {response.status_code}")
        except requests.ConnectionError:
            print(f"No se pudo conectar al endpoint {url}. Verifica que la API esté en ejecución.")
