from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('request-change/', views.request_change, name='request_change'),
    path('request-change/<int:shift_id>/', views.request_change, name='request_change_for_shift'),
    path('review/<int:request_id>/', views.review_request, name='review_request'),
    path('pending-requests/', views.pending_requests, name='pending_requests'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('create-profile/', views.create_employee_profile, name='create_employee_profile'),
    path('shifts/new/', views.create_shift, name='create_shift'),
    path('shifts/<int:shift_id>/delete/', views.delete_shift, name='delete_shift'),
    path('history/', views.shift_history, name='shift_history'),
    path('employees/create/', views.create_employee, name='create_employee'),
    path('shift/<int:shift_id>/status/<str:new_status>/', views.update_shift_status, name='update_shift_status'),

]
