# Amr monday evening###########
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


# main/dashboard/category_views.py

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .forms import *
# 
# You'll create this form
from .models import Category
from .models import Tag 

def is_admin(user):
    return user.is_staff


@login_required
@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'dashboard/category_list.html', {'categories': categories})


@login_required
@user_passes_test(lambda u: u.is_staff)
def category_create(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    return render(request, 'dashboard/category_form.html', {'form': form})
#
@login_required
@user_passes_test(lambda u: u.is_staff)
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('category_list')
    return render(request, 'dashboard/category_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'dashboard/category_confirm_delete.html', {'category': category})




def project_list(request):
    projects = Project.objects.select_related('category', 'creator').prefetch_related('tags').all()
    return render(request, 'dashboard/project_list.html', {'projects': projects})

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)  
            project.creator = request.user  
            project.save()
            form.save_m2m()  
            return redirect('project_list')
    else:
        form = ProjectForm()

    categories = Category.objects.all()
    tags = Tag.objects.all()

    return render(request, 'dashboard/project_form.html', {
        'form': form,
        'categories': categories,
        'tags': tags,
    })



# # Amr monday evening###########
# class AdminDashboardView(LoginRequiredMixin, View):
#     def get(self, request):
#         # Only show the logged-in user's data
#         projects = Project.objects.all()
#         categories = Category.objects.all()
#         tags = Tag.objects.all()

#         context = {
#             'projects': projects,
#             'categories': categories,
#             'tags': tags,
#         }
#         return render(request, 'dashboard/admin_dashboard.html', context)
    
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
import math
from users.models import User
from dashboard.models import Project, Category, Tag
from interactions.models import Donation, Comment, Rating, Report

# Add custom template filter for range
from django.template.defaulttags import register

@method_decorator(staff_member_required, name='dispatch')
class AdminDashboardView(View):
    """Admin dashboard view showing project statistics and management options"""
    template_name = 'dashboard/admin_dashboard.html'
    def get(self, request):

        context = {}
        # getting counts for main entities
        context['total_users'] = User.objects.count()
        context['total_projects'] = Project.objects.count()
        context['total_categories'] = Category.objects.count()
        context['total_tags'] = Tag.objects.count()
        context['total_donations'] = Donation.objects.count()
        context['total_comments'] = Comment.objects.count()
        context['total_reports'] = Report.objects.count()
        context['unresolved_reports'] = Report.objects.filter(is_resolved=False)
        
        # getting the users to pass to admin
        context['users'] = User.objects.all()
        
        # getting donation statistics
        context['total_donation_amount'] = Donation.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # getting recent activity
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['recent_projects'] = Project.objects.order_by('-start_time')[:5]
        context['recent_donations'] = Donation.objects.order_by('-created_at')[:5]
        
        # getting top categories by project count
        context['top_categories'] = Category.objects.annotate(
            project_count=Count('project')
        ).order_by('-project_count')[:5]
        
        # getting top donors
        context['top_donors'] = User.objects.annotate(
            donation_total=Sum('donations__amount')
        ).exclude(donation_total=None).order_by('-donation_total')[:5]
        
        # getting projects statistics by time
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)
        
        context['new_projects_month'] = Project.objects.filter(
            start_time__gte=thirty_days_ago
        ).count()
        
        context['new_users_month'] = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()
        

        # adding chunks for the users_management component 

        user_chunks = []
        page_size = 6
        user_count = context['total_users']
        # fetching the users with their related donations if exists
        users = User.objects.all().order_by('-date_joined').prefetch_related(
            'donations',
            'donations__project'  # This prefetches the related project objects
        )

        # Now attach donation history with specific fields to each user
        for user in users:
            donations_list = list(user.donations.all().order_by('-created_at'))
            
            if donations_list:
                # Create a structured donation history with the fields you want
                user.donation_history = [
                    {
                        'amount': donation.amount,
                        'created_at': donation.created_at,
                        'project_id': donation.project.id,
                        'project_title': donation.project.title,
                        'project_details': donation.project.details
                    }
                    for donation in donations_list
                ]
            else:
                user.donation_history = None

        for i in range(0, user_count, page_size):
            user_chunks.append(users[i: i+page_size])
        context['user_chunks'] = user_chunks

        print("x"*60)
        print(context['user_chunks'][0][4].donation_history)
        print("x"*60)
        ##################################################

        

        @register.filter
        def rerange(value):
            return range(value)
            

        return render(request, self.template_name, context)
    

# #### trying to implement the edit user data page
# class EditUserData(LoginRequiredMixin, UpdateView): 
#     def get(self, request):
#         return render(request, 'dacshboard/edit_user_data.html')
    
# class EditProfile(LoginRequiredMixin, UpdateView):
#     model = User
#     template_name = "main/edit_profile.html"
#     form_class = UserUpdateForm  
#     success_url = reverse_lazy("profile") 

#     # to edit the current user rather than passing the user pk in the url 
#     def get_object(self, queryset=None):
#         return self.request.user