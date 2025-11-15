from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
from shift_manager.models import Employee, Shift


class Command(BaseCommand):
    help = "Seeduje tydzień zmian dla hotelu – standardowy grafik"

    def handle(self, *args, **options):
        today = timezone.now().date()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        # Czyszczenie istniejących zmian w tym tygodniu
        Shift.objects.filter(date__gte=monday, date__lte=sunday).delete()

        self.stdout.write(self.style.WARNING(">>> Tworzę zmiany na tydzień:"))

        # Pobieramy pracowników
        def emp(username):
            return Employee.objects.get(user__username=username)

        # Zmiany – standardy
        def add_shift(employee, date, start, end, shift_type="custom"):
            Shift.objects.create(
                employee=employee,
                date=date,
                start_time=start,
                end_time=end,
                shift_type=shift_type,
                notes="(seed)"
            )

        # Zakres tygodnia
        for day_offset in range(7):
            date = monday + timedelta(days=day_offset)
            weekday = date.strftime("%A")

            # ===== TECHNICZNI =====
            add_shift(emp("jurek.tech"), date, time(8, 0), time(16, 0), "full")

            # Przemek i Karol rotacyjnie 08–16 lub 12–20
            if day_offset % 2 == 0:
                add_shift(emp("przemek.tech"), date, time(8, 0), time(16, 0), "morning")
                add_shift(emp("karol.tech"), date, time(12, 0), time(20, 0), "afternoon")
            else:
                add_shift(emp("przemek.tech"), date, time(12, 0), time(20, 0), "afternoon")
                add_shift(emp("karol.tech"), date, time(8, 0), time(16, 0), "morning")

            # Kontraktor Sławek – zwykle późna zmiana
            add_shift(emp("slawek.tech"), date, time(12, 0), time(20, 0), "afternoon")

            # ===== KSIĘGOWOŚĆ =====
            add_shift(emp("wiesia.ksiegowosc"), date, time(8, 0), time(16, 0), "full")

            # ===== RECEPCJA: dzień + noc =====
            add_shift(emp("agnieszka.recepcja"), date, time(7, 0), time(19, 0), "full")
            add_shift(emp("recepcja1"), date, time(19, 0), time(7, 0), "night")

            # ===== HOUSEKEEPING =====
            add_shift(emp("natalia.hk"), date, time(8, 0), time(16, 0), "full")
            add_shift(emp("hk1"), date, time(8, 0), time(16, 0), "full")

            # ===== SALA =====
            add_shift(emp("sala.lider"), date, time(7, 0), time(15, 0), "morning")
            add_shift(emp("sala1"), date, time(12, 0), time(20, 0), "afternoon")

            # ===== KUCHNIA =====
            add_shift(emp("michal.kuchnia"), date, time(7, 0), time(15, 0), "morning")
            add_shift(emp("kuchnia1"), date, time(12, 0), time(20, 0), "afternoon")

        self.stdout.write(self.style.SUCCESS("✓ Zmiany seedowane poprawnie!"))
        self.stdout.write(self.style.SUCCESS(f"Tydzień: {monday} → {sunday}"))
