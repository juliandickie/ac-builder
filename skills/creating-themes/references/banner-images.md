# Banner image reference

Every theme needs a banner image. It renders at the top of every email, sets brand recognition, and acts as the visual hook before the subject and body. Get this right and the rest of the email looks intentional; get it wrong and the email looks like a stock template.

## Recommended dimensions

- **1200 x 300 px (4:1 aspect ratio)** is the most common choice. Renders crisply on retina displays and scales down cleanly on phones.
- **600 x 180 px (10:3 aspect ratio)** is what the iDD `lpis` example uses. Smaller file, faster load, but shows pixelation on retina if you're not careful.
- **1600 x 400 px (4:1 retina)** if you want maximum sharpness across all devices and don't mind the file size.

The schema allows `banner_width_px` (100-1200) and `banner_height_px` (50-600) on the theme's `branding` block. Setting these is optional but recommended - email clients use them to reserve layout space, which improves perceived load speed.

## File format

- **JPG** is smaller. Best for photographic banners (course image, product shot, hero photo).
- **PNG** is better quality for graphics with text. If your banner has type baked into it (course title, brand wordmark), use PNG to keep the type crisp.
- **WebP** is supported by modern clients but not universally. Stick with JPG/PNG for broad compatibility.
- **SVG** is not supported by major email clients (Gmail, Outlook, Apple Mail). Don't use SVG for banners.

Aim for under 200KB. Most email clients soft-block remote images by default; a slow-loading banner means people see the alt text instead.

## Hosting

The banner needs to be served over HTTPS from a stable URL. Options:

### S3 / Cloudflare R2 / any HTTPS-served CDN

Most flexible. Upload once, get a permanent URL, reference it from every theme that uses that banner. Recommended if you're managing multiple brands and want a single point of truth.

URL pattern looks like: `https://your-bucket.s3.amazonaws.com/banners/acme-2026.jpg`

### ActiveCampaign content library

If you upload an image to AC's content library (Settings > Files), AC serves it from its CDN at:

```
https://content.app-us1.com/{ACCOUNT_ID}/{YYYY}/{MM}/{DD}/{uuid}.{ext}
```

To get the canonical URL: upload the image, then in the file list right-click > "Get URL" (or the equivalent button in the UI). Copy that URL into your theme.

The iDD `lpis` example uses this pattern:

```
https://content.app-us1.com/LMez9/2026/04/28/3a23406d-1b41-443d-a826-037cb3e0309a.jpeg
```

Pros: integrated with AC, no third-party dependency. Cons: account-locked - if you ever migrate accounts you have to re-upload.

### placehold.co (testing only)

For development/testing, use https://placehold.co. It serves a real image at any size with custom colors and text:

```
https://placehold.co/1200x300/0066cc/ffffff?text=Acme+Implants
```

The example themes use placehold.co URLs. Replace these before going live - placehold.co is fine for local testing but you don't want it in production emails.

## Banner alt text

`banner_alt` is required by the schema. This text is shown when:

- The image fails to load (slow connection, blocked images)
- The user has images disabled in their email client (Outlook does this by default)
- The user is on a screen reader (alt text is read aloud)

Good alt text describes the brand and emails being sent. Bad alt text describes the visual.

- Good: "Acme Implants 2026 - hands-on residency course"
- Bad: "Banner image showing a dental chair and instruments"
- Worse: "banner.jpg"

Keep it under 100 characters. Don't stuff keywords. Don't repeat what the subject line already says.

## Banner rotation (optional)

If you want different emails in a sequence to use different banners (e.g. early-bird emails use one banner, final-deadline emails use a more urgent banner), set `branding.banner_urls` as an array:

```json
"branding": {
  "banner_url": "https://example.com/banner-1.jpg",
  "banner_urls": [
    "https://example.com/banner-1.jpg",
    "https://example.com/banner-2.jpg",
    "https://example.com/banner-3.jpg"
  ],
  "banner_alt": "Acme Implants 2026 launch"
}
```

The orchestrator rotates through the array per-email. If `banner_urls` is absent, every email uses `banner_url`. The first item of `banner_urls` should match `banner_url` (the loader uses `banner_url` as the canonical primary).

## Width and height in the JSON

```json
"branding": {
  "banner_url": "https://example.com/banner.jpg",
  "banner_alt": "Acme Implants 2026 launch",
  "banner_width_px": 1200,
  "banner_height_px": 300
}
```

These render as `<img width="1200" height="300">` attributes in the HTML. They:

- Reserve layout space, preventing CLS-style jank when the image loads
- Help screen readers and assistive tech understand the layout
- Are required by some email rendering services for proper display

If you don't know the actual dimensions, omit these and the renderer will skip the attributes. The image still renders, just without the layout reservation.

## Production checklist

Before pushing a theme to production:

- [ ] Banner URL is a real HTTPS URL (not placehold.co, not a local file path)
- [ ] Image is actually accessible at that URL (cURL test: `curl -I <url>` should return 200)
- [ ] Image is under 200KB
- [ ] Alt text is descriptive and brand-relevant
- [ ] Width and height match the actual file dimensions
- [ ] Image renders correctly in dark mode (test by previewing in Apple Mail dark mode)
