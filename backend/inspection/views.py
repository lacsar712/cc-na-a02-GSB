from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from inspection.models import AidCard, Inspection
from inspection.rules import judge


def _can_write(user) -> bool:
    return user.groups.filter(name="inspector").exists()


def health(_request):
    from django.http import JsonResponse

    return JsonResponse({"status": "ok", "service": "nav-aid-inspection"})


@require_http_methods(["GET", "POST"])
def login_view(request):
    from django.contrib.auth import authenticate, login

    error = ""
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", ""),
        )
        if user is None:
            error = "用户名或密码错误"
        else:
            login(request, user)
            return redirect("list")
    return render(request, "login.html", {"error": error})


def logout_view(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect("login")


@login_required
def ledger_view(request):
    cards = list(AidCard.objects.all())
    counts = {}
    for row in Inspection.objects.values("aid_code").annotate(n=models.Count("id")):
        counts[row["aid_code"]] = row["n"]
    for card in cards:
        card.inspection_count = counts.get(card.aid_code, 0)
    return render(request, "ledger.html", {"cards": cards})


@login_required
def card_detail_view(request, aid_code):
    card = get_object_or_404(AidCard, aid_code=aid_code)
    rows = Inspection.objects.filter(aid_code=card.aid_code)
    return render(request, "card_detail.html", {"card": card, "rows": rows})


@login_required
@require_http_methods(["GET", "POST"])
def card_create_view(request):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅持灯账号可建台账卡")
    error = ""
    if request.method == "POST":
        code = request.POST.get("aid_code", "").strip()
        waterway = request.POST.get("waterway", "").strip()
        try:
            nominal = float(request.POST["nominal_cd"])
            if not code or not waterway:
                raise ValueError("empty")
        except (KeyError, ValueError):
            error = "请填灯号、所在水道和标称坎德拉"
        else:
            if AidCard.objects.filter(aid_code=code).exists():
                error = f"灯号 {code} 已建过台账卡，无需重复建卡"
            else:
                AidCard.objects.create(
                    aid_code=code,
                    waterway=waterway,
                    nominal_cd=nominal,
                    created_by=request.user.username,
                )
                return redirect("card_detail", aid_code=code)
    return render(request, "card_form.html", {"error": error})


@login_required
def list_view(request):
    rows = Inspection.objects.all()
    return render(request, "list.html", {"rows": rows, "can_write": _can_write(request.user)})


@login_required
def detail_view(request, pk):
    row = get_object_or_404(Inspection, pk=pk)
    return render(request, "detail.html", {"row": row})


@login_required
@require_http_methods(["GET", "POST"])
def create_view(request):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅巡检员可登记灯光巡检")
    cards = AidCard.objects.all()
    error = ""
    if request.method == "POST":
        code = request.POST.get("aid_code", "").strip()
        try:
            measured = float(request.POST["measured_cd"])
            bearing = float(request.POST["bearing_error_deg"])
        except (KeyError, ValueError):
            error = "请填实测光强和方位偏差"
        else:
            card = AidCard.objects.filter(aid_code=code).first() if code else None
            if not code:
                error = "请选择灯号"
            elif card is None:
                error = f"灯号 {code} 还没有台账卡：每座灯须先建卡才能挂巡检，请先在灯标台账中建卡"
            else:
                verdict, note = judge(measured, card.nominal_cd, bearing)
                row = Inspection.objects.create(
                    aid_code=card.aid_code,
                    measured_cd=measured,
                    required_cd=card.nominal_cd,
                    bearing_error_deg=bearing,
                    verdict=verdict,
                    note=note,
                    created_by=request.user.username,
                )
                return redirect("detail", pk=row.pk)
    return render(request, "form.html", {"error": error, "cards": cards})
