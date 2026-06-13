from django.contrib import admin
from django.utils.html import format_html
from .models import Election, Candidate, Voter, Vote, AuditLog


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'start_date', 'end_date', 'total_votes', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_votes']
    actions = ['activate_elections', 'close_elections']

    def activate_elections(self, request, queryset):
        queryset.filter(status='draft').update(status='active')
    activate_elections.short_description = "Activate selected elections"

    def close_elections(self, request, queryset):
        queryset.filter(status='active').update(status='closed')
    close_elections.short_description = "Close selected elections"


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'election', 'vote_count', 'vote_percentage', 'position']
    list_filter = ['election']
    search_fields = ['name', 'election__title']
    readonly_fields = ['id', 'created_at', 'vote_count', 'vote_percentage']


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ['name', 'voter_id', 'email', 'is_eligible', 'registered_at']
    list_filter = ['is_eligible']
    search_fields = ['name', 'voter_id', 'email']
    readonly_fields = ['id', 'registered_at']
    actions = ['mark_eligible', 'mark_ineligible']

    def mark_eligible(self, request, queryset):
        queryset.update(is_eligible=True)
    mark_eligible.short_description = "Mark selected voters as eligible"

    def mark_ineligible(self, request, queryset):
        queryset.update(is_eligible=False)
    mark_ineligible.short_description = "Mark selected voters as ineligible"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'candidate', 'voted_at', 'ip_address']
    list_filter = ['candidate__election']
    search_fields = ['voter__name', 'candidate__name']
    readonly_fields = ['id', 'voted_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'actor', 'timestamp', 'ip_address']
    list_filter = ['action']
    search_fields = ['actor', 'action']
    readonly_fields = ['id', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
