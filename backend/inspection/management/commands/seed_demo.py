from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from inspection.models import Inspection, LightCard
from inspection.rules import judge


class Command(BaseCommand):
    help = "seed accounts, light cards and inspections"

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name="inspector")
        keeper, created = User.objects.get_or_create(username="keeper")
        if created or not keeper.check_password("light123456"):
            keeper.set_password("light123456")
            keeper.save()
        keeper.groups.add(group)
        watch, created = User.objects.get_or_create(username="watch")
        if created or not watch.check_password("watch123456"):
            watch.set_password("watch123456")
            watch.save()
        watch.groups.remove(group)

        if Inspection.objects.exists():
            self.stdout.write("already seeded")
            return

        # 先建台账卡：灯号、所在水道、标称坎德拉
        cards = {
            code: LightCard.objects.create(
                aid_code=code,
                waterway=waterway,
                nominal_cd=nominal,
                created_by="keeper",
            )
            for code, waterway, nominal in [
                ("LH-01", "吴淞口北水道", 1200),
                ("LH-09", "吴淞口南水道", 1200),
                ("LH-18", "吴淞口主航道", 1200),
            ]
        }

        # 再把实测挂到对应卡上，没有卡的灯号无法登记
        samples = [
            ("LH-01", 1400, 0.4),
            ("LH-09", 800, 0.2),
            ("LH-18", 1450, 0.2),
        ]
        for code, measured, bearing in samples:
            card = cards[code]
            verdict, note = judge(measured, card.nominal_cd, bearing)
            Inspection.objects.create(
                card=card,
                measured_cd=measured,
                required_cd=card.nominal_cd,
                bearing_error_deg=bearing,
                verdict=verdict,
                note=note,
                created_by="keeper",
            )
        self.stdout.write("seeded")
