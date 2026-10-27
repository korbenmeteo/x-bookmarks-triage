# Collecting bookmarks

## Which route

| Route | Reach | Cost | Unattended |
|---|---|---|---|
| Browser (this skill's `collector.js`) | Everything the bookmarks page shows (863 items back to 2020 in testing) | Free | Yes, with the dump route below |
| X API v2 `GET /2/users/:id/bookmarks` | The 800 most recent bookmarks only | Pay per use; owned reads are billed per resource (check the current price in the X developer console) | Yes, OAuth 2.0 user token |
| X data archive | Reportedly no bookmarks file | Free | No |

The browser route reads your own bookmarks, in your own logged-in browser, at
human scrolling speed. Use it on your own account only. If you need an
officially supported path, use the API.

## Procedure (Claude in Chrome)

1. Open a new tab on `https://x.com/i/bookmarks` and wait for it to load.
2. Paste `scripts/collector.js` with `javascript_tool`. It answers "collector ready".
3. Start: `__xb.start({knownIds: [...], stopAfterKnown: 15})`. For a first full backlog, call `__xb.start()` with no known ids.
4. Poll every ~40 s with `await new Promise(r => setTimeout(r, 40000)); __xb.status()` until `running=false`. A full backlog of ~900 items takes 6 to 10 minutes.
5. Optional, X Premium folders: open each folder from the "Bookmarks" menu in the same tab, `__xb.collectFolder("Name")`, poll, then `__xb.applyFolders()`.
6. Get the data out, either way:
   - **Unattended or no download allowed:** `__xb.dump()`, then read the page with `get_page_text` and write the JSON to `exports_dir` exactly as read. Check the item count with Python.
   - **User present and agrees to a download:** `__xb.download("x-bookmarks-export-YYYY-MM-DD.json")`, then ask for access to the Downloads folder and copy the file into `exports_dir`. This is faster and byte-exact for big backlogs.
7. Close the tab.

## Pitfalls seen in practice

- **Scroll step.** X renders only the posts near the viewport. A 3,000 px step lost 216 of 863 bookmarks without any error. Keep 700 px.
- **Timeouts.** A JS call that awaits a long loop times out (about 45 s). `start()` runs in the background on purpose.
- **Truncated tool output.** Results longer than roughly 1,000 characters get cut, and query strings in URLs can make a result be blocked entirely. Keep JS return values short; move data with `dump()` or `download()`.
- **X articles** have no tweet text in the list. The collector keeps the visible preview in `article_hint`; open the post to read the article.
- **"Show more"** posts are truncated in the list (`show_more: true`). Open the strongest ones before routing.
- **Background tabs** are throttled by Chrome; keep the bookmarks tab in front during a long run.
