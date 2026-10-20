from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Company(models.Model):
    """An employer. Postings and applications hang off a company."""

    name = models.CharField(max_length=200, unique=True)
    careers_url = models.URLField(blank=True)  # text fields use blank=True, not null=True

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Posting(models.Model):
    """A job posting, usually imported from jobscout. Matched by URL on re-import."""

    class Tier(models.TextChoices):
        # Mirrors jobscout's digest tiers.
        APPLY_TODAY = "apply_today", "Apply today"
        WORTH_A_LOOK = "worth_a_look", "Worth a look"
        OLDER = "older", "Older"
        NOT_A_FIT = "not_a_fit", "Probably not a fit"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,  # deleting a company deletes its postings
        related_name="postings",   # enables company.postings.all()
    )
    title = models.CharField(max_length=300)
    url = models.URLField(max_length=500, unique=True)  # natural key for the importer
    location = models.CharField(max_length=200, blank=True)
    posted_on = models.DateField(null=True, blank=True)  # non-text fields need null=True too
    fit_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    tier = models.CharField(max_length=20, choices=Tier.choices, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-first_seen"]

    def __str__(self):
        return f"{self.company} — {self.title}"


class Application(models.Model):
    """My application to one posting, tracked from applied to outcome."""

    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREEN = "screen", "Recruiter screen"
        INTERVIEWING = "interviewing", "Interviewing"
        OFFER = "offer", "Offer"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    posting = models.OneToOneField(
        Posting,
        on_delete=models.CASCADE,
        related_name="application",  # enables posting.application
    )
    applied_on = models.DateField()
    resume_version = models.CharField(max_length=100, blank=True)
    referral = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.APPLIED
    )
    notes = models.TextField(blank=True)  # TextField: no length limit, for free-form notes
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_on"]

    def __str__(self):
        return f"{self.posting} ({self.get_status_display()})"
