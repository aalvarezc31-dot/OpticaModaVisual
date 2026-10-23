from django.contrib import messages
from presentacion.sesion import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from presentacion.cliente_api import ReglaNegocioError
from presentacion.servicios import citas, examenes
from presentacion.forms import ExamenVisualForm
from presentacion.utilidades import mostrar_error, paginar


@login_required
def lista_examenes(request):
    busqueda = request.GET.get("q", "").strip()

    return render(request, "presentacion/examenes.html", {
        **paginar(request, examenes.buscar_con_paciente(busqueda)),
        "busqueda": busqueda,
    })


def _valores_iniciales(request):
    """Permite abrir el formulario desde una cita: ?cita=ID."""
    iniciales = {
        "fecha_examen": timezone.now().strftime("%Y-%m-%dT%H:%M"),
    }

    if request.GET.get("cita", "").isdigit():
        cita = citas.obtener(int(request.GET["cita"]))
        iniciales.update({
            "cita": cita.id_cita,
            "cliente": cita.id_cliente,
            "optometrista": cita.id_usuario_atiende,
            "motivo_consulta": cita.motivo,
        })
    elif request.GET.get("cliente", "").isdigit():
        iniciales["cliente"] = int(request.GET["cliente"])

    return iniciales


@login_required
def registrar_examen(request):
    if request.method == "POST":
        form = ExamenVisualForm(request.POST)

        if form.is_valid():
            datos = dict(form.cleaned_data)
            datos["id_cliente"] = datos.pop("cliente")
            datos["id_cita"] = datos.pop("cita")
            datos["id_optometrista"] = datos.pop("optometrista")

            try:
                examen = examenes.registrar(datos)
                messages.success(
                    request,
                    f"Examen #{examen.id_examen} registrado correctamente."
                )
                return redirect("detalle_examen", examen.id_examen)

            except ReglaNegocioError as error:
                # La API nombra los campos por su id: id_cita -> cita
                error.campo = (error.campo or "").removeprefix("id_") or None
                mostrar_error(request, form, error)
    else:
        form = ExamenVisualForm(initial=_valores_iniciales(request))

    return render(request, "presentacion/examen_form.html", {"form": form})


@login_required
def detalle_examen(request, id_examen):
    return render(request, "presentacion/examen_detalle.html", examenes.ficha(id_examen))
