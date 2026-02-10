from django.shortcuts import render, get_object_or_404, redirect
from services.models import Service
from services.forms_service import ServiceFormNoCar


def services_edit(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == "POST":
        form = ServiceFormNoCar(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect("services_list")
    else:
        form = ServiceFormNoCar(instance=service)
    return render(request, "services_edit.html", {"form": form, "service": service})


def services_delete(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == "POST":
        service.delete()
        return redirect("services_list")
    return render(request, "services_delete.html", {"service": service})
