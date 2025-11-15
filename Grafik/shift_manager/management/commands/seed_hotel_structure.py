from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shift_manager.models import Employee, Department


class Command(BaseCommand):
    help = "Seeduje strukturę hotelu: działy, kadrę, technicznych itd."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(">> Start seeda hotelowego..."))

        # ===== 1. Działy =====
        departments_def = [
            ("Recepcja", "Recepcja"),
            ("Housekeeping", "Housekeeping"),
            ("Kuchnia", "Kuchnia"),
            ("Sala", "Sala"),
            ("Techniczni", "Techniczni"),
            ("Księgowość", "Ksiegowosc"),
            ("Management", "Management"),
            ("Właściciele", "Wlasciciele"),
        ]

        dept_objs = {}
        for name, short in departments_def:
            dept, _ = Department.objects.get_or_create(
                name=name,
                defaults={
                    "short_name": short,
                    "color": "#0d6efd",
                },
            )
            # jeśli rekord już istniał, zadbajmy żeby short_name był ustawiony
            if not dept.short_name:
                dept.short_name = short
                dept.save()
            dept_objs[name] = dept

        self.stdout.write(self.style.SUCCESS("✓ Działy gotowe"))

        # ===== Helper do tworzenia pracowników =====
        def create_emp(
            username,
            first_name,
            last_name,
            position,
            dept_name,
            role,
            supervisor=None,
            is_supervisor_flag=None,
            password="pass123",
        ):
            dept = dept_objs[dept_name]

            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "last_name": last_name},
            )
            # ujednolicamy dane (na devie to wygodne)
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.save()

            if is_supervisor_flag is None:
                is_supervisor_flag = role in ("supervisor", "manager", "director")

            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    "position": position,
                    "department": dept,
                    "role": role,
                    "supervisor": supervisor,
                    "is_supervisor": is_supervisor_flag,
                },
            )
            # aktualizacja w razie zmian
            emp.position = position
            emp.department = dept
            emp.role = role
            emp.supervisor = supervisor
            emp.is_supervisor = is_supervisor_flag
            emp.save()

            return emp

        # ===== 2. Top: właściciel, dyrektor, kierownik =====
        owner_jerzy = create_emp(
            username="jerzy.owner",
            first_name="Jerzy",
            last_name="Właściciel",
            position="Właściciel",
            dept_name="Właściciele",
            role="director",
            supervisor=None,
            password="pass123",  # zmień w prod
        )

        dyrektor_roma = create_emp(
            username="roma.dyrektor",
            first_name="Roma",
            last_name="Dyrektor",
            position="Dyrektor Hotelu",
            dept_name="Management",
            role="director",
            supervisor=owner_jerzy,
        )

        kierownik_konrad = create_emp(
            username="konrad.kierownik",
            first_name="Konrad",
            last_name="Kierownik",
            position="Kierownik Operacyjny",
            dept_name="Management",
            role="manager",
            supervisor=dyrektor_roma,
        )

        self.stdout.write(self.style.SUCCESS("✓ Właściciel, dyrektor, kierownik"))

        # ===== 3. Kuchnia =====
        szef_kuchni_michal = create_emp(
            username="michal.kuchnia",
            first_name="Michał",
            last_name="Szef",
            position="Szef Kuchni",
            dept_name="Kuchnia",
            role="supervisor",
            supervisor=kierownik_konrad,
        )

        # Możesz dorzucić zwykłych kucharzy, jak chcesz
        kucharz1 = create_emp(
            username="kuchnia1",
            first_name="Piotr",
            last_name="Kucharz",
            position="Kucharz",
            dept_name="Kuchnia",
            role="staff",
            supervisor=szef_kuchni_michal,
        )

        # ===== 4. Housekeeping =====
        hk_lider_natalia = create_emp(
            username="natalia.hk",
            first_name="Natalia",
            last_name="Lider",
            position="Lider Housekeepingu",
            dept_name="Housekeeping",
            role="supervisor",
            supervisor=kierownik_konrad,
        )

        hk1 = create_emp(
            username="hk1",
            first_name="Anna",
            last_name="Pokojowa",
            position="Pokojowa",
            dept_name="Housekeeping",
            role="staff",
            supervisor=hk_lider_natalia,
        )

        # ===== 5. Recepcja =====
        recepcja_lider_agnieszka = create_emp(
            username="agnieszka.recepcja",
            first_name="Agnieszka",
            last_name="Lider",
            position="Lider Recepcji",
            dept_name="Recepcja",
            role="supervisor",
            supervisor=kierownik_konrad,
        )

        recepcjonista1 = create_emp(
            username="recepcja1",
            first_name="Kasia",
            last_name="Recepcjonistka",
            position="Recepcjonistka",
            dept_name="Recepcja",
            role="staff",
            supervisor=recepcja_lider_agnieszka,
        )

        # ===== 6. Księgowość (Wiesia) =====
        ksiegowosc_wiesia = create_emp(
            username="wiesia.ksiegowosc",
            first_name="Wiesia",
            last_name="Księgowa",
            position="Księgowość / Recepcja",
            dept_name="Księgowość",
            role="manager",
            supervisor=kierownik_konrad,
        )

        # ===== 7. Sala =====
        sala_lider = create_emp(
            username="sala.lider",
            first_name="Marek",
            last_name="Kelner",
            position="Lider Sali",
            dept_name="Sala",
            role="supervisor",
            supervisor=kierownik_konrad,
        )

        kelner1 = create_emp(
            username="sala1",
            first_name="Ola",
            last_name="Kelnerka",
            position="Kelnerka",
            dept_name="Sala",
            role="staff",
            supervisor=sala_lider,
        )

        # ===== 8. Techniczni: Jurek (lider), Przemek, Karol, Sławek (kontraktor) =====
        tech_lider_jurek = create_emp(
            username="jurek.tech",
            first_name="Jurek",
            last_name="Techniczny",
            position="Lider Techniczny",
            dept_name="Techniczni",
            role="supervisor",
            supervisor=kierownik_konrad,
        )

        tech_przemek = create_emp(
            username="przemek.tech",
            first_name="Przemek",
            last_name="Techniczny",
            position="Konserwator",
            dept_name="Techniczni",
            role="staff",
            supervisor=tech_lider_jurek,
        )

        tech_karol = create_emp(
            username="karol.tech",
            first_name="Karol",
            last_name="Techniczny",
            position="Konserwator",
            dept_name="Techniczni",
            role="staff",
            supervisor=tech_lider_jurek,
        )

        tech_slawek = create_emp(
            username="slawek.tech",
            first_name="Sławek",
            last_name="Kontraktor",
            position="Kontraktor techniczny",
            dept_name="Techniczni",
            role="staff",
            supervisor=None,          # niezależny contractor
            is_supervisor_flag=False,
        )

        self.stdout.write(self.style.SUCCESS("✓ Techniczni (lider + zespół + kontraktor)"))

        self.stdout.write(self.style.SUCCESS("\n=== SEED HOTELU ZAKOŃCZONY ==="))
        self.stdout.write("Loginy testowe (hasło wszędzie: pass123):")
        self.stdout.write(" - Właściciel Jerzy:    jerzy.owner")
        self.stdout.write(" - Dyrektor Roma:      roma.dyrektor")
        self.stdout.write(" - Kierownik Konrad:   konrad.kierownik")
        self.stdout.write(" - Szef Kuchni Michał: michal.kuchnia")
        self.stdout.write(" - HK Lider Natalia:   natalia.hk")
        self.stdout.write(" - Recepcja Agnieszka: agnieszka.recepcja")
        self.stdout.write(" - Księgowość Wiesia:  wiesia.ksiegowosc")
        self.stdout.write(" - Tech lider Jurek:   jurek.tech")
        self.stdout.write(" - Tech kontraktor:    slawek.tech")
