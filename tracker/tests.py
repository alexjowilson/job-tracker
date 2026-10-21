"""Tests for the tracker app: model rules (unit) and admin pages (integration)."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from tracker.models import Application, Company, Posting


@pytest.fixture
def company(db):
    return Company.objects.create(name="Fluke", careers_url="https://example.com/careers")


@pytest.fixture
def posting(company):
    return Posting.objects.create(
        company=company,
        title="Software Design Engineer",
        url="https://example.com/jobs/1",
        location="Everett, WA",
        fit_score=9,
        tier=Posting.Tier.APPLY_TODAY,
    )


# --- Model rules (unit tests) -------------------------------------------------


def test_str_representations(posting):
    app = Application.objects.create(posting=posting, applied_on=date(2026, 10, 13))
    assert str(posting.company) == "Fluke"
    assert str(posting) == "Fluke — Software Design Engineer"
    assert str(app) == "Fluke — Software Design Engineer (Applied)"


def test_posting_url_must_be_unique(posting):
    with pytest.raises(IntegrityError), transaction.atomic():
        Posting.objects.create(company=posting.company, title="Duplicate", url=posting.url)


def test_company_name_must_be_unique(company):
    with pytest.raises(IntegrityError), transaction.atomic():
        Company.objects.create(name="Fluke")


@pytest.mark.parametrize("score", [0, 11])
def test_fit_score_must_be_between_1_and_10(posting, score):
    posting.fit_score = score
    with pytest.raises(ValidationError):
        posting.full_clean()


def test_optional_fields_can_be_empty(company):
    p = Posting(company=company, title="Minimal", url="https://example.com/jobs/2")
    p.full_clean()  # location, posted_on, fit_score and tier are all optional
    p.save()
    assert p.first_seen is not None  # set automatically


def test_application_defaults(posting):
    app = Application.objects.create(posting=posting, applied_on=date(2026, 10, 13))
    assert app.status == Application.Status.APPLIED
    assert app.referral is False


def test_only_one_application_per_posting(posting):
    Application.objects.create(posting=posting, applied_on=date(2026, 10, 13))
    with pytest.raises(IntegrityError), transaction.atomic():
        Application.objects.create(posting=posting, applied_on=date(2026, 10, 14))


def test_related_names(posting):
    app = Application.objects.create(posting=posting, applied_on=date(2026, 10, 13))
    assert list(posting.company.postings.all()) == [posting]
    assert posting.application == app


def test_deleting_company_cascades(posting):
    Application.objects.create(posting=posting, applied_on=date(2026, 10, 13))
    posting.company.delete()
    assert Posting.objects.count() == 0
    assert Application.objects.count() == 0


# --- Admin pages (integration tests) -------------------------------------------


@pytest.mark.parametrize("model", ["company", "posting", "application"])
def test_admin_list_pages_load(admin_client, posting, model):
    response = admin_client.get(reverse(f"admin:tracker_{model}_changelist"))
    assert response.status_code == 200


def test_admin_posting_search(admin_client, posting):
    url = reverse("admin:tracker_posting_changelist")
    assert "Software Design Engineer" in admin_client.get(url, {"q": "design"}).text
    assert "Software Design Engineer" not in admin_client.get(url, {"q": "nomatch"}).text


def test_admin_requires_login(client):
    response = client.get(reverse("admin:tracker_posting_changelist"))
    assert response.status_code == 302  # redirected to the login page
