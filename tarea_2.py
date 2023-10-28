# -*- coding: utf-8 -*-
"""Tarea_2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mq4ZfV6pFr2ESOdRDXd8Fg-b7UUVse_4

# Universidad de O'Higgins

## Escuela de Ingeniería
## COM4402: Introducción a Inteligencia Artificial

### **Tarea 2: Clasificación de Dígitos Manuscritos con Redes Neuronales**

### Estudiante: Emilio Cáceres

El objetivo de esta tarea es utilizar redes neuronales en un problema de clasificación de dígitos. Se utilizará el conjunto de datos Optical Recognition of Handwritten Digits Data Set. Este conjunto tiene 64 características, con 10 clases y 5620 muestras en total. La base de datos estará disponible en U-Campus.

Las redes a ser entrenadas tienen la siguiente estructura: capa de entrada de dimensionalidad 64 (correspondiente a los datos de entrada), capas ocultas (una o dos) y capa de salida con 10 neuronas y función de activación softmax. La función de loss (pérdida) es entropía cruzada. El optimizador que se
debe usar es Adam. La función softmax está implícita al usar la función de pérdida CrossEntropyLoss de PyTorch (**no se debe agregar softmax a la salida de la red**).

Se usará PyTorch para entrenar y validar la red neuronal que implementa el clasificador de dígitos. Se analizará los efectos de cambiar el tamaño de la red (número de capas ocultas y de neuronas en estas
capas) y la función de activación.

El siguiente código base debe ser usado para realizar las actividades pedidas.

## Observación: Antes de ejecutar su código, active el uso de GPU en Google Colab para acelerar el proceso de entrenamiento.

### Para esto: vaya a "Entorno de Ejecución" en el menú superior, haga click en "Cambiar tipo de entorno de ejecución", y seleccionar/verificar "GPU" en "Acelerador de Hardware"

## Importar Librerías
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
import torch.optim as optim

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score

import copy
import time

"""## Subir datasets de dígitos (train)"""

!wget https://raw.githubusercontent.com/Felipe1401/Mineria/main/dataset_digits/1_digits_train.txt
!wget https://raw.githubusercontent.com/Felipe1401/Mineria/main/dataset_digits/1_digits_test.txt

"""## Leer dataset de dígitos"""

column_names = ["feat" + str(i) for i in range(64)]
column_names.append("class")

df_train_val = pd.read_csv('1_digits_train.txt', names = column_names)
df_train_val

df_test = pd.read_csv('1_digits_test.txt', names = column_names)
df_test

df_train, df_val = train_test_split(df_train_val, test_size = 0.3, random_state = 10)

scaler = StandardScaler().fit(df_train.iloc[:,0:64])
df_train.iloc[:,0:64] = scaler.transform(df_train.iloc[:,0:64])
df_val.iloc[:,0:64] = scaler.transform(df_val.iloc[:,0:64])
df_test.iloc[:,0:64] = scaler.transform(df_test.iloc[:,0:64])

df_train

"""## Crear datasets y dataloaders para pytorch (train)"""

# Crear datasets
feats_train = df_train.to_numpy()[:,0:64].astype(np.float32)
labels_train = df_train.to_numpy()[:,64].astype(int)
dataset_train = [ {"features":feats_train[i,:], "labels":labels_train[i]} for i in range(feats_train.shape[0]) ]

feats_val = df_val.to_numpy()[:,0:64].astype(np.float32)
labels_val = df_val.to_numpy()[:,64].astype(int)
dataset_val = [ {"features":feats_val[i,:], "labels":labels_val[i]} for i in range(feats_val.shape[0]) ]

feats_test = df_test.to_numpy()[:,0:64].astype(np.float32)
labels_test = df_test.to_numpy()[:,64].astype(int)
dataset_test = [ {"features":feats_test[i,:], "labels":labels_test[i]} for i in range(feats_test.shape[0]) ]

# Crear dataloaders
dataloader_train = torch.utils.data.DataLoader(dataset_train, batch_size=128, shuffle=True, num_workers=0)
dataloader_val = torch.utils.data.DataLoader(dataset_val, batch_size=128, shuffle=True, num_workers=0)
dataloader_test = torch.utils.data.DataLoader(dataset_test, batch_size=128, shuffle=True, num_workers=0)

"""## Crear modelo"""

# Funcion para crear modelos de redes neuronales

def create_model(neuronas_co, fun_act, capas_ocultas=1):
    # Inicializa una lista llamada 'layers' para almacenar las capas de la red
    layers = [nn.Linear(64, neuronas_co), nn.ReLU() if fun_act == "ReLU" else nn.Tanh()]

    # Agrega capas ocultas si se especifica más de una capa
    for _ in range(capas_ocultas - 1):
        # Agrega una capa lineal seguida de una función de activación (ReLU o Tanh) a la lista 'layers'
        layers.extend([nn.Linear(neuronas_co, neuronas_co), nn.ReLU() if fun_act == "ReLU" else nn.Tanh()])

    # Agrega una capa lineal adicional después de las capas ocultas
    layers.append(nn.Linear(neuronas_co, 10))

    # Crea un modelo secuencial utilizando las capas definidas en 'layers'
    model = nn.Sequential(*layers)

    return model  # Devuelve el modelo creado

# Creacion de un diccionario que contiene informacion sobre varios modelos
dic = {}

# Define diferentes modelos con configuraciones especificas y los almacena en el diccionario

dic["model1"] = {"neuronas_co": 10, "fun_act": "ReLU"}
# Model 1: 10 neuronas en la capa oculta, funcion de activacion ReLU.

dic["model2"] = {"neuronas_co": 40, "fun_act": "ReLU"}
# Model 2: 40 neuronas en la capa oculta, funcion de activacion ReLU.

dic["model3"] = {"neuronas_co": 10, "fun_act": "Tanh"}
# Model 3: 10 neuronas en la capa oculta, funcion de activacion Tangente hiperbolica (Tanh).

dic["model4"] = {"neuronas_co": 40, "fun_act": "Tanh"}
# Model 4: 40 neuronas en la capa oculta, funcion de activacion Tangente hiperbolica (Tanh).

dic["model5"] = {"capas_ocultas": 2, "neuronas_co": 10, "fun_act": "ReLU"}
# Model 5: 2 capas ocultas, cada una con 10 neuronas y funcion de activacion ReLU.

dic["model6"] = {"capas_ocultas": 2, "neuronas_co": 40, "fun_act": "ReLU"}
# Model 6: 2 capas ocultas, cada una con 40 neuronas y funcion de activacion ReLU.

# Crear modelos basados en el diccionario original

models = {}  # Inicializa un diccionario llamado 'models' para almacenar los modelos

patience_values = [5, 10, 15, 20]  # Lista de valores de paciencia

for key, value in dic.items():
    if "capas_ocultas" in value:
        # Si el diccionario tiene la clave "capas_ocultas", usa el valor proporcionado
        model = create_model(neuronas_co=value["neuronas_co"], fun_act=value["fun_act"], capas_ocultas=value["capas_ocultas"])
    else:
        # Si no, crea un modelo con una sola capa oculta
        model = create_model(neuronas_co=value["neuronas_co"], fun_act=value["fun_act"])

    models[key] = []  # Crea una lista vacía para almacenar modelos con diferentes paciencias

    # Crear copias del modelo original con diferentes valores de paciencia
    for patience in patience_values:
        # Clona el modelo original usando copy.deepcopy() para evitar que compartan pesos
        model_copy = copy.deepcopy(model)
        # Agrega el modelo clonado y el valor de paciencia correspondiente a la lista de modelos
        models[key].append((model_copy, patience))

# El diccionario 'models' ahora contiene modelos con diferentes configuraciones y valores de paciencia.

# Verifica los modelos creados

for key, model in models.items():
    print(key)  # Imprime el nombre del modelo (por ejemplo, "model1", "model2", etc.)
    print(model)  # Imprime la lista de modelos y valores de paciencia asociados

# Este código recorre el diccionario 'models' e imprime los nombres de los modelos y la lista de modelos junto con sus valores de paciencia.

"""# Entrenamiento"""

# Inicializa una serie de listas y variables para almacenar información sobre el entrenamiento y los modelos
all_train_losses = []  # Almacena las pérdidas de entrenamiento de todos los modelos
all_val_losses = []    # Almacena las pérdidas de validación de todos los modelos
best_loss_train = []   # Almacena las mejores pérdidas de entrenamiento
best_loss_val = []     # Almacena las mejores pérdidas de validación
bests_accuracies = []  # Almacena los mejores accuracies de la mejor configuración
bests_models_patience = []  # Almacena los valores de "patience" para los mejores modelos
last_val_accuracy = None

# Inicializa variables para el mejor early stopping
best_accuracy_value = 0.0  # Inicializa con un valor bajo
best_patience = None    # Inicializa con None
name_best_model = None  # Inicializa con None
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')  # Establece el dispositivo como GPU si está disponible

# Recorre cada modelo y entrena
for model_name, model_list in models.items():
    for model, patience in model_list:
        print(f"Training model: {model_name} with patience: {patience}")
        print(model)

        # Mueve el modelo a la GPU si está disponible
        model = model.to(device)

        criterion = nn.CrossEntropyLoss()  # Define la función de pérdida
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)  # Configura el optimizador

        # Inicializa variables para el early stopping y el mejor accuracy
        best_val_loss = float('inf')  # Inicializa con un valor grande
        best_model_state_dict = None   # Guarda el estado del modelo con el mejor accuracy
        last_val_loss = float('inf')   # Inicializa con un valor grande
        wait = 0  # Contador para el early stopping

        # Inicializa listas para almacenar los resultados de entrenamiento y validación
        train_losses = []   # Almacena las pérdidas de entrenamiento
        val_losses = []     # Almacena las pérdidas de validación
        val_accuracies = []  # Almacena los accuracies de validación
        best_accuracy = 0.0

        # Inicializa listas para las predicciones y etiquetas verdaderas en el conjunto de prueba
        test_predicted_labels = []  # Almacena las predicciones en el conjunto de prueba
        test_true_labels = []  # Almacena las etiquetas verdaderas en el conjunto de prueba

        start = time.time()  # Registra el tiempo de inicio
        epocas = 1000  # Número máximo de épocas de entrenamiento

        for epoch in range(epocas):
            model.train()  # Establece el modelo en modo de entrenamiento
            train_loss_sum = 0.0  # Inicializa la suma de pérdidas de entrenamiento

            # Inicializa listas para almacenar predicciones y etiquetas verdaderas de entrenamiento en esta época
            train_predicted_labels = []
            train_true_labels = []

            for i, data in enumerate(dataloader_train, 0):
                inputs = data["features"].to(device)  # Mueve los datos de entrada a la GPU
                labels = data['labels'].to(device)     # Mueve las etiquetas a la GPU
                optimizer.zero_grad()  # Reinicia los gradientes
                outputs = model(inputs)  # Realiza una pasada hacia adelante
                loss = criterion(outputs, labels)  # Calcula la pérdida
                loss.backward()  # Realiza la retropropagación
                optimizer.step()  # Actualiza los pesos
                train_loss_sum += loss.item()  # Acumula la pérdida del lote

                # Almacena las predicciones y etiquetas verdaderas de este lote
                _, predicted = torch.max(outputs, 1)
                train_predicted_labels.extend(predicted.cpu().numpy())
                train_true_labels.extend(labels.cpu().numpy())

            # Calcula el promedio de las pérdidas de entrenamiento
            average_train_loss = train_loss_sum / len(dataloader_train)
            train_losses.append(average_train_loss)  # Guarda las pérdidas del entrenamiento

            model.eval()  # Establece el modelo en modo de evaluación
            val_loss_sum = 0.0  # Inicializa la suma de pérdidas de validación

            with torch.no_grad():
                for data in dataloader_val:
                    inputs = data['features'].to(device)
                    labels = data['labels'].to(device)
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    val_loss_sum += loss.item()  # Acumula la pérdida de validación
                    _, predicted = torch.max(outputs, 1)

                    # Almacena las predicciones y etiquetas verdaderas en el conjunto de prueba
                    test_predicted_labels.extend(predicted.cpu().numpy())
                    test_true_labels.extend(labels.cpu().numpy())

                # Calcula el promedio de las pérdidas de validación
                average_val_loss = val_loss_sum / len(dataloader_val)
                val_losses.append(average_val_loss)

                # Calcula el accuracy utilizando accuracy_score
                val_accuracy = accuracy_score(test_true_labels, test_predicted_labels)
                val_accuracies.append(val_accuracy)

                # Imprime o almacena las pérdidas de entrenamiento y validación para cada época
                print(f'Epoch {epoch} - Training Loss: {average_train_loss} - Validation Loss: {average_val_loss} - Accuracy: {val_accuracy}')

                # Comprueba si la pérdida en validación es mayor que en la época anterior (early stopping)
                if average_val_loss >= best_val_loss:
                    wait += 1
                    if wait >= patience:
                        print(f'Early stopping at epoch {epoch}')
                        break
                else:
                    wait = 0
                    best_val_loss = average_val_loss  # Actualiza el mejor valor de pérdida en validación

            last_val_loss = average_val_loss  # Actualiza la pérdida en validación de la época actual

            # Comprueba si el ultimo accuracy en validación es el mejor hasta ahora, sirve para escoger al mejor modelo de cada configuración
            if val_accuracy > best_accuracy:
                best_accuracy = val_accuracy
                best_patience = patience  # Actualiza el mejor valor de "patience"
                best_loss_train = train_losses  # Almacena las pérdidas de entrenamiento del mejor modelo
                best_loss_val = val_losses  # Almacena las pérdidas de validación del mejor modelo

        last_val_accuracy = val_accuracy  # Actualiza el último valor de accuracy

        # Comprueba si el ultimo accuracy en validación es el mejor hasta ahora, sirve para escoger al mejor modelo
        if last_val_accuracy > best_accuracy_value:
          best_accuracy_value = last_val_accuracy
          best_model = model
          name_best_model = model_name  # Almacena el nombre del mejor modelo

        end = time.time()
        print(f'Finished Training {model_name} with patience: {patience}, total time {end - start} seconds')

    # Agrega los resultados del mejor modelo a las listas globales
    all_train_losses.append(best_loss_train)
    all_val_losses.append(best_loss_val)
    bests_models_patience.append(best_patience)
    bests_accuracies.append(best_accuracy)

# Mostrar las mejores configuraciones, accuracies y descripción del modelo para cada modelo
for model_name, best_patience, best_acc in zip(models.keys(), bests_models_patience, bests_accuracies):
    print(f'Model: {model_name}')
    print(f'Model Description:\n{models[model_name][0][0]}\n')
    print(f'Best Patience: {best_patience}')
    print(f'Best Accuracy in Validation: {best_acc}\n')

"""# Gráfico de Función de Pérdida"""

# Recorre cada modelo y sus pérdidas
for model_name, train_losses, val_losses in zip(models.keys(), all_train_losses, all_val_losses):
    print(f"Plotting losses for model: {model_name}")

    # Crea un rango de épocas basado en la longitud de las listas de pérdidas
    epochs = list(range(1, len(train_losses) + 1))

    # Graficar las pérdidas de entrenamiento y validación en función del tiempo
    plt.figure(figsize=(10, 6))  # Crea una figura para el gráfico
    plt.plot(epochs, train_losses, label='Training Loss', color='blue')  # Gráfica las pérdidas de entrenamiento
    plt.plot(epochs, val_losses, label='Validation Loss', color='red')  # Gráfica las pérdidas de validación
    plt.xlabel('Epoch')  # Etiqueta del eje x
    plt.ylabel('Loss')  # Etiqueta del eje y
    plt.legend()  # Agrega una leyenda al gráfico
    plt.title(f'Losses for model: {model_name}')  # Título del gráfico
    plt.grid(True)  # Habilita la cuadrícula en el gráfico

    plt.show()  # Muestra el gráfico en pantalla

"""# Matriz de Confusión"""

# Creacion de models2 para guardar los mejores modelos de cada configuracion
# Inicializa un nuevo diccionario donde copiarás los modelos
models2 = {}

# Obtiene la lista de nombres de modelos en el mismo orden que en "models"
model_names = list(models.keys())

for i, desired_patience in enumerate(bests_models_patience):
    model_name = model_names[i]  # Obtiene el nombre del modelo actual
    if model_name in models:
        model_data = models[model_name]  # Obtiene la lista de modelos para el modelo actual
        for model, patience in model_data:
            if patience == desired_patience:
                # Si el modelo ya existe en "models2", agrega este modelo a la lista
                if model_name in models2:
                    models2[model_name].append(model)
                else:
                    # Si el modelo no existe en "models2", crea una nueva lista y agrega el modelo
                    models2[model_name] = [model]
    else:
        print(f"Model {model_name} not found in the models dictionary.")

"""## Ambos"""

# Definir las clases
classes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Inicializa listas para las matrices de confusión y accuracy de validación y entrenamiento
val_confusion_matrices = []  # Almacena las matrices de confusión de validación
val_accuracies = []  # Almacena los accuracies de validación
train_confusion_matrices = []  # Almacena las matrices de confusión de entrenamiento
train_accuracies = []  # Almacena los accuracies de entrenamiento

for model_name, model_data in models2.items():
    print(f"Evaluating model: {model_name}")

    # Accede al modelo dentro de los datos del modelo actual
    model = model_data[0]

    # Coloca el modelo en modo de evaluación
    model.eval()

    # Inicializa listas para las predicciones y etiquetas verdaderas de validación
    val_predicted_labels = []  # Almacena las predicciones de validación
    val_true_labels = []  # Almacena las etiquetas verdaderas de validación

    # Inicializa listas para las predicciones y etiquetas verdaderas de entrenamiento
    train_predicted_labels = []  # Almacena las predicciones de entrenamiento
    train_true_labels = []  # Almacena las etiquetas verdaderas de entrenamiento

    # Realiza predicciones en el conjunto de validación y entrenamiento
    with torch.no_grad():
        for data in dataloader_val:  # Asegúrese de que dataloader_val esté definido y contenga los datos de validación
            inputs = data["features"].to(device)  # Asegúrese de que device esté definido
            labels = data["labels"].to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            val_predicted_labels.extend(predicted.cpu().numpy())
            val_true_labels.extend(labels.cpu().numpy())

        for data in dataloader_train:  # Asegúrese de que dataloader_train esté definido y contenga los datos de entrenamiento
            inputs = data["features"].to(device)
            labels = data["labels"].to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            train_predicted_labels.extend(predicted.cpu().numpy())
            train_true_labels.extend(labels.cpu().numpy())

    # Calcula la matriz de confusión y el accuracy para validación
    val_cm = confusion_matrix(val_true_labels, val_predicted_labels, labels=classes, normalize='true')
    val_confusion_matrices.append(val_cm)
    val_acc = accuracy_score(val_true_labels, val_predicted_labels)
    val_accuracies.append(val_acc)

    # Calcula la matriz de confusión y el accuracy para entrenamiento
    train_cm = confusion_matrix(train_true_labels, train_predicted_labels, labels=classes, normalize='true')
    train_confusion_matrices.append(train_cm)
    train_acc = accuracy_score(train_true_labels, train_predicted_labels)
    train_accuracies.append(train_acc)

    # Crear una figura con dos subplots para las matrices de confusión de validación y entrenamiento
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))  # Ajusta el tamaño de la figura

    fig.suptitle(f"Matrices de Confusión y Accuracy para modelo: {model_name}", fontsize=16)

    # Visualizar la matriz de confusión de entrenamiento
    ax = axes[0]
    sns.heatmap(train_cm, annot=True, fmt='.2f', cmap='Blues', cbar=True, square=True, ax=ax)  # Añade el colorbar
    ax.set_title(f"Entrenamiento \nAccuracy:{train_acc:.2f}")

    ax.set_xlabel('Clase Predicha')
    ax.set_ylabel('Clase Real')

    # Configurar etiquetas de clase
    tick_marks = np.arange(len(classes))
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(classes)
    ax.set_yticklabels(classes, rotation=0)

    # Visualizar la matriz de confusión de validación
    ax = axes[1]
    sns.heatmap(val_cm, annot=True, fmt='.2f', cmap='Blues', cbar=True, square=True, ax=ax)  # Añade el colorbar
    ax.set_title(f"Validación \nAccuracy:{val_acc:.2f}")
    ax.set_xlabel('Clase Predicha')
    ax.set_ylabel('Clase Real')

    # Configurar etiquetas de clase
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(classes)
    ax.set_yticklabels(classes, rotation=0)

    # Ajusta el espacio entre los subplots
    plt.tight_layout()

    # Mostrar la figura
    plt.show()

"""# Mejor Red"""

# Carga el mejor modelo
best_model_data = models[name_best_model]  # Asegúrate de que name_best_model esté definido y sea el nombre del mejor modelo
best_model = best_model_data[0]  # Accede al modelo dentro de la tupla
best_model = best_model[0].to(device)  # Mueve el mejor modelo a la GPU si está disponible

# Inicializa listas para las predicciones y etiquetas verdaderas en el conjunto de prueba
test_predicted_labels = []  # Almacena las predicciones en el conjunto de prueba
test_true_labels = []  # Almacena las etiquetas verdaderas en el conjunto de prueba

# Coloca el modelo en modo de evaluación
best_model.eval()

# Realiza predicciones en el conjunto de prueba
with torch.no_grad():
    for data in dataloader_test:  # Asegúrate de que dataloader_test contenga los datos de prueba
        inputs = data['features'].to(device)
        labels = data['labels'].to(device)
        outputs = best_model(inputs)
        _, predicted = torch.max(outputs, 1)
        test_predicted_labels.extend(predicted.cpu().numpy())
        test_true_labels.extend(labels.cpu().numpy())

# Calcula la matriz de confusión para el conjunto de prueba
test_cm = confusion_matrix(test_true_labels, test_predicted_labels, normalize='true')

# Calcula el accuracy para el conjunto de prueba
test_acc = accuracy_score(test_true_labels, test_predicted_labels)

# Grafica la matriz de confusión para el conjunto de prueba
plt.figure(figsize=(8, 6))
sns.heatmap(test_cm, annot=True, fmt=".2f", cmap="Blues")  # Crea un gráfico de la matriz de confusión
plt.title(f"Normalized Confusion Matrix for Test - {name_best_model}\nNormalized Accuracy: {test_acc:.2f}")  # Título del gráfico
plt.xlabel("Predicted")
plt.ylabel("True")

# Muestra la figura
plt.show()