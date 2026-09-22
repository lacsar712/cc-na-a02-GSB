from django.db import models


class LightCard(models.Model):
    """灯标台账卡：先建卡，才允许在该灯号下挂巡检实测。"""

    aid_code = models.CharField("灯号", max_length=40, unique=True)
    waterway = models.CharField("所在水道", max_length=80)
    nominal_cd = models.FloatField("标称坎德拉")
    created_by = models.CharField("建卡人", max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["aid_code"]

    def __str__(self):
        return self.aid_code


class Inspection(models.Model):
    card = models.ForeignKey(
        LightCard,
        verbose_name="台账卡",
        on_delete=models.PROTECT,
        related_name="inspections",
    )
    measured_cd = models.FloatField("实测光强")
    required_cd = models.FloatField("要求光强")
    bearing_error_deg = models.FloatField("方位偏差")
    verdict = models.CharField("结论", max_length=20)
    note = models.CharField("说明", max_length=200)
    created_by = models.CharField("登记人", max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    @property
    def aid_code(self):
        return self.card.aid_code
