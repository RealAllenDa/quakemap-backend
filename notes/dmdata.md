# DMData Module Procedure

HomeNetwork **UNPUBLISHED CONFIDENTIAL**. Copyright (c) 2023.

## 1. Using JQuake

JQuake plan only charges for 550 yen/month, which is cheaper than regular plans.
However, its disadvantages include:

- Require manual one-time* (in an 183 day time period, auto-renewed by running program) _refresh_token_ extraction
- Use undocumented _client_id_, _client_secret_ and socket initializer which can easily change over versions
- Unknown request handling from DMData (probable 403)

Albeit these disadvantages, leveraging its price, it's more preferred to use JQuake plan.

## 2. Not Using JQuake

NOTE: Since not using JQuake plan requires:

- Expensive plans (Up to 1950 yen/month)
- Manual OAuth application creation (Complicated)
- Manual OAuth flow execution (**impossible**, since servers tend not to have web browsers and are usually headless)

Thus, at least in foreseeable future, it won't be implemented.