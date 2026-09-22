from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from inspection.models import Inspection, LightCard
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
def list_view(request):
    rows = Inspection.objects.select_related("card").all()
    return render(request, "list.html", {"rows": rows, "can_write": _can_write(request.user)})


@login_required
def detail_view(request, pk):
    row = get_object_or_404(Inspection.objects.select_related("card"), pk=pk)
    return render(request, "detail.html", {"row": row})


@login_required
@require_http_methods(["GET", "POST"])
def create_view(request):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅巡检员可登记灯光巡检")
    cards = LightCard.objects.all()
    error = ""
    selected = ""
    measured = ""
    bearing = ""
    if request.method == "POST":
        selected = request.POST.get("aid_code", "").strip()
        card = LightCard.objects.filter(aid_code=selected).first()
        # 无卡不许挂巡检：表单停在原处并写出缺卡原因
        if card is None:
            label = selected or "（未填写灯号）"
            error = (
                f"缺卡：灯号 {label} 尚未建立台账卡，不能登记巡检。"
                "请先在灯标台账中为该灯建卡，再回来登记。"
            )
        else:
            try:
                measured = float(request.POST["measured_cd"])
                bearing = float(request.POST["bearing_error_deg"])
            except (KeyError, ValueError):
                error = "请填写实测光强和方位偏差两项数值"
            else:
                verdict, note = judge(measured, card.nominal_cd, bearing)
                row = Inspection.objects.create(
                    card=card,
                    measured_cd=measured,
                    required_cd=card.nominal_cd,
                    bearing_error_deg=bearing,
                    verdict=verdict,
                    note=note,
                    created_by=request.user.username,
                )
                return redirect("detail", pk=row.pk)
    return render(
        request,
        "form.html",
        {
            "error": error,
            "cards": cards,
            "selected": selected,
            "measured": measured,
            "bearing": bearing,
        },
    )


@login_required
def card_list_view(request):
    cards = LightCard.objects.all()
    return render(
        request,
        "cards.html",
        {"cards": cards, "can_write": _can_write(request.user)},
    )


@login_required
def card_detail_view(request, pk):
    card = get_object_or_404(LightCard, pk=pk)
    rows = card.inspections.all()
    return render(
        request,
        "card_detail.html",
        {"card": card, "rows": rows, "can_write": _can_write(request.user)},
    )


@login_required
@require_http_methods(["GET", "POST"])
def card_create_view(request):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅持灯账号可建立灯标台账卡")
    error = ""
    form = {"aid_code": "", "waterway": "", "nominal_cd": ""}
    if request.method == "POST":
        form = {
            "aid_code": request.POST.get("aid_code", "").strip(),
            "waterway": request.POST.get("waterway", "").strip(),
            "nominal_cd": request.POST.get("nominal_cd", "").strip(),
        }
        if not form["aid_code"] or not form["waterway"]:
            error = "请填写灯号和所在水道"
        else:
            try:
                nominal = float(form["nominal_cd"])
                if nominal <= 0:
                    raise ValueError
            except ValueError:
                nominal = None
                error = "标称坎德拉须为大于零的数值"
            if not error and LightCard.objects.filter(aid_code=form["aid_code"]).exists():
                error = f"灯号 {form['aid_code']} 的台账卡已存在，无需重复建卡"
            if not error:
                card = LightCard.objects.create(
                    aid_code=form["aid_code"],
                    waterway=form["waterway"],
                    nominal_cd=nominal,
                    created_by=request.user.username,
                )
                return redirect("card_detail", pk=card.pk)
    return render(request, "card_form.html", {"error": error, "form": form})
