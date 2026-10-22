from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from negocio.excepciones import ReglaNegocioError
from negocio.servicios import recetas
from presentacion.forms import RecetaOpticaForm
from presentacion.utilidades import paginar


@login_required
def resultados(request):
    busqueda = request.GET.get("q", "").strip()

    return render(request, "presentacion/resultados.html", {
        **paginar(request, recetas.resultados(busqueda)),
        "busqueda": busqueda,
    })


@login_required
def registrar_receta(request, id_examen):
    try:
        examen = recetas.examen_para_receta(id_examen)
    except ReglaNegocioError as error:
        messages.info(request, error.mensaje)
        return redirect("detalle_examen", id_examen)

    if request.method == "POST":
        form = RecetaOpticaForm(request.POST)

        if form.is_valid():
            try:
                receta = recetas.registrar(examen, form.cleaned_data)
                messages.success(
                    request, "Receta óptica registrada correctamente."
                )
                return redirect("ver_receta", receta.id_receta)

            except ReglaNegocioError as error:
                messages.error(request, error.mensaje)
    else:
        form = RecetaOpticaForm(
            initial={"fecha_emision": timezone.now().date()}
        )

    return render(request, "presentacion/registrar_receta.html", {
        "form": form,
        "examen": examen,
    })


@login_required
def ver_receta(request, id_receta):
    return render(request, "presentacion/receta_detalle.html", recetas.ficha(id_receta))
