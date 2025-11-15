from django import forms
from .models import ShiftChangeRequest, Shift, Employee

class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        # user ustawimy w widoku, więc go tu nie pokazujemy
        fields = ['position', 'phone', 'supervisor', 'is_supervisor']
        labels = {
            'position': 'Stanowisko',
            'phone': 'Telefon',
            'supervisor': 'Przełożony',
            'is_supervisor': 'Czy jesteś przełożonym?',
        }
class ShiftForm(forms.ModelForm):
    date = forms.DateField(
        label='Data',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
    )
    start_time = forms.TimeField(
        label='Godzina rozpoczęcia',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'class': 'form-control'
            }
        )
    )
    end_time = forms.TimeField(
        label='Godzina zakończenia',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'class': 'form-control'
            }
        )
    )

    class Meta:
        model = Shift
        fields = ['employee', 'date', 'shift_type', 'start_time', 'end_time', 'notes']
        labels = {
            'employee': 'Pracownik',
            'shift_type': 'Typ zmiany',
            'notes': 'Notatki',
        }
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'shift_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ShiftChangeRequestForm(forms.ModelForm):
    """Formularz wniosku o zmianę w grafiku"""
    
    class Meta:
        model = ShiftChangeRequest
        fields = [
            'request_type',
            'swap_with_employee',
            'swap_shift',
            'new_date',
            'new_start_time',
            'new_end_time',
            'new_shift_type',
            'reason'
        ]
        widgets = {
            'new_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'new_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'new_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'new_shift_type': forms.Select(attrs={'class': 'form-control'}),
            'request_type': forms.Select(attrs={'class': 'form-control'}),
            'swap_with_employee': forms.Select(attrs={'class': 'form-control'}),
            'swap_shift': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Opisz powód wniosku...'}),
        }
        labels = {
            'request_type': 'Typ wniosku',
            'swap_with_employee': 'Zamiana z pracownikiem',
            'swap_shift': 'Zmiana do zamiany',
            'new_date': 'Nowa data',
            'new_start_time': 'Nowy początek',
            'new_end_time': 'Nowy koniec',
            'new_shift_type': 'Typ zmiany',
            'reason': 'Powód',
        }
    
    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        self.shift = kwargs.pop('shift', None)
        super().__init__(*args, **kwargs)
        
        # Ogranicz listę pracowników do kolegów z pracy (pod tym samym przełożonym)
        if self.employee and self.employee.supervisor:
            colleagues = Employee.objects.filter(
                supervisor=self.employee.supervisor
            ).exclude(id=self.employee.id).select_related('user')
            self.fields['swap_with_employee'].queryset = colleagues
        else:
            self.fields['swap_with_employee'].queryset = Employee.objects.none()
        
        # Ogranicz zmiany do zamiany
        self.fields['swap_shift'].queryset = Shift.objects.none()
        
        # Dynamicznie pokaż/ukryj pola w zależności od typu wniosku
        self.fields['swap_with_employee'].required = False
        self.fields['swap_shift'].required = False
        self.fields['new_date'].required = False
        self.fields['new_start_time'].required = False
        self.fields['new_end_time'].required = False
        self.fields['new_shift_type'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        
        if request_type == 'swap':
            if not cleaned_data.get('swap_with_employee') or not cleaned_data.get('swap_shift'):
                raise forms.ValidationError('Dla zamiany musisz wybrać pracownika i zmianę.')
        
        elif request_type == 'modify':
            if not any([
                cleaned_data.get('new_date'),
                cleaned_data.get('new_start_time'),
                cleaned_data.get('new_end_time'),
                cleaned_data.get('new_shift_type')
            ]):
                raise forms.ValidationError('Musisz podać przynajmniej jedną zmianę.')
        
        elif request_type == 'add':
            required_fields = ['new_date', 'new_start_time', 'new_end_time', 'new_shift_type']
            if not all(cleaned_data.get(field) for field in required_fields):
                raise forms.ValidationError('Dla nowej zmiany musisz podać wszystkie dane.')
        
        return cleaned_data


class ReviewRequestForm(forms.Form):
    """Formularz rozpatrywania wniosku"""
    action = forms.ChoiceField(
        choices=[('approve', 'Zaakceptuj'), ('reject', 'Odrzuć')],
        widget=forms.RadioSelect,
        label='Decyzja'
    )
    review_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        label='Notatki'
    )
