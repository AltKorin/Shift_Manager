# System Zarządzania Grafikami Pracowniczymi

Prosty system Django do zarządzania grafikami pracy z możliwością składania wniosków o zmiany wymagających akceptacji przełożonego.

## Funkcje

### Dla Pracowników
- Przeglądanie własnych zmian w kalendarzu tygodniowym
- Składanie wniosków o:
  - Zamianę zmiany z innym pracownikiem
  - Anulowanie zmiany
  - Modyfikację godzin zmiany
  - Dodanie nowej zmiany
- Śledzenie statusu swoich wniosków
- Panel główny z nadchodzącymi zmianami

### Dla Przełożonych
- Wszystkie funkcje pracownika
- Przeglądanie grafików swoich podwładnych
- Akceptowanie/odrzucanie wniosków o zmiany
- Dodawanie notatek do rozpatrzonych wniosków
- Automatyczne wykonywanie zaakceptowanych zmian

## Instalacja

### 1. Wymagania
- Python 3.8+
- Django 4.2+
- pip

### 2. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 3. Konfiguracja projektu Django

#### a) Dodaj aplikację do settings.py

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shift_manager',  # <-- dodaj tutaj
]

# Ustaw polską lokalizację
LANGUAGE_CODE = 'pl-pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True
```

#### b) Dodaj URLe do głównego urls.py

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shift_manager.urls')),  # <-- dodaj tutaj
]
```

### 4. Migracje bazy danych

```bash
python manage.py makemigrations shift_manager
python manage.py migrate
```

### 5. Utwórz superużytkownika

```bash
python manage.py createsuperuser
```

### 6. Uruchom serwer

```bash
python manage.py runserver
```

## Pierwsze kroki

### 1. Dodaj pracowników

Zaloguj się do panelu admina: `http://localhost:8000/admin/`

1. Najpierw utwórz użytkowników Django (Users)
   - Dodaj imię i nazwisko
   - Ustaw hasło

2. Utwórz profile pracowników (Employees)
   - Przypisz użytkownika
   - Ustaw stanowisko
   - **Oznacz przełożonych** zaznaczając "Czy przełożony"
   - Przypisz przełożonego dla zwykłych pracowników

### 2. Dodaj zmiany do grafiku

W panelu admina dodaj zmiany (Shifts):
- Wybierz pracownika
- Ustaw datę
- Wybierz typ zmiany (poranna/popołudniowa/nocna/cały dzień)
- Ustaw godziny

### 3. Pracownicy mogą teraz:

1. Zalogować się na: `http://localhost:8000/`
2. Zobaczyć swoje nadchodzące zmiany
3. Przeglądać grafik tygodniowy
4. Składać wnioski o zmiany

### 4. Przełożeni mogą:

1. Rozpatrywać wnioski w zakładce "Do rozpatrzenia"
2. Akceptować lub odrzucać wnioski z opcjonalnymi notatkami
3. System automatycznie wykona zmianę w grafiku po akceptacji

## Typy wniosków

### Zamiana zmiany
Pracownik może zaproponować zamianę swojej zmiany ze zmianą innego pracownika (pod tym samym przełożonym).

### Anulowanie zmiany
Usunięcie zmiany z grafiku.

### Modyfikacja godzin
Zmiana daty, godzin lub typu istniejącej zmiany.

### Dodanie zmiany
Wniosek o dodanie nowej zmiany do grafiku.

## Struktura plików

```
shift_manager/
├── models.py              # Modele: Employee, Shift, ShiftChangeRequest
├── views.py               # Widoki aplikacji
├── forms.py               # Formularze
├── urls.py                # Mapowanie URLi
├── admin.py               # Konfiguracja panelu admina
└── templates/
    └── shift_manager/
        ├── base.html              # Szablon bazowy
        ├── dashboard.html         # Panel główny
        ├── schedule.html          # Grafik tygodniowy
        ├── request_change.html    # Formularz wniosku
        ├── review_request.html    # Rozpatrywanie wniosku
        ├── my_requests.html       # Lista moich wniosków
        └── pending_requests.html  # Wnioski do rozpatrzenia
```

## Rozszerzanie systemu

### Dodanie powiadomień email
W metodach `approve()` i `reject()` modelu `ShiftChangeRequest` możesz dodać wysyłkę emaili:

```python
from django.core.mail import send_mail

def approve(self, supervisor, notes=""):
    # ... istniejący kod ...
    
    # Wyślij email do pracownika
    send_mail(
        'Wniosek zaakceptowany',
        f'Twój wniosek został zaakceptowany przez {supervisor.user.get_full_name()}',
        'noreply@hotel.pl',
        [self.employee.user.email],
    )
```

### Dodanie eksportu do PDF/Excel
Możesz dodać funkcje eksportu grafiku używając bibliotek jak `reportlab` lub `openpyxl`.

### Integracja z systemem kadrowym
Modele można rozszerzyć o dodatkowe pola lub zintegrować z istniejącym systemem poprzez API.

## Licencja

Ten projekt jest dostępny na licencji MIT. Możesz go swobodnie używać i modyfikować dla własnych potrzeb.

## Wsparcie

W razie pytań lub problemów:
1. Sprawdź logi Django
2. Upewnij się, że wszystkie migracje zostały wykonane
3. Sprawdź, czy pracownicy mają przypisanych przełożonych

## Changelog

### v1.0.0 (2024)
- Podstawowa funkcjonalność zarządzania grafikami
- System wniosków z akceptacją
- Widok kalendarza tygodniowego
- Panel dla przełożonych
- Panel dla pracowników
