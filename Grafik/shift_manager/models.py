from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Employee(models.Model):
    """Pracownik z powiązaniem do użytkownika Django"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, verbose_name="Stanowisko")
    supervisor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='subordinates',
        verbose_name="Przełożony"
    )
    is_supervisor = models.BooleanField(default=False, verbose_name="Czy przełożony")
    
    class Meta:
        verbose_name = "Pracownik"
        verbose_name_plural = "Pracownicy"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"


class Shift(models.Model):
    """Zmiana pracownika"""
    SHIFT_TYPES = [
        ('morning', 'Poranna (6:00-14:00)'),
        ('afternoon', 'Popołudniowa (14:00-22:00)'),
        ('night', 'Nocna (22:00-6:00)'),
        ('full', 'Cały dzień (8:00-16:00)'),
    ]
    
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='shifts'
    )
    date = models.DateField(verbose_name="Data")
    shift_type = models.CharField(
        max_length=20,
        choices=SHIFT_TYPES,
        verbose_name="Typ zmiany"
    )
    start_time = models.TimeField(verbose_name="Początek")
    end_time = models.TimeField(verbose_name="Koniec")
    notes = models.TextField(blank=True, verbose_name="Uwagi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Zmiana"
        verbose_name_plural = "Zmiany"
        ordering = ['-date', 'start_time']
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.date} ({self.get_shift_type_display()})"

def save(self, *args, **kwargs):
    self.full_clean()
    created = self.pk is None

    with transaction.atomic():
        overlapping = (
            Shift.objects
            .select_for_update()
            .filter(employee=self.employee, date=self.date)
            .exclude(pk=self.pk)
            .filter(
                start_time__lte=self.end_time,
                end_time__gte=self.start_time,
            )
        )

        if overlapping.exists():
            old_ids = list(overlapping.values_list('id', flat=True))

            all_starts = [self.start_time] + [s.start_time for s in overlapping]
            all_ends = [self.end_time] + [s.end_time for s in overlapping]

            self.start_time = min(all_starts)
            self.end_time = max(all_ends)

            other_notes = [s.notes for s in overlapping if s.notes]
            if self.notes:
                other_notes.insert(0, self.notes)
            if other_notes:
                self.notes = " | ".join(other_notes)

            super().save(*args, **kwargs)

            log_shift_history(
                action='merged',
                shift=self,
                changed_by=getattr(self, '_changed_by', None),
                source='merge',
                extra_info=f"Scalono zmiany: {old_ids}"
            )

            overlapping.delete()
        else:
            super().save(*args, **kwargs)
            log_shift_history(
                action='created' if created else 'updated',
                shift=self,
                changed_by=getattr(self, '_changed_by', None),
                source='manual',
            )

class ShiftChangeRequest(models.Model):
    """Wniosek o zmianę w grafiku"""
    STATUS_CHOICES = [
        ('pending', 'Oczekuje'),
        ('approved', 'Zaakceptowany'),
        ('rejected', 'Odrzucony'),
    ]
    
    REQUEST_TYPES = [
        ('swap', 'Zamiana zmiany'),
        ('cancel', 'Anulowanie zmiany'),
        ('modify', 'Modyfikacja godzin'),
        ('add', 'Dodanie zmiany'),
    ]
    
    shift = models.ForeignKey(
        Shift, 
        on_delete=models.CASCADE, 
        related_name='change_requests',
        null=True,
        blank=True,
        verbose_name="Zmiana"
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='my_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name="Typ wniosku")
    
    # Dla zamiany
    swap_with_employee = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='swap_requests',
        verbose_name="Zamiana z"
    )
    swap_shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='swap_requests',
        verbose_name="Zmiana do zamiany"
    )
    
    # Dla nowych/zmienionych zmian
    new_date = models.DateField(null=True, blank=True, verbose_name="Nowa data")
    new_start_time = models.TimeField(null=True, blank=True, verbose_name="Nowy początek")
    new_end_time = models.TimeField(null=True, blank=True, verbose_name="Nowy koniec")
    new_shift_type = models.CharField(max_length=20, choices=Shift.SHIFT_TYPES, blank=True)
    
    reason = models.TextField(verbose_name="Powód")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    
    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
        verbose_name="Rozpatrzony przez"
    )
    review_notes = models.TextField(blank=True, verbose_name="Notatki przełożonego")
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Wniosek o zmianę"
        verbose_name_plural = "Wnioski o zmiany"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.get_request_type_display()} ({self.get_status_display()})"
    
    def approve(self, supervisor, notes=""):
        """Zaakceptuj wniosek"""
        self.status = 'approved'
        self.reviewed_by = supervisor
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()
        
        # Wykonaj zmianę w grafiku
        if self.request_type == 'cancel' and self.shift:
            self.shift.delete()
        elif self.request_type == 'modify' and self.shift:
            if self.new_date:
                self.shift.date = self.new_date
            if self.new_start_time:
                self.shift.start_time = self.new_start_time
            if self.new_end_time:
                self.shift.end_time = self.new_end_time
            if self.new_shift_type:
                self.shift.shift_type = self.new_shift_type
            self.shift.save()
        elif self.request_type == 'add':
            Shift.objects.create(
                employee=self.employee,
                date=self.new_date,
                start_time=self.new_start_time,
                end_time=self.new_end_time,
                shift_type=self.new_shift_type,
                notes=f"Dodane przez wniosek #{self.id}"
            )
        elif self.request_type == 'swap' and self.swap_with_employee:
            # Zamień pracowników między zmianami
            if self.shift and self.swap_shift:
                original_employee = self.shift.employee
                swap_employee = self.swap_shift.employee
                
                self.shift.employee = swap_employee
                self.swap_shift.employee = original_employee
                
                self.shift.save()
                self.swap_shift.save()
    
    def reject(self, supervisor, notes=""):
        """Odrzuć wniosek"""
        self.status = 'rejected'
        self.reviewed_by = supervisor
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()
class ShiftHistory(models.Model):
    ACTION_CHOICES = [
        ('created', 'Utworzono'),
        ('updated', 'Zaktualizowano'),
        ('merged', 'Scalono'),
        ('deleted', 'Usunięto'),
    ]

    shift = models.ForeignKey(
        'Shift',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='history_entries',
        verbose_name='Powiązana zmiana'
    )

    employee = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shift_history',
        verbose_name='Pracownik'
    )

    # snapshot wartości w momencie operacji
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    shift_type = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='performed_shift_changes',
        verbose_name='Zmienione przez'
    )

    source = models.CharField(
        max_length=50,
        blank=True,
        help_text="Źródło zmiany, np. 'manual', 'request', 'merge', 'seed'"
    )

    extra_info = models.TextField(
        blank=True,
        help_text="Dodatkowe informacje (np. poprzednie ID, powód zmiany)"
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Historia zmiany"
        verbose_name_plural = "Historia zmian"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} - {self.employee} - {self.date} {self.start_time}-{self.end_time}"
def log_shift_history(action, shift, changed_by=None, source="", extra_info=""):
    """
    Tworzy wpis w historii zmian na podstawie aktualnego stanu shift.
    """
    from .models import ShiftHistory  # jeśli helper przeniesiesz gdzie indziej

    return ShiftHistory.objects.create(
        shift=shift if action != 'deleted' else None,
        employee=shift.employee if shift else None,
        date=shift.date if shift else None,
        start_time=shift.start_time if shift else None,
        end_time=shift.end_time if shift else None,
        shift_type=shift.shift_type if shift else "",
        notes=shift.notes if shift and shift.notes else "",
        action=action,
        changed_by=changed_by,
        source=source,
        extra_info=extra_info or "",
    )
    
    