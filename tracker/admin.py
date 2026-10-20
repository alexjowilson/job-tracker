from django.contrib import admin

from .models import Application, Company, Posting


class PostingInline(admin.TabularInline):
    model = Posting
    extra = 0
    fields = ("title", "tier", "fit_score", "url")
    show_change_link = True


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "careers_url")
    search_fields = ("name",)
    inlines = [PostingInline]


class ApplicationInline(admin.StackedInline):
    model = Application
    extra = 0


@admin.register(Posting)
class PostingAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "tier", "fit_score", "posted_on", "first_seen")
    list_filter = ("tier", "company")
    search_fields = ("title", "company__name")
    list_select_related = ("company",)
    inlines = [ApplicationInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("posting", "status", "applied_on", "resume_version", "referral")
    list_filter = ("status", "referral", "resume_version")
    search_fields = ("posting__title", "posting__company__name", "notes")
    list_select_related = ("posting", "posting__company")
    date_hierarchy = "applied_on"
