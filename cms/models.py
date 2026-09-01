from datetime import date
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.search import index
from taggit.models import TaggedItemBase
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager


# Create your models here.
class BlogPage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("body")]

    template = "blog/blog_page.html"

    def get_context(self, request):
        tag = request.GET.get("tag")
        if tag:
            articles = (
                ArticlePage.objects.filter(tags__name=tag)
                .live()
                .order_by("-first_published_at")
            )
        else:
            articles = self.get_children().live().order_by("-first_published_at")

        context = super().get_context(request)
        context["articles"] = articles
        context["tag"] = tag
        return context


class ArticlePage(Page):
    intro = models.CharField(max_length=80)
    body = RichTextField(blank=True)
    date = models.DateField("Post date", default=date.today)
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    caption = models.CharField(blank=True, max_length=80)
    tags = ClusterTaggableManager(through="ArticleTag", blank=True)

    def get_author(self):
        return self.owner.username

    def get_author_first_name(self):
        return self.owner.first_name

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("get_author"),
        index.SearchField("get_author_first_name"),
    ]

    template = "blog/article_page.html"

    content_panels = [
        FieldPanel("title"),
        FieldPanel("intro"),
        FieldPanel("image"),
        FieldPanel("caption"),
        FieldPanel("body"),
        FieldPanel("date"),
        FieldPanel("tags"),
    ]


class ArticleTag(TaggedItemBase):
    content_object = ParentalKey(
        ArticlePage,
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )
