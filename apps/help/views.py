from __future__ import annotations

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.dashboard.overview import get_or_create_plan
from apps.home.forms import NewsletterForm

from .models import HelpArticle, HelpArticleFeedback, HelpCategory
from .services import search_articles


def _published_categories():
    return (
        HelpCategory.objects.filter(is_published=True)
        .annotate(
            article_count=Count(
                "articles",
                filter=Q(articles__is_published=True),
            )
        )
        .filter(article_count__gt=0)
    )


def _site_footer_context(**extra):
    ctx = {"newsletter_form": NewsletterForm()}
    ctx.update(extra)
    return ctx


@require_GET
def help_home(request):
    q = (request.GET.get("q") or "").strip()
    categories = _published_categories()
    results = search_articles(q, limit=40) if q else HelpArticle.objects.none()
    return render(
        request,
        "help/home.html",
        _site_footer_context(
            categories=categories,
            q=q,
            results=results,
            result_count=len(results) if q else 0,
        ),
    )


@require_GET
def help_category(request, category_slug):
    category = get_object_or_404(
        HelpCategory,
        slug=category_slug,
        is_published=True,
    )
    articles = category.articles.filter(is_published=True)
    return render(
        request,
        "help/category.html",
        _site_footer_context(
            category=category,
            articles=articles,
        ),
    )


@require_GET
def help_article(request, category_slug, article_slug):
    article = get_object_or_404(
        HelpArticle.objects.select_related("category").prefetch_related("attachments"),
        slug=article_slug,
        category__slug=category_slug,
        category__is_published=True,
        is_published=True,
    )
    related = (
        HelpArticle.objects.filter(
            category=article.category,
            is_published=True,
        )
        .exclude(pk=article.pk)[:3]
    )
    can_chat = False
    chat_gate = "anon"
    if request.user.is_authenticated:
        plan = get_or_create_plan(request.user)
        if plan.is_pro:
            can_chat = True
            chat_gate = "pro"
        else:
            chat_gate = "free"
    return render(
        request,
        "help/article.html",
        _site_footer_context(
            article=article,
            related=related,
            can_chat=can_chat,
            chat_gate=chat_gate,
            coach_url=reverse("dashboard:coach"),
            login_url=reverse("accounts:login"),
        ),
    )


@require_POST
def help_feedback(request, category_slug, article_slug):
    article = get_object_or_404(
        HelpArticle,
        slug=article_slug,
        category__slug=category_slug,
        is_published=True,
    )
    raw = (request.POST.get("helpful") or "").strip().lower()
    if raw not in {"yes", "no", "1", "0", "true", "false"}:
        return redirect(article.get_absolute_url())
    was_helpful = raw in {"yes", "1", "true"}
    if not request.session.session_key:
        request.session.save()
    HelpArticleFeedback.objects.create(
        article=article,
        was_helpful=was_helpful,
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or "",
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "helpful": was_helpful})
    return redirect(f"{article.get_absolute_url()}?feedback=1")


@require_http_methods(["GET", "POST"])
def help_api_suggest(request):
    """Public JSON: BrandBox Coach Agent reply grounded on Help articles."""
    from .coach_reply import synthesize_agent_reply

    if request.method == "POST":
        q = (request.POST.get("q") or request.POST.get("message") or "").strip()
    else:
        q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"matches": [], "reply": "", "guide_title": "", "guide_url": ""})
    synthesized = synthesize_agent_reply(q, request=request)
    return JsonResponse(
        {
            "matches": synthesized.get("matches") or [],
            "reply": synthesized.get("body") or "",
            "guide_title": synthesized.get("guide_title") or "",
            "guide_url": synthesized.get("guide_url") or "",
        }
    )
