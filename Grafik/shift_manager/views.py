from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Employee, Shift, ShiftChangeRequest, Department
from .forms import ShiftChangeRequestForm, EmployeeProfileForm, ShiftForm
from django.contrib.auth import logout
from .forms import ShiftForm          # ← formularz do tworzenia zmiany
from .models import ShiftHistory      # ← model historii
from .models import log_shift_history # ← helper do logowania historii (jeśli w models.py)
from datetime import datetime, timedelta

@login_required
def app_logout(request):
    """Wylogowanie z aplikacji i powrót na stronę logowania"""
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    """Panel główny pracownika"""
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.warning(request, "Brak profilu pracownika. Uzupełnij dane, aby korzystać z systemu.")
        return redirect('create_employee_profile')
    
    # Nadchodzące zmiany (następne 14 dni)
    today = timezone.now().date()
    upcoming_shifts = Shift.objects.filter(
        employee=employee,
        date__gte=today,
        date__lte=today + timedelta(days=14)
    ).order_by('date', 'start_time')
    
    # Moje wnioski
    my_requests = ShiftChangeRequest.objects.filter(
        employee=employee
    ).order_by('-created_at')[:10]
    
    # Jeśli jestem przełożonym - wnioski do rozpatrzenia
    pending_requests = None
    if employee.is_supervisor_like:
        pending_requests = ShiftChangeRequest.objects.filter(
            employee__supervisor=employee,
            status='pending'
        ).order_by('created_at')
    
    context = {
        'employee': employee,
        'upcoming_shifts': upcoming_shifts,
        'my_requests': my_requests,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'shift_manager/dashboard.html', context)


@login_required
def schedule_view(request):
    """Widok grafiku - kalendarz tygodniowy z uwzględnieniem ról i działów"""
    employee = request.user.employee_profile

    # DATA BAZOWA
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    # Poniedziałek tego tygodnia i niedziela
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # FILTR DZIAŁU (dla kadry)
    selected_department_id = request.GET.get('department')
    selected_department = None

    # Bazowy queryset na zmiany
    shifts_qs = Shift.objects.filter(
        date__gte=start_of_week,
        date__lte=end_of_week,
    ).select_related('employee__user', 'employee__department')

    # LOGIKA WIDOCZNOŚCI W ZALEŻNOŚCI OD ROLI
    if not employee.is_supervisor_like:
        # Zwykły pracownik → tylko swoje zmiany
        shifts_qs = shifts_qs.filter(employee=employee)

    else:
        # supervisor / manager / director
        # Dla supervisorów: tylko ich zespół + oni sami
        if employee.role == 'supervisor':
            shifts_qs = shifts_qs.filter(
                Q(employee=employee) | Q(employee__supervisor=employee)
            )

        # manager / director
        elif employee.role in ('manager', 'director'):
            # jeśli wybrano dział w filtrze → ten dział
            if selected_department_id:
                shifts_qs = shifts_qs.filter(employee__department_id=selected_department_id)
                try:
                    selected_department = Department.objects.get(id=selected_department_id)
                except Department.DoesNotExist:
                    selected_department = None
            else:
                # jeśli manager ma własny dział, domyślnie pokazujemy jego dział
                if employee.department:
                    shifts_qs = shifts_qs.filter(employee__department=employee.department)
                    selected_department = employee.department
                # jeśli nie ma działu (np. dyrektor), pokazuje wszystko
                else:
                    pass

        else:
            # fallback – traktuj jak supervisor
            shifts_qs = shifts_qs.filter(
                Q(employee=employee) | Q(employee__supervisor=employee)
            )

    shifts_qs = shifts_qs.order_by('date', 'start_time', 'employee__user__last_name')

    # ORGANIZACJA PO DNIACH
    week_schedule = {}
    current = start_of_week
    while current <= end_of_week:
        week_schedule[current] = {
            'date': current,
            'shifts': [s for s in shifts_qs if s.date == current]
        }
        current += timedelta(days=1)

    # Lista działów tylko dla kadry
    departments = Department.objects.all().order_by('name') if employee.is_supervisor_like else None

    context = {
        'employee': employee,
        'week_schedule': week_schedule,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'prev_week': start_of_week - timedelta(days=7),
        'next_week': start_of_week + timedelta(days=7),
        'departments': departments,
        'selected_department': selected_department,
        'selected_department_id': selected_department_id or '',
        'today': timezone.now().date(),
    }

    return render(request, 'shift_manager/schedule.html', context)


@login_required
def request_change(request, shift_id=None):
    """Formularz wniosku o zmianę"""
    employee = request.user.employee_profile
    shift = None
    
    if shift_id:
        shift = get_object_or_404(Shift, id=shift_id, employee=employee)
    
    if request.method == 'POST':
        form = ShiftChangeRequestForm(request.POST, employee=employee, shift=shift)
        if form.is_valid():
            change_request = form.save(commit=False)
            change_request.employee = employee
            if shift:
                change_request.shift = shift
            change_request.save()
            
            messages.success(request, 'Wniosek został wysłany do przełożonego.')
            return redirect('dashboard')
    else:
        initial = {}
        if shift:
            initial = {
                'shift': shift,
                'new_date': shift.date,
                'new_start_time': shift.start_time,
                'new_end_time': shift.end_time,
                'new_shift_type': shift.shift_type,
            }
        form = ShiftChangeRequestForm(initial=initial, employee=employee, shift=shift)
    
    context = {
        'form': form,
        'shift': shift,
        'employee': employee,
    }
    
    return render(request, 'shift_manager/request_change.html', context)


@login_required
def review_request(request, request_id):
    """Rozpatrywanie wniosku przez przełożonego"""
    employee = request.user.employee_profile
    
    if not employee.is_supervisor:
        messages.error(request, 'Brak uprawnień.')
        return redirect('dashboard')
    
    change_request = get_object_or_404(
        ShiftChangeRequest,
        id=request_id,
        employee__supervisor=employee,
        status='pending'
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '')
        
        if action == 'approve':
            try:
                change_request.approve(employee, notes)
                messages.success(request, 'Wniosek został zaakceptowany.')
            except Exception as e:
                messages.error(request, f'Błąd przy akceptacji: {str(e)}')
        elif action == 'reject':
            change_request.reject(employee, notes)
            messages.success(request, 'Wniosek został odrzucony.')
        
        return redirect('pending_requests')
    
    context = {
        'change_request': change_request,
        'employee': employee,
    }
    
    return render(request, 'shift_manager/review_request.html', context)


@login_required
def pending_requests(request):
    """Lista wniosków oczekujących na rozpatrzenie"""
    employee = request.user.employee_profile
    
    if not employee.is_supervisor:
        messages.error(request, 'Brak uprawnień.')
        return redirect('dashboard')
    
    requests = ShiftChangeRequest.objects.filter(
        employee__supervisor=employee,
        status='pending'
    ).select_related('employee__user', 'shift').order_by('created_at')
    
    context = {
        'requests': requests,
        'employee': employee,
    }
    
    return render(request, 'shift_manager/pending_requests.html', context)


@login_required
def my_requests(request):
    """Moje wnioski"""
    employee = request.user.employee_profile
    
    requests = ShiftChangeRequest.objects.filter(
        employee=employee
    ).select_related('reviewed_by__user', 'shift').order_by('-created_at')
    
    context = {
        'requests': requests,
        'employee': employee,
    }
    
    return render(request, 'shift_manager/my_requests.html', context)

@login_required
def create_employee_profile(request):
    """Tworzenie profilu pracownika dla zalogowanego użytkownika"""
    # jeśli profil już istnieje, nie ma co tu robić
    try:
        request.user.employee_profile
        return redirect('dashboard')
    except Employee.DoesNotExist:
        pass

    if request.method == 'POST':
        form = EmployeeProfileForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.user = request.user
            employee.save()
            messages.success(request, 'Profil pracownika został utworzony.')
            return redirect('dashboard')
    else:
        form = EmployeeProfileForm()

    return render(request, 'shift_manager/create_employee.html', {
        'form': form,
    })

@login_required
def create_shift(request):
    """Tworzenie nowej zmiany – tylko dla przełożonych"""
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Brak profilu pracownika.")
        return redirect('create_employee_profile')

    if not employee.is_supervisor:
        messages.error(request, "Nie masz uprawnień do tworzenia zmian.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ShiftForm(request.POST)
        # ograniczamy wybór pracowników również przy POST
        form.fields['employee'].queryset = (
            Employee.objects.filter(supervisor=employee) |
            Employee.objects.filter(id=employee.id)
        )

        if form.is_valid():
            shift = form.save(commit=False)
            # WSTRZYKUJEMY użytkownika do instancji przed save
            shift._changed_by = request.user
            shift.save()
            messages.success(request, f"Utworzono zmianę dla {shift.employee.user.get_full_name()} na {shift.date}.")
            return redirect('schedule')
        else:
            # tymczasowo: pokaż błędy walidacji
            messages.error(request, f"Błędy w formularzu: {form.errors}")
    else:
        form = ShiftForm()
        form.fields['employee'].queryset = (
            Employee.objects.filter(supervisor=employee) |
            Employee.objects.filter(id=employee.id)
        )

    return render(request, 'shift_manager/create_shift.html', {
        'form': form,
        'employee': employee,
    })
    
@login_required
def delete_shift(request, shift_id):
    """Usuwanie zmiany – tylko dla przełożonych (swoich ludzi / siebie)"""
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Brak profilu pracownika.")
        return redirect('create_employee_profile')

    if not employee.is_supervisor:
        messages.error(request, "Nie masz uprawnień do usuwania zmian.")
        return redirect('dashboard')

    shift = get_object_or_404(Shift, id=shift_id)

    # Bezpieczeństwo: supervisor może usuwać tylko swoje i swoich podwładnych
    if shift.employee != employee and shift.employee.supervisor != employee:
        messages.error(request, "Nie możesz usuwać zmian spoza swojego zespołu.")
        return redirect('schedule')

    if request.method == 'POST':
        log_shift_history(
            action='deleted',
            shift=shift,
            changed_by=request.user,
            source='manual',
            extra_info="Usunięto z widoku grafiku"
        )
        date = shift.date
        staff_name = shift.employee.user.get_full_name()
        shift.delete()
        messages.success(
            request,
            f"Usunięto zmianę {staff_name} z dnia {date}."
        )
        return redirect('schedule')

    return render(request, 'shift_manager/delete_shift.html', {
        'shift': shift,
        'employee': employee,
    })

@login_required
def shift_history(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Brak profilu pracownika.")
        return redirect('create_employee_profile')

    if employee.is_supervisor_like:
        history = ShiftHistory.objects.select_related('employee', 'changed_by').all()
    else:
        history = ShiftHistory.objects.filter(
            employee=employee
        ).select_related('employee', 'changed_by')

    history = history.order_by('-created_at')

    return render(request, 'shift_manager/shift_history.html', {
        'history': history,
        'employee': employee,
    })