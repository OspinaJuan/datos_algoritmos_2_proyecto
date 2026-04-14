from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

tareas = {}

# modelo para crear tarea
class Tarea(BaseModel):
    titulo: str = Field(..., min_length=3)
    descripcion: Optional[str] = None
    completada: bool = False
    prioridad: int = Field(..., ge=1, le=5)


# modelo para actualizar
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    completada: Optional[bool] = None
    prioridad: Optional[int] = Field(None, ge=1, le=5)


# endpoint inicial para probar
@app.get("/")
def inicio():
    return {"mensaje": "API funcionando"}


# crear tarea
@app.post("/tareas")
def crear_tarea(tarea: Tarea):
    if tarea.titulo in tareas:
        raise HTTPException(status_code=400, detail="La tarea ya existe")

    tareas[tarea.titulo] = tarea.dict()
    return tareas[tarea.titulo]


# obtener todas las tareas
@app.get("/tareas")
def obtener_tareas():
    return list(tareas.values())


# obtener una tarea
@app.get("/tareas/{titulo}")
def obtener_tarea(titulo: str):
    if titulo not in tareas:
        raise HTTPException(status_code=404, detail="No encontrada")

    return tareas[titulo]


# actualizar tarea
@app.put("/tareas/{titulo}")
def actualizar_tarea(titulo: str, datos: TareaUpdate):
    if titulo not in tareas:
        raise HTTPException(status_code=404, detail="No encontrada")

    tarea = tareas[titulo]

    # actualizar solo lo que venga
    if datos.descripcion is not None:
        tarea["descripcion"] = datos.descripcion

    if datos.completada is not None:
        tarea["completada"] = datos.completada

    if datos.prioridad is not None:
        tarea["prioridad"] = datos.prioridad

    return tarea


# eliminar tarea
@app.delete("/tareas/{titulo}")
def eliminar_tarea(titulo: str):
    if titulo not in tareas:
        raise HTTPException(status_code=404, detail="No encontrada")

    del tareas[titulo]
    return {"mensaje": "Tarea eliminada"}


# filtrar por prioridad
@app.get("/tareas/prioridad/{prioridad}")
def tareas_por_prioridad(prioridad: int):
    if prioridad < 1 or prioridad > 5:
        raise HTTPException(status_code=400, detail="Prioridad invalida")

    resultado = []

    for t in tareas.values():
        if t["prioridad"] == prioridad:
            resultado.append(t)

    return resultado
