from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, time
import random

from shift_manager.models import Employee, Shift, ShiftChangeRequest


class Command(BaseCommand):
    help = "Seed test data for Shift Manager"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Shift Manager test data...")

        # 1. Tworzymy głównego usera
        user, created = User.objects.get_or_create(
            username="testuser",
            defaults={
                "first_name": "Jan",
                "last_name": "Testowy",
                "email": "jan.testowy@example.com"
            }
        )
        if created:
            user.set_password("test123")
            user.save()

        # 2. Tworzymy profil pracownika
        employee, created = Employee.objects.get_or_create(
            user=user,
            defaults={
                "position": "Recepcjonista",
                "phone": "500600700",
                "is_supervisor": True
            }
        )

        # 3. Tworzymy kilka innych pracowników pod nim
        subordinates = []
        for i in range(3):
            u, _ = User.objects.get_or_create(
                username=f"pracownik{i+1}",
                defaults={
                    "first_name": f"Pracownik{i+1}",
                    "last_name": "Testowy",
                    "email": f"pracownik{i+1}@example.com"
                }
            )
            u.set_password("test123")
            u.save()

            e, _ = Employee.objects.get_or_create(
                user=u,
                defaults={
                    "position": "Obsługa",
                    "supervisor": employee
                }
            )
            subordinates.append(e)

        # 4. Tworzymy zmiany na 14 dni
        today = timezone.now().date()

        def create_shift(emp, date):
            shift_type = random.choice(['morning', 'evening', 'night'])
            if shift_type == 'morning':
                start, end = time(6, 0), time(14, 0)
            elif shift_type == 'evening':
                start, end = time(14, 0), time(22, 0)
            else:
                start, end = time(22, 0), time(6, 0)

            return Shift.objects.get_or_create(
                employee=emp,
                date=date,
                defaults={
                    "shift_type": shift_type,
                    "start_time": start,
                    "end_time": end
                }
            )

        for emp in [employee] + subordinates:
            for offset in range(1, 15):
                create_shift(emp, today + timedelta(days=offset))

        # 5. Tworzymy parę testowych wniosków
        for emp in subordinates:
            ShiftChangeRequest.objects.get_or_create(
                employee=emp,
                request_type="change_shift",
                new_date=today + timedelta(days=3),
                new_start_time=time(10, 0),
                new_end_time=time(18, 0),
                status='pending'
            )

        self.stdout.write(self.style.SUCCESS("Seed completed."))
        self.stdout.write("Logowanie testowe:")
        self.stdout.write("  login: testuser")
        self.stdout.write("  password: test123")
