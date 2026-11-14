"""Assemble the 30 second demo: stills with slow zooms and crossfades, burned-in
captions, the AI narration and a quiet synthesized ambient tone."""
import json
import subprocess

TOTAL = 29.5          # hard cap is 30.0 s
TEMPO = 1.06
GAP, LEAD, XF, FPS = 0.15, 0.25, 0.35, 30
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

S = json.load(open("script.json"))
D = {k: v / TEMPO for k, v in json.load(open("durs.json")).items()}

# when each sentence starts
start, t = {}, LEAD
for k in S:
    start[k] = t
    t += D[k] + GAP
speech_end = t - GAP

# shots: (still, start time). Sentence 7 is shared by two stills.
half7 = start["7"] + D["7"] * 0.42
shots = [("s1_hero.png", 0.0), ("s2_problem.png", start["2"] - 0.1), ("s3_idea.png", start["3"] - 0.1),
         ("s4_pick.png", start["4"] - 0.1), ("s5_match.png", start["5"] - 0.1),
         ("s6_proof.png", start["6"] - 0.1), ("s7a_region.png", start["7"] - 0.1),
         ("s7b_close.png", half7), ("s8_end.png", speech_end + 0.35)]
ends = [s for _, s in shots[1:]] + [TOTAL]

inputs, fc = [], []
for i, ((img, s), e) in enumerate(zip(shots, ends)):
    dur = e - s + (XF if i < len(shots) - 1 else 0)
    n = int(round(dur * FPS))
    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", img]
    # zoom in on odd shots, out on even ones; the end card stays almost still
    amt = 0.012 if img == "s8_end.png" else 0.05
    z = f"1+{amt}*on/{n}" if i % 2 == 0 else f"1+{amt}-{amt}*on/{n}"
    fc.append(f"[{i}:v]scale=3840:2160,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"d=1:s=1920x1080:fps={FPS},setsar=1,format=yuv420p[v{i}]")
prev = "v0"
for i in range(1, len(shots)):
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={shots[i][1]:.3f}[x{i}]")
    prev = f"x{i}"

# captions (English subtitles) and the AI-voice label
draw, srt = [], []
for n, k in enumerate(S, 1):
    open(f"cap{k}.txt", "w").write(S[k])
    a, b = start[k], start[k] + D[k] + 0.1
    draw.append(f"drawtext=fontfile={FONT}:textfile=cap{k}.txt:fontsize=40:fontcolor=white:"
                f"box=1:boxcolor=black@0.62:boxborderw=18:x=(w-text_w)/2:y=h-128:"
                f"enable='between(t,{a:.2f},{b:.2f})'")
    f = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round((x%1)*1000)):03d}"
    srt.append(f"{n}\n{f(a)} --> {f(b)}\n{S[k]}\n")
open("label.txt", "w").write("AI-generated voice")
draw.append(f"drawtext=fontfile={FONT}:textfile=label.txt:fontsize=21:fontcolor=white@0.55:x=36:y=h-44:"
            f"enable='lt(t,{shots[-1][1]:.2f})'")
fc.append(f"[{prev}]" + ",".join(draw) + f",fade=t=in:d=0.4,fade=t=out:st={TOTAL-0.5}:d=0.5[vout]")
open("demo.srt", "w").write("\n".join(srt))

# audio: narration sentences placed on the timeline, plus an ambient tone
nv = len(shots)
for j, k in enumerate(S):
    inputs += ["-i", f"tts/s{k}.wav"]
    fc.append(f"[{nv+j}:a]atempo={TEMPO},highpass=f=70,adelay={int(start[k]*1000)}:all=1[a{j}]")
fc.append("".join(f"[a{j}]" for j in range(len(S))) + f"amix=inputs={len(S)}:normalize=0,"
          "acompressor=threshold=-18dB:ratio=3:attack=5:release=120,aecho=0.8:0.5:24:0.09,volume=3.7[voice]")
fc.append(f"sine=f=110:d={TOTAL}[p1];sine=f=164.81:d={TOTAL}[p2];sine=f=220.6:d={TOTAL}[p3];"
          f"[p1][p2][p3]amix=inputs=3:normalize=0,lowpass=f=600,tremolo=f=0.18:d=0.35,volume=0.085,"
          f"afade=t=in:d=1.2,afade=t=out:st={TOTAL-1.6}:d=1.6[pad]")
fc.append(f"[voice][pad]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.95,"
          f"aresample=48000,apad,atrim=0:{TOTAL}[aout]")

note = ("Narration is an AI-generated voice (Piper text-to-speech, en_GB-alan-medium). "
        "All footage is the team's real website, https://duplicaa.vercel.app; no image or video is AI-generated. "
        "Background tone synthesized with FFmpeg.")
cmd = ["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
       "-map", "[vout]", "-map", "[aout]", "-t", str(TOTAL), "-r", str(FPS),
       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
       "-metadata", "title=Planetary Twin Finder - Team Duplica - NASA Space Apps 2026 demo",
       "-metadata", f"comment={note}", "-metadata", f"description={note}",
       "-metadata", "artist=Team Duplica", "planetary_twin_finder_demo.mp4"]
subprocess.run(cmd, check=True)
print("speech ends", round(speech_end, 2), "| end card from", round(shots[-1][1], 2), "| total", TOTAL)
for k in S:
    print(k, round(start[k], 2), round(start[k] + D[k], 2), S[k])
