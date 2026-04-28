from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from collections import deque

app = FastAPI()

tareas_dict = {}
tareas_lista = []
historial = []
pendientes = deque()


class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


class ListaEnlazada:
    def __init__(self):
        self.cabeza = None

    def agregar(self, valor):
        nuevo = Nodo(valor)
        if not self.cabeza:
            self.cabeza = nuevo
        else:
            actual = self.cabeza
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo

    def contiene(self, valor):
        actual = self.cabeza
        while actual:
            if actual.valor == valor:
                return True
            actual = actual.siguiente
        return False

    def obtener_todos(self):
        elementos = []
        actual = self.cabeza
        while actual:
            elementos.append(actual.valor)
            actual = actual.siguiente
        return elementos


class Grafo:
    def __init__(self):
        self.lista_adyacencia = {}

    def agregar_vertice(self, vertice):
        if vertice not in self.lista_adyacencia:
            self.lista_adyacencia[vertice] = ListaEnlazada()

    def agregar_arista(self, v1, v2):
        if v1 not in self.lista_adyacencia or v2 not in self.lista_adyacencia:
            raise ValueError()

        if not self.lista_adyacencia[v1].contiene(v2):
            self.lista_adyacencia[v1].agregar(v2)

        if not self.lista_adyacencia[v2].contiene(v1):
            self.lista_adyacencia[v2].agregar(v1)

    def adyacentes(self, vertice):
        if vertice not in self.lista_adyacencia:
            return []
        return self.lista_adyacencia[vertice].obtener_todos()

    def grado(self, vertice):
        return len(self.adyacentes(vertice))


grafo_tareas = Grafo()


class Tarea(BaseModel):
    titulo: str = Field(..., min_length=3)
    descripcion: Optional[str] = None
    completada: bool = False
    prioridad: int = Field(..., ge=1, le=5)


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    completada: Optional[bool] = None
    prioridad: Optional[int] = Field(None, ge=1, le=5)


@app.get("/")
def inicio():
    return {"mensaje": "API funcionando"}


@app.post("/tareas")
def crear_tarea(tarea: Tarea):
    if tarea.titulo in tareas_dict:
        raise HTTPException(status_code=400, detail="La tarea ya existe")

    data = tarea.dict()

    tareas_dict[tarea.titulo] = data
    tareas_lista.append(data)
    pendientes.append(data)
    historial.append(("crear", tarea.titulo))

    grafo_tareas.agregar_vertice(tarea.titulo)

    return data


@app.get("/tareas")
def obtener_tareas():
    return tareas_lista


@app.get("/tareas/{titulo}")
def obtener_tarea(titulo: str):
    if titulo not in tareas_dict:
        raise HTTPException(status_code=404, detail="No encontrada")

    return tareas_dict[titulo]


@app.put("/tareas/{titulo}")
def actualizar_tarea(titulo: str, datos: TareaUpdate):
    if titulo not in tareas_dict:
        raise HTTPException(status_code=404, detail="No encontrada")

    tarea = tareas_dict[titulo]
    copia = tarea.copy()

    if datos.descripcion is not None:
        tarea["descripcion"] = datos.descripcion

    if datos.completada is not None:
        tarea["completada"] = datos.completada

    if datos.prioridad is not None:
        tarea["prioridad"] = datos.prioridad

    historial.append(("actualizar", titulo, copia))

    return tarea


@app.delete("/tareas/{titulo}")
def eliminar_tarea(titulo: str):
    if titulo not in tareas_dict:
        raise HTTPException(status_code=404, detail="No encontrada")

    tarea = tareas_dict[titulo]

    tareas_lista.remove(tarea)
    del tareas_dict[titulo]

    historial.append(("eliminar", titulo, tarea))

    return {"mensaje": "Tarea eliminada"}


@app.get("/tareas/prioridad/{prioridad}")
def tareas_por_prioridad(prioridad: int):
    if prioridad < 1 or prioridad > 5:
        raise HTTPException(status_code=400, detail="Prioridad invalida")

    resultado = []

    for t in tareas_lista:
        if t["prioridad"] == prioridad:
            resultado.append(t)

    return resultado


@app.post("/deshacer")
def deshacer():
    if not historial:
        raise HTTPException(status_code=400, detail="Nada que deshacer")

    accion = historial.pop()

    if accion[0] == "crear":
        titulo = accion[1]
        tarea = tareas_dict[titulo]

        tareas_lista.remove(tarea)
        pendientes.remove(tarea)
        del tareas_dict[titulo]

        return {"mensaje": "Creacion deshecha"}

    elif accion[0] == "eliminar":
        titulo = accion[1]
        tarea = accion[2]

        tareas_dict[titulo] = tarea
        tareas_lista.append(tarea)

        return {"mensaje": "Eliminacion deshecha"}

    elif accion[0] == "actualizar":
        titulo = accion[1]
        datos_anteriores = accion[2]

        tareas_dict[titulo] = datos_anteriores

        for i in range(len(tareas_lista)):
            if tareas_lista[i]["titulo"] == titulo:
                tareas_lista[i] = datos_anteriores

        return {"mensaje": "Actualizacion deshecha"}


@app.get("/pendientes")
def ver_pendientes():
    return list(pendientes)


@app.post("/pendientes/atender")
def atender_pendiente():
    if not pendientes:
        raise HTTPException(status_code=400, detail="No hay pendientes")

    return pendientes.popleft()


@app.post("/relaciones")
def crear_relacion(t1: str, t2: str):
    if t1 not in tareas_dict or t2 not in tareas_dict:
        raise HTTPException(status_code=404, detail="Una de las tareas no existe")

    try:
        grafo_tareas.agregar_arista(t1, t2)
    except:
        raise HTTPException(status_code=400, detail="Error al crear relacion")

    return {"mensaje": "Relacion creada"}


@app.get("/tareas/{titulo}/relaciones")
def ver_relaciones(titulo: str):
    if titulo not in tareas_dict:
        raise HTTPException(status_code=404, detail="No encontrada")

    return grafo_tareas.adyacentes(titulo)


@app.get("/tareas/{titulo}/grado")
def grado_tarea(titulo: str):
    if titulo not in tareas_dict:
        raise HTTPException(status_code=404, detail="No encontrada")

    return {"grado": grafo_tareas.grado(titulo)}