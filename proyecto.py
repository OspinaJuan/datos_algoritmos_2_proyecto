from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from collections import deque

app = FastAPI()

tareas_dict = {}
tareas_lista = []
historial = []
pendientes = deque()


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