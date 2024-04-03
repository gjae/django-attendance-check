from django.shortcuts import render
from django.http.response import JsonResponse
from django.forms.models import model_to_dict

from src.dining_room.models import DiningChecking
from src.employees.models import Employee

# Create your views here.

def index(request, *args, **kwargs):
    today_checks = DiningChecking.objects.today_checks()

    return render(
        request, 
        "dining_room/index.html", 
        {"today_checks": today_checks}
    )

def default_today_last_checks(request, *args, **kwargs):
    today_checks = DiningChecking.objects.today_checks().order_by("-created")[0:39]
    response = []
    for check in today_checks:
        response.append({
            "name": check.employer.name,
            "lastname": check.employer.last_name,
            "position": check.employer.position.position if check.employer.position is not None else '',
            "department": check.employer.department.name if check.employer.department is not None else '',
            "id": check.employer.id,
            "avatar": check.employer.picture.url if check.employer is not None and check.employer.picture.name else '',
            "is_birthday": check.employer.is_birthday,
            "check_turn": check.conf_dining_room.check_name,
            "check_at": check.created.strftime("%H:%M")
        })
        
    return JsonResponse({
        "error": False,
        "data": response
    })


def check_dining_employer(request, card_id, *args, **kwargs):
    emp = Employee.objects.select_related("position", "department").filter(cedula=card_id).first()
    if emp is None:
        return JsonResponse({
            "error": True, 
            "can_check": False, 
            "checked": False,
            "employer": None
        })
    
    check = DiningChecking.objects.make_check_if_can(emp)

    if check is None:
        return JsonResponse({
            "error": True, 
            "can_check": True, 
            "checked": False,
            "employer": None
        })
    
    return JsonResponse({
        "error": False,
        "can_check": True,
        "checked": True,
        "employer": {
            "name": emp.name,
            "lastname": emp.last_name,
            "position": emp.position.position if emp.position is not None else '',
            "department": emp.department.name if emp.department is not None else '',
            "id": emp.id,
            "avatar": emp.picture.url if emp is not None and emp.picture.name else '',
            "is_birthday": emp.is_birthday,
            "check_turn": check.conf_dining_room.check_name,
            "check_at": check.created.strftime("%H:%M a")
        }
    })