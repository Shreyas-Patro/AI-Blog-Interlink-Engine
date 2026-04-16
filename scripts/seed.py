#!/usr/bin/env python3
from pathlib import Path

posts = {
    "seo-basics.md": """---
title: SEO Basics for Beginners
slug: seo-basics
url: https://myblog.com/seo-basics
tags: [seo, beginners]
---

## What is SEO

Search engine optimization (SEO) is the practice of improving your website to increase organic
traffic from search engines. It involves optimizing content, improving site structure, and
building quality backlinks. When done correctly, SEO can dramatically increase your website's
visibility in search results pages. Most businesses rely on organic search as a primary source
of website traffic, making SEO a critical marketing discipline.

## On-Page SEO Techniques

On-page SEO refers to optimizations you make directly on your website pages. This includes
writing high-quality content that satisfies user intent, optimizing title tags and meta
descriptions, using header tags effectively to organize content hierarchy, and ensuring your
images have descriptive alt text. Internal linking is a crucial on-page technique that helps
search engines understand your site structure and distributes link equity across your pages.
Proper keyword placement throughout your content signals relevance to search engines.

## Technical SEO Fundamentals

Technical SEO focuses on improving the backend structure of your website. Key areas include
site speed optimization, mobile responsiveness, XML sitemaps, robots.txt configuration, and
structured data markup. A technically sound website ensures search engines can crawl and index
your content efficiently. Core Web Vitals have become increasingly important ranking factors,
measuring loading performance, interactivity, and visual stability of your pages.

## Building Quality Backlinks

Backlinks remain one of the strongest ranking signals in search algorithms. Quality matters
far more than quantity - a single link from an authoritative domain can outweigh hundreds of
low-quality links. Effective link building strategies include creating original research,
writing guest posts for industry publications, building useful tools that attract natural
links, and forming partnerships with complementary businesses in your niche.
""",

    "content-marketing.md": """---
title: Content Marketing Strategy Guide
slug: content-marketing
url: https://myblog.com/content-marketing
tags: [content, marketing, strategy]
---

## What is Content Marketing

Content marketing is a strategic marketing approach focused on creating and distributing
valuable, relevant, and consistent content to attract and retain a clearly defined audience.
Unlike traditional advertising, content marketing aims to provide genuine value to potential
customers throughout their buying journey. Companies that master content marketing build
trust and authority in their industry, leading to sustainable long-term growth.

## Creating a Content Calendar

A content calendar is an essential tool for any serious content marketing operation. It helps
your team plan topics in advance, maintain consistent publishing frequency, align content with
business goals and seasonal trends, and coordinate work across writers, designers, and editors.
Effective content calendars include publication dates, content formats, target keywords,
assigned authors, and distribution channels for each planned piece.

## Keyword Research for Content

Keyword research forms the foundation of data-driven content strategy. By understanding what
your target audience searches for, you can create content that matches real demand. Tools like
Ahrefs, Semrush, and Google Search Console reveal search volume, keyword difficulty, and
related terms. Long-tail keywords often convert better than broad terms because they indicate
more specific intent. Topic clusters have become the preferred architecture for modern
SEO-driven content programs.

## Measuring Content Performance

Content marketing success requires consistent measurement against clear objectives. Key metrics
include organic traffic growth, keyword ranking improvements, engagement signals like time on
page and scroll depth, lead generation from content downloads, and revenue attributed to
content-influenced customers. Setting up proper analytics tracking before publishing ensures
you have clean data from day one for meaningful performance analysis.
""",

    "link-building.md": """---
title: Advanced Link Building Tactics
slug: link-building
url: https://myblog.com/link-building
tags: [seo, link-building, backlinks]
---

## Understanding Domain Authority

Domain authority is a metric developed by Moz that predicts how well a website will rank in
search engine result pages. It scores websites on a 100-point scale, with higher scores
indicating greater ranking potential. While not a direct Google ranking factor, domain authority
correlates strongly with organic search performance. Building links from high-authority domains
transfers significant ranking power to your website, improving your ability to rank for
competitive keywords over time.

## Outreach Email Strategies

Successful link building depends on effective outreach. The best outreach emails are
personalized, concise, and lead with value rather than requests. Research the recipient before
writing - reference their recent content, acknowledge their expertise, and explain specifically
why your resource would benefit their audience. Follow-up timing matters: one follow-up after
five to seven days is appropriate. Batch outreach with personalization at scale using tools
like Pitchbox or BuzzStream to manage high-volume campaigns while maintaining quality.

## Content-Based Link Acquisition

The most sustainable link building strategy revolves around creating content that naturally
attracts links. Original research and data studies, comprehensive industry surveys, free tools
and calculators, visual assets like infographics and charts, and definitive reference guides
all attract links organically. When you produce genuinely useful resources, bloggers and
journalists naturally reference them when writing about related topics.

## Competitor Backlink Analysis

Analyzing where your competitors earn their backlinks reveals opportunities you might otherwise
miss. Export competitor backlink profiles from tools like Ahrefs or Semrush and look for
patterns - recurring publications, resource pages, directories, or partner sites. If a resource
links to multiple competitors but not to you, it is a warm prospect. Replicating competitor
link sources is one of the most reliable paths to closing the authority gap in competitive
search verticals.
""",

    "technical-seo.md": """---
title: Technical SEO Complete Guide
slug: technical-seo
url: https://myblog.com/technical-seo
tags: [seo, technical, crawling]
---

## Site Speed Optimization

Page speed is a confirmed Google ranking factor and critically affects user experience.
Core Web Vitals - Largest Contentful Paint, First Input Delay, and Cumulative Layout Shift -
are the primary speed metrics Google measures. Improving site speed involves compressing
images, leveraging browser caching, minimizing JavaScript execution, using a content delivery
network, and eliminating render-blocking resources. Regular speed audits using Google
PageSpeed Insights and Lighthouse identify the highest-impact opportunities for improvement.

## Crawl Budget Management

Search engines allocate a finite crawl budget to each website, determining how many pages
they will crawl within a given timeframe. Large websites with thousands of pages must carefully
manage crawl budget by blocking low-value pages via robots.txt, using canonical tags to
consolidate duplicate content, keeping XML sitemaps updated and free of error pages, and
fixing broken internal links that waste crawler resources. Efficient crawl budget usage
ensures your most important pages receive regular reindexing.

## Structured Data Implementation

Structured data markup helps search engines understand your content and can generate rich
results in search pages. Schema.org provides the vocabulary for marking up articles, products,
events, recipes, reviews, FAQs, and more. Implementing JSON-LD structured data on appropriate
pages can improve click-through rates significantly even without ranking changes. Regular
validation using Google's Rich Results Test catches markup errors before they prevent rich
result eligibility.

## International SEO Configuration

Websites targeting multiple countries or languages require careful international SEO
configuration. The hreflang attribute tells search engines which version of a page to serve
to users in different regions and language preferences. URL structure decisions - subdirectories,
subdomains, or country-code top-level domains - each carry different tradeoffs for authority
consolidation and geographic targeting strength. Consistent localization of both content and
technical signals produces the strongest international search performance.
""",
}

dest = Path("test_posts")
dest.mkdir(exist_ok=True)

for filename, content in posts.items():
    (dest / filename).write_text(content, encoding="utf-8")  # <-- THIS WAS THE BUG
    print(f"Created: {dest / filename}")

print(f"\n{len(posts)} test articles created in ./test_posts/")