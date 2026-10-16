"""
Automated Demo Video Generator for NexusGraph
Using Playwright (70k+ stars on GitHub), Edge-TTS (10k+ stars on GitHub), and FFmpeg.
Generates a synchronized 1080p demo video following the exact hackathon script.
"""

import asyncio
import os
import subprocess
import json
import time
from pathlib import Path
import edge_tts
from playwright.async_api import async_playwright

ASSETS_DIR = Path("demo_assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
RAW_VIDEO_DIR = ASSETS_DIR / "raw_video"
RAW_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

FINAL_OUTPUT = Path("NexusGraph_Demo_Video_1080p.mp4")

SCRIPT_SEGMENTS = [
    {
        "id": "seg1",
        "title": "Introduction & Architecture Overview",
        "badge": "NEXUSGRAPH // FALKORDB GRAPH HACKS",
        "narration": (
            "Hi judges! Welcome to NexusGraph, an autonomous enterprise SRE and organizational "
            "intelligence swarm powered entirely by FalkorDB. Traditional vector RAG fails when "
            "agents need to reason across complex enterprise dependencies. NexusGraph solves this "
            "by putting data, memory, and company knowledge into a graph where agents can traverse "
            "relationships in real time. We are entering this project into all three hackathon tracks simultaneously."
        )
    },
    {
        "id": "seg2",
        "title": "Track 1 & Track 3: Connected Action & Company Brain",
        "badge": "TRACK 1: CONNECTED ACTION  |  TRACK 3: COMPANY BRAIN",
        "narration": (
            "Let's trigger a production incident on our primary checkout service. Watch the 3-agent swarm "
            "coordinate directly through FalkorDB. First, Track 1 activates: our Triage Agent invokes "
            "Model Context Protocol tools, executing native FalkorDB PageRank algorithms to identify "
            "redis-session-cache as the bottleneck and tracing the exact failure path. Next, Track 3 kicks in: "
            "the Company Brain queries structural ADR-042 and instantly filters our engineering directory to find "
            "an online expert who isn't on PTO, Elena Rostova."
        )
    },
    {
        "id": "seg3",
        "title": "Track 2: Agent Memory & Cross-Session Coordination",
        "badge": "TRACK 2: EPISODIC MEMORY & HANDOFFS",
        "narration": (
            "Notice how every step emits verifiable Cypher queries and subgraph traces for complete explainability. "
            "Now, what happens in the next session when a similar alert fires? Instead of re-guessing, Track 2 takes over. "
            "The Memory Coordinator instantly queries FalkorDB's temporal episodic nodes, retrieving Episode-101 "
            "and its verified procedural runbook from our previous session in under two milliseconds. "
            "State persists because the graph is the memory."
        )
    },
    {
        "id": "seg4",
        "title": "Multi-Tenant Graph Isolation",
        "badge": "MULTI-TENANT ISOLATION // FALKORDB MULTIGRAPH",
        "narration": (
            "To prove true production readiness, NexusGraph leverages FalkorDB's multigraph topology. "
            "With a single database instance, we instantly switch tenants to finserve_io, isolating banking "
            "microservices, compliance audits, and zero-trust ADRs with zero data leakage and sub-millisecond "
            "sparse-matrix traversals."
        )
    },
    {
        "id": "seg5",
        "title": "Open Source & 100% Test Coverage",
        "badge": "OPEN SOURCE & VERIFIED TEST SUITE",
        "narration": (
            "NexusGraph is fully open-source, features 100% automated pytest coverage, and spins up with a single "
            "docker-compose command. Complete with MCP integration, native graph algorithms, and explainable path "
            "tracing, NexusGraph redefines what AI agents can achieve with real context. Thank you!"
        )
    }
]

def get_audio_duration(file_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())

async def generate_speech():
    print("=== 1. Generating High-Quality Neural Narration via Edge-TTS ===")
    durations = {}
    for seg in SCRIPT_SEGMENTS:
        seg_id = seg["id"]
        out_path = ASSETS_DIR / f"{seg_id}.mp3"
        print(f"Generating audio for {seg_id}: '{seg['title']}'...")
        # en-US-ChristopherNeural is clear, confident, authoritative engineering voice
        comm = edge_tts.Communicate(seg["narration"], "en-US-ChristopherNeural", rate="+3%")
        await comm.save(str(out_path))
        dur = get_audio_duration(out_path)
        durations[seg_id] = dur
        print(f"  -> {seg_id}.mp3 generated: {dur:.2f} seconds")
    return durations

async def record_browser_session(durations: dict):
    print("\n=== 2. Recording 1080p Browser Interaction via Playwright ===")
    
    # Calculate timing schedule
    PAUSE = 1.2  # clean breathing pause between segments
    t1 = durations["seg1"]
    t2 = durations["seg2"]
    t3 = durations["seg3"]
    t4 = durations["seg4"]
    t5 = durations["seg5"]
    
    print(f"Segment Timings:\n"
          f"  Seg 1: {t1:.1f}s\n"
          f"  Seg 2: {t2:.1f}s\n"
          f"  Seg 3: {t3:.1f}s\n"
          f"  Seg 4: {t4:.1f}s\n"
          f"  Seg 5: {t5:.1f}s\n"
          f"  Total Estimated Video: {t1+t2+t3+t4+t5 + 5*PAUSE:.1f}s")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RAW_VIDEO_DIR),
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        print("Navigating to http://localhost:5173 (NexusGraph Mission Control)...")
        await page.goto("http://localhost:5173", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # ---------------------------------------------------------------------
        # SEGMENT 1: Intro, Title, Track Badges, Multi-tenant Selector
        # ---------------------------------------------------------------------
        print("Executing Segment 1 Visuals...")
        # Hover over title
        await page.hover("h1")
        await page.wait_for_timeout(2500)

        # Highlight Track 1 badge
        track1_btn = page.locator("button:has-text('Track 1: Connected Action')")
        if await track1_btn.count() > 0:
            await track1_btn.hover()
            await page.wait_for_timeout(1500)
            await track1_btn.click()
            await page.wait_for_timeout(2500)
            await track1_btn.click()  # untoggle
            await page.wait_for_timeout(1000)

        # Highlight Track 2 badge
        track2_btn = page.locator("button:has-text('Track 2: Episodic Memory')")
        if await track2_btn.count() > 0:
            await track2_btn.hover()
            await page.wait_for_timeout(1500)

        # Highlight Track 3 badge
        track3_btn = page.locator("button:has-text('Track 3: Company Brain')")
        if await track3_btn.count() > 0:
            await track3_btn.hover()
            await page.wait_for_timeout(1500)

        # Hover tenant dropdown
        tenant_select = page.locator("select")
        if await tenant_select.count() > 0:
            await tenant_select.hover()
            await page.wait_for_timeout(2000)

        # Hover over canvas to show topology
        await page.mouse.move(960, 540)
        await page.wait_for_timeout(int(max(1000, (t1 - 14) * 1000)))

        # ---------------------------------------------------------------------
        # SEGMENT 2: Trigger Scenario 1 (Checkout API 502 Spike)
        # ---------------------------------------------------------------------
        print("Executing Segment 2 Visuals (Triggering Scenario 1)...")
        sc1_btn = page.locator("button:has-text('Scenario 1:')")
        if await sc1_btn.count() > 0:
            await sc1_btn.hover()
            await page.wait_for_timeout(800)
            await sc1_btn.click()
            print("  -> Scenario 1 clicked! Waiting for swarm response...")

        # Wait for the agent steps to render
        await page.wait_for_selector("text=SRE_Triage_Agent", timeout=15000)
        await page.wait_for_timeout(3000)

        # Hover over SRE_Triage_Agent step
        sre_card = page.locator("div:has-text('SRE_Triage_Agent')").first
        if await sre_card.count() > 0:
            await sre_card.hover()
            await page.wait_for_timeout(2000)

        # Click Highlight Path on Triage agent
        highlight_btn = page.locator("button:has-text('Highlight Path')").first
        if await highlight_btn.count() > 0:
            await highlight_btn.click()
            await page.wait_for_timeout(3000)

        # Move mouse across the canvas over the highlighted blast radius
        await page.mouse.move(600, 450)
        await page.wait_for_timeout(1000)
        await page.mouse.move(800, 500)
        await page.wait_for_timeout(1000)
        await page.mouse.move(1100, 550)
        await page.wait_for_timeout(2000)

        # Scroll down Agent Stream to show Company Brain agent & Elena Rostova
        stream_panel = page.locator("div.overflow-y-auto").first
        if await stream_panel.count() > 0:
            await stream_panel.evaluate("el => el.scrollBy({ top: 350, behavior: 'smooth' })")
            await page.wait_for_timeout(2500)

        # Hover over citations panel on the right
        citations = page.locator("text=ADR-042").first
        if await citations.count() > 0:
            await citations.hover()
            await page.wait_for_timeout(2500)

        await page.wait_for_timeout(int(max(1000, (t2 - 20) * 1000)))

        # ---------------------------------------------------------------------
        # SEGMENT 3: Cypher Trace Inspection & Scenario 2 Memory Recall
        # ---------------------------------------------------------------------
        print("Executing Segment 3 Visuals (Cypher Inspection & Scenario 2)...")
        # Scroll back up slightly and click 'Cypher' button
        cypher_btn = page.locator("button:has-text('Cypher')").first
        if await cypher_btn.count() > 0:
            await cypher_btn.hover()
            await page.wait_for_timeout(1000)
            await cypher_btn.click()
            print("  -> Expanded Cypher accordion!")
            await page.wait_for_timeout(3500)

        # Click Scenario 2 button
        sc2_btn = page.locator("button:has-text('Scenario 2:')")
        if await sc2_btn.count() > 0:
            await sc2_btn.hover()
            await page.wait_for_timeout(1000)
            await sc2_btn.click()
            print("  -> Scenario 2 clicked! Verifying cross-session memory recall...")

        await page.wait_for_selector("text=Memory_Coordinator_Agent", timeout=15000)
        await page.wait_for_timeout(3000)

        # Scroll to Memory Coordinator step
        mem_card = page.locator("div:has-text('Memory_Coordinator_Agent')").first
        if await mem_card.count() > 0:
            await mem_card.hover()
            await page.wait_for_timeout(3000)

        await page.wait_for_timeout(int(max(1000, (t3 - 15) * 1000)))

        # ---------------------------------------------------------------------
        # SEGMENT 4: Multi-Tenant Switcher (finserve_io)
        # ---------------------------------------------------------------------
        print("Executing Segment 4 Visuals (Multi-Tenant Switch)...")
        if await tenant_select.count() > 0:
            await tenant_select.hover()
            await page.wait_for_timeout(1000)
            await tenant_select.select_option("finserve_io")
            print("  -> Switched tenant to finserve_io!")
            await page.wait_for_timeout(4000)

        # Hover over canvas showing new banking microservices
        await page.mouse.move(700, 400)
        await page.wait_for_timeout(2000)
        await page.mouse.move(1000, 600)
        await page.wait_for_timeout(3000)

        await page.wait_for_timeout(int(max(1000, (t4 - 10) * 1000)))

        # ---------------------------------------------------------------------
        # SEGMENT 5: GitHub Repo, Docker-Compose & Test Verification
        # ---------------------------------------------------------------------
        print("Executing Segment 5 Visuals (Conclusion & Architecture)...")
        # Switch back to acme_corp to leave the dashboard in clean state
        if await tenant_select.count() > 0:
            await tenant_select.select_option("acme_corp")
            await page.wait_for_timeout(2000)

        # Navigate to GitHub repo page or show clean overview
        try:
            print("Navigating to GitHub repository view...")
            await page.goto("https://github.com/Sandeep-Hipparagi/NexusGraph", timeout=12000)
            await page.wait_for_timeout(3000)
            # Scroll down to README Quickstart
            await page.evaluate("window.scrollBy({ top: 900, behavior: 'smooth' })")
            await page.wait_for_timeout(4000)
            await page.evaluate("window.scrollBy({ top: 900, behavior: 'smooth' })")
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Note: GitHub navigation timed out ({e}), staying on dashboard.")
            await page.goto("http://localhost:5173")
            await page.wait_for_timeout(8000)

        await page.wait_for_timeout(int(max(1000, (t5 - 12) * 1000)))

        # Close page and context to finalize video recording
        await page.close()
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        print(f"Raw video recorded to: {video_path}")
        return Path(video_path)

def compose_final_video(raw_video_path: Path, durations: dict):
    print("\n=== 3. Composing Final Synchronized 1080p Video via FFmpeg ===")
    
    # 1. Concatenate all audio segments into single master narration track
    concat_list = ASSETS_DIR / "audio_concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in SCRIPT_SEGMENTS:
            p = (ASSETS_DIR / f"{seg['id']}.mp3").resolve()
            f.write(f"file '{p.as_posix()}'\n")

    master_audio = ASSETS_DIR / "master_narration.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(master_audio)
    ], check=True)
    print(f"Master narration audio created: {master_audio}")

    # Total audio duration
    total_audio_dur = get_audio_duration(master_audio)
    print(f"Total narration duration: {total_audio_dur:.2f}s")

    # 2. Build elegant subtitle / lower-third overlay filter using drawtext or subtitles
    # We will encode high-quality H.264 at 1920x1080 with AAC audio
    print("Muxing video with audio, applying 1080p scaling, and syncing...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_video_path),
        "-i", str(master_audio),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(FINAL_OUTPUT)
    ]
    subprocess.run(cmd, check=True)
    
    size_mb = FINAL_OUTPUT.stat().st_size / (1024 * 1024)
    final_dur = get_audio_duration(FINAL_OUTPUT)
    print(f"\n🎉 SUCCESS! Generated {FINAL_OUTPUT.name}:")
    print(f"  - Resolution: 1920x1080 (Full HD)")
    print(f"  - Duration: {final_dur:.1f} seconds")
    print(f"  - File Size: {size_mb:.2f} MB")
    print(f"  - Codec: H.264 + AAC Audio (Universal Compatibility)")

async def main():
    start_time = time.time()
    durations = await generate_speech()
    raw_video = await record_browser_session(durations)
    compose_final_video(raw_video, durations)
    print(f"\nDone in {time.time() - start_time:.1f}s.")

if __name__ == "__main__":
    asyncio.run(main())
