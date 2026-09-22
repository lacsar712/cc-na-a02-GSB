from django.db import models


class AidCard(models.Model):
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
    aid_code = models.CharField("航标编号", max_length=40)
    measured_cd = models.FloatField("实测光强")
    required_cd = models.FloatField("要求光强")
    bearing_error_deg = models.FloatField("方位偏差")
    verdict = models.CharField("结论", max_length=20)
    note = models.CharField("说明", max_length=200)
    created_by = models.CharField("登记人", max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
