# YouTube upload workflow (AI video -> YouTube)

Reproduces the "Everygen MCP -> Claude -> video" reel, with the extra step of
publishing the result to YouTube. Written from a real run on 2026-09-24.

## What the reel does

1. Go to everygen.ai/mcp.
2. In claude.ai: Customize -> Connectors -> Add custom connector.
   Name: `Everygen`. URL: `https://www.viewmax.io/api/mcp`.
3. Prompt Claude: "make a 30-second fireplace video in 4K" and let it cook.

## What actually works from a Claude Code cloud session

A custom connector added in claude.ai Settings is NOT visible to a Claude Code
remote session, so step 2 cannot be followed here. Two connectors that ARE
present do the same job:

| Step | Reel | This repo |
| --- | --- | --- |
| Generate video | Everygen MCP | Higgsfield MCP (`generate_video_batch`) |
| Upload to YouTube | manual | Composio `youtube` toolkit (`YOUTUBE_UPLOAD_VIDEO`) |

## Procedure

1. **Pick a model and preflight cost.** Call `generate_video` with
   `get_cost: true` before spending credits. Costs seen on 2026-09-24
   for a 30 s, 16:9 clip:

   | Model | Res | Audio | Credits |
   | --- | --- | --- | --- |
   | seedance_2_5 | 1080p | on | 360 |
   | seedance_2_5 | 1080p | off | 360 |
   | seedance_2_5 | 720p | on | 210 |
   | seedance_2_5 | 480p | on | 90 |
   | wan3_0 | 1080p | on | 105 |
   | seedance_2_0 (15 s, native 4k) | 4k | on | 330 |

   No model renders 30 s natively at 4K. Render at 1080p, then upscale
   with `upscale_video` (provider `bytedance`, resolution `4k`) if credits
   allow.

2. **Submit** with `generate_video_batch` (headless), then `jobs_wait`
   until `all_terminal` is true. Keep the `job_id`; it is also the
   `video_id` for the upscaler.

3. **Stage the file for Composio.** In `COMPOSIO_REMOTE_WORKBENCH`,
   download to local sandbox disk and push through the presigned uploader.
   Do NOT write the video to `/mnt/files/`; that s3fs mount fails with
   `Input/output error` on close for files in the tens of MB (a 5-byte
   probe works, a 90 MB video does not).

   ```python
   import requests
   local = '/home/user/fireplace_1080p.mp4'
   r = requests.get(VIDEO_URL, stream=True, timeout=170)
   with open(local, 'wb') as f:
       for chunk in r.iter_content(1 << 20):
           f.write(chunk)
   data, err = upload_local_file(local)   # returns data['s3key']
   ```

   A `curl` exit code 23 at the very end of the download is benign as long
   as the byte count matches the `Content-Length` header.

4. **Upload.** Still in the workbench, so the account can be chosen:

   ```python
   data, err = run_composio_tool(
       'YOUTUBE_UPLOAD_VIDEO',
       {
         'title': ..., 'description': ..., 'tags': [...],
         'categoryId': '22', 'privacyStatus': 'private',
         'videoFilePath': {'name': 'fireplace.mp4',
                           'mimetype': 'video/mp4', 's3key': s3key},
       },
       account='youtube_timist-huron',   # Phil Samonte channel
       print_schema_for_tool=False,
   )
   video_id = data['data']['response_data']['id']
   ```

   Connected YouTube accounts (Composio ids):

   | Account id | Channel |
   | --- | --- |
   | youtube_timist-huron | Phil Samonte (@philsamonte) |
   | youtube_bahan-placus | Halo-Halo History (default) |
   | youtube_slate-fod | Blood & Silver |

   Upload as `private` first. Flip to public in YouTube Studio after
   review, or via `YOUTUBE_UPDATE_VIDEO`.

## Run log

| Date | Model | Spec | Credits | Result |
| --- | --- | --- | --- | --- |
| 2026-09-24 | wan3_0 | 30 s, 1080p, 16:9, audio | 105 | Uploaded private to Phil Samonte as `04xa3AdtVtw` (86 MB) |

Render time for the 30 s clip was about 19 minutes. Poll with
`jobs_wait` at its 15 s maximum; do not resubmit on a slow job.

Not done on 2026-09-24: the 4K upscale. `upscale_video` has no cost
preflight and the balance after the render was about 142 credits, so it
was left for a deliberate follow-up run.

## Rules

- Always preflight cost. Never submit a job that exceeds the balance.
- Never upload `public` on the first pass.
- The Composio default YouTube account is Halo-Halo History, not Phil's
  personal channel. Pass `account` explicitly every time.
